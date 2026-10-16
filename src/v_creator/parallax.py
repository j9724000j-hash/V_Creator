"""2.5D camera moves from a single still: depth-aware parallax on CPU.

Model: every source pixel S with normalised depth D (1 = near) is displayed at

    P = C + (S - C) * (Zg + kz * (D - f)) + (tx + px * (D - f) * W,
                                             ty + py * (D - f) * W)

where C is the frame centre and f the focus depth (the scene's median), so the
mid-ground stays steady while near layers move more than far ones. We render by
*backward* mapping: for each output pixel we solve S by fixed-point iteration
(D is looked up at the current estimate of S). Depth is first dilated so that
foreground edges stretch the background rather than tearing, then blurred.
Warp maps are computed on a <=960 px grid and upsampled; the full-resolution
frame is sampled once with OpenCV remap. Output: raw RGB frames piped to FFmpeg.

This is a camera move, NOT generative video: nothing inside the scene acts or
changes, and strong moves reveal stretched "rubber" edges behind foreground.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import subprocess
from typing import Iterator

import numpy as np
from PIL import Image

CAMERAS = ("auto", "dolly-in", "dolly-out", "orbit-left", "orbit-right",
           "pan-left", "pan-right", "crane-up", "crane-down", "breathe")
# Varied but calm sequence used by camera: auto (by scene ordinal).
AUTO_SEQUENCE = ("dolly-in", "orbit-right", "crane-up", "orbit-left", "dolly-out", "pan-left")
MAP_MAX_SIDE = 960
ITERATIONS = 3


def resolve_camera(camera: str, ordinal: int) -> str:
    if camera not in CAMERAS:
        raise ValueError(f"camera must be one of {', '.join(CAMERAS)}")
    return AUTO_SEQUENCE[(ordinal - 1) % len(AUTO_SEQUENCE)] if camera == "auto" else camera


def ease(t: float) -> float:
    """Mostly linear (motion never stalls at cuts) with soft acceleration."""
    t = min(1.0, max(0.0, t))
    return 0.65 * t + 0.35 * (0.5 - 0.5 * math.cos(math.pi * t))


@dataclass(frozen=True)
class CameraState:
    zoom: float          # Zg: global scale (>1 keeps borders covered)
    depth_zoom: float    # kz: extra scale per unit depth above focus (dolly feel)
    tx: float            # global translation, output pixels
    ty: float
    px: float            # parallax translation per unit depth, fraction of width
    py: float


def camera_state(name: str, t: float, *, strength: float, focus: float,
                 width: int, height: int) -> CameraState:
    """Camera parameters at clip progress t in [0, 1]."""
    s = float(strength)
    e = ease(t)
    spread = max(focus, 1.0 - focus)  # largest |D - f|
    if name in ("dolly-in", "dolly-out"):
        k = e if name == "dolly-in" else 1.0 - e
        return CameraState(1.02 + 0.08 * s * k, 0.07 * s * k, 0.0, 0.0, 0.0, 0.0)
    if name in ("orbit-left", "orbit-right", "crane-up", "crane-down"):
        a = 0.022 * s
        swing = a * (1.0 - 2.0 * e)  # +a -> -a
        if name in ("orbit-left", "crane-down"):
            swing = -swing
        zoom = 1.0 + 2.0 * a * spread + 0.02 + 0.015 * s * e
        if name.startswith("orbit"):
            return CameraState(zoom, 0.0, 0.0, 0.0, swing, 0.0)
        return CameraState(zoom, 0.0, 0.0, 0.0, 0.0, swing)
    if name in ("pan-left", "pan-right"):
        a, b = 0.018 * s, 0.02 * s
        direction = 1.0 - 2.0 * e
        if name == "pan-left":
            direction = -direction
        zoom = 1.0 + 2.0 * (b + a * spread) + 0.02
        return CameraState(zoom, 0.0, b * direction * width, 0.0, a * direction, 0.0)
    if name == "breathe":
        wave = math.sin(math.pi * e)
        return CameraState(1.03 + 0.02 * s * e, 0.03 * s * wave, 0.0, 0.0, 0.0, 0.0)
    raise ValueError(f"unknown camera move: {name}")


def fit_box(src_w: int, src_h: int, width: int, height: int) -> tuple[float, float, float, float]:
    """Centred crop box (in source pixels) with the target aspect ratio."""
    target = width / height
    if src_w / src_h > target:
        crop = src_h * target
        x0 = (src_w - crop) / 2
        return (x0, 0.0, x0 + crop, float(src_h))
    crop = src_w / target
    y0 = (src_h - crop) / 2
    return (0.0, y0, float(src_w), y0 + crop)


def fit_image_and_depth(image: Image.Image, depth: np.ndarray, width: int,
                        height: int) -> tuple[np.ndarray, np.ndarray]:
    """Crop/resize the still and its depth map identically (cover fit)."""
    rgb = image.convert("RGB")
    box = fit_box(*rgb.size, width, height)
    frame = np.asarray(rgb.resize((width, height), Image.Resampling.LANCZOS, box=box))
    dh, dw = depth.shape
    sx, sy = dw / rgb.size[0], dh / rgb.size[1]
    dbox = (box[0] * sx, box[1] * sy, box[2] * sx, box[3] * sy)
    scale = min(1.0, MAP_MAX_SIDE / max(width, height))
    mw, mh = max(8, round(width * scale)), max(8, round(height * scale))
    depth_img = Image.fromarray(depth.astype(np.float32))
    fitted = np.asarray(depth_img.resize((mw, mh), Image.Resampling.BILINEAR, box=dbox),
                        dtype=np.float32)
    return np.ascontiguousarray(frame), np.ascontiguousarray(fitted)


def prepare_depth(depth: np.ndarray) -> np.ndarray:
    """Grow the foreground slightly and smooth, so edges stretch instead of tear."""
    import cv2

    h, w = depth.shape
    radius = max(1, round(max(w, h) * 0.006))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius + 1, 2 * radius + 1))
    grown = cv2.dilate(depth.astype(np.float32), kernel)
    sigma = max(0.8, max(w, h) * 0.004)
    return cv2.GaussianBlur(grown, (0, 0), sigma)


def warp_maps(depth: np.ndarray, state: CameraState, focus: float, width: int,
              height: int) -> tuple[np.ndarray, np.ndarray]:
    """Backward maps (output px -> source px) on the depth grid, upsampled to WxH."""
    import cv2

    mh, mw = depth.shape
    gx = np.linspace(0.0, width - 1.0, mw, dtype=np.float32)[None, :].repeat(mh, 0)
    gy = np.linspace(0.0, height - 1.0, mh, dtype=np.float32)[:, None].repeat(mw, 1)
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    to_grid_x = (mw - 1) / max(1.0, width - 1.0)
    to_grid_y = (mh - 1) / max(1.0, height - 1.0)
    sx, sy = gx.copy(), gy.copy()
    d = depth
    for _ in range(ITERATIONS):
        rel = d - focus
        scale = np.maximum(0.5, state.zoom + state.depth_zoom * rel)
        sx = cx + (gx - cx - state.tx - state.px * rel * width) / scale
        sy = cy + (gy - cy - state.ty - state.py * rel * width) / scale
        d = cv2.remap(depth, sx * to_grid_x, sy * to_grid_y, cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_REPLICATE)
    if (mw, mh) != (width, height):
        sx = cv2.resize(sx, (width, height), interpolation=cv2.INTER_LINEAR)
        sy = cv2.resize(sy, (width, height), interpolation=cv2.INTER_LINEAR)
    # cv2 returns float32 already; avoid a full-resolution copy per frame.
    return np.ascontiguousarray(sx, dtype=np.float32), np.ascontiguousarray(sy, dtype=np.float32)


def frames(base: np.ndarray, depth: np.ndarray, camera: str, count: int, *,
           strength: float = 1.0) -> Iterator[np.ndarray]:
    """Yield `count` HxWx3 uint8 frames for a resolved camera move."""
    import cv2

    height, width = base.shape[:2]
    prepared = prepare_depth(depth)
    focus = float(np.median(prepared))
    for i in range(count):
        t = i / max(1, count - 1)
        state = camera_state(camera, t, strength=strength, focus=focus, width=width, height=height)
        mx, my = warp_maps(prepared, state, focus, width, height)
        yield cv2.remap(base, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)


def _overlay_blender(overlay: Path, width: int, height: int):
    """Return a per-frame "over" blend for a full-frame RGBA title overlay.

    The title (and its scrim) is baked into each frame here instead of through
    FFmpeg's looped PNG input plus overlay filter: that filter graph buffers
    full-resolution frames without back-pressure and peaks near 2 GB on a 4K
    render, which OOM-kills the encoder next to the Python warper on a small
    CPU-only box. cv2.blendLinear does the same math in ~15 ms per 4K frame
    (measured; a float32 NumPy blend costs ~120 ms).
    """
    import cv2

    with Image.open(overlay) as image:
        rgba = image.convert("RGBA")
        if rgba.size != (width, height):
            rgba = rgba.resize((width, height), Image.Resampling.BILINEAR)
        raw = np.asarray(rgba, dtype=np.uint8)
    if not raw[:, :, 3].any():
        return None
    weight = np.ascontiguousarray(raw[:, :, 3], dtype=np.float32)
    weight /= 255.0
    inverse = np.ascontiguousarray(1.0 - weight, dtype=np.float32)
    source = np.ascontiguousarray(raw[:, :, :3])

    def blend(frame: np.ndarray) -> np.ndarray:
        return cv2.blendLinear(source, frame, weight, inverse)

    return blend


def encode_clip(frame_iter: Iterator[np.ndarray], *, width: int, height: int, fps: int, count: int,
                out: Path, ffmpeg: str, overlay: Path | None, fade: float | None,
                duration: float, preview: bool, log: Path) -> None:
    """Pipe raw RGB frames to FFmpeg; title overlay is baked in Python, fades in FFmpeg."""
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
           "-framerate", str(fps), "-i", "pipe:0"]
    blender = _overlay_blender(overlay, width, height) if overlay is not None else None
    chain = ["[0:v]null", "format=yuv420p"]
    if fade:
        chain += [f"fade=t=in:st=0:d={fade:.3f}",
                  f"fade=t=out:st={max(0.0, duration - fade):.3f}:d={fade:.3f}"]
    cmd += ["-filter_complex", ",".join(chain) + "[v]", "-map", "[v]", "-frames:v", str(count),
            "-c:v", "libx264", "-preset", "ultrafast" if preview else "medium",
            "-crf", "27" if preview else "19", "-pix_fmt", "yuv420p"]
    if not preview:
        # Full-resolution renders must fit small CPU boxes: with libx264's auto
        # threads a 4K medium encode peaks above 2 GB (measured), which OOM-kills
        # the encoder next to the Python warper. Capping frame threads and the
        # lookahead keeps the same CRF quality at roughly 0.7 GB.
        cmd += ["-threads", "2", "-x264-params", "rc-lookahead=15:sync-lookahead=0"]
    cmd += ["-an", "-movflags", "+faststart", str(out)]
    with log.open("a", encoding="utf-8") as stream:
        stream.write("$ " + " ".join(repr(p) for p in cmd) + "  <raw frames on stdin>\n")
        stream.flush()
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=stream, stderr=stream)
        assert process.stdin is not None
        written = 0
        try:
            for frame in frame_iter:
                if blender is not None:
                    frame = blender(frame)
                if frame.shape != (height, width, 3) or frame.dtype != np.uint8:
                    raise ValueError(f"frame has shape {frame.shape} / {frame.dtype}")
                process.stdin.write(memoryview(np.ascontiguousarray(frame)))
                written += 1
        except BrokenPipeError:
            pass
        finally:
            try:
                process.stdin.close()
            except BrokenPipeError:
                pass
            code = process.wait()
    if code != 0 or written != count:
        out.unlink(missing_ok=True)
        raise RuntimeError(f"Parallax encode failed (code {code}, {written}/{count} frames); see {log}")
