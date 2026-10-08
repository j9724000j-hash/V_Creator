"""Seeded CPU synthesis, local TTS and FFmpeg sidechain mastering."""
import math
from pathlib import Path
import wave
import numpy as np
from .spec import Spec, Cue
from .util import ProductionError, Runner, binary, ffbase, probe, safe_path

RATE=24000

def save(path: Path, data: np.ndarray):
    if data.ndim==1:
        data=np.column_stack([data,data])
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes((np.clip(data,-.98,.98)*32767).astype('<i2').tobytes())

def effect(cue: Cue, seed=0) -> np.ndarray:
    t=np.arange(round(cue.duration*RATE),dtype=np.float32)/RATE
    n=np.random.default_rng(seed).normal(0,.25,len(t))
    u=t/cue.duration
    if cue.effect in ('whoosh','wind','rain','ambience','riser','sweep'):
        sound=n*np.sin(np.pi*u)**2
        if cue.effect in ('riser','sweep'):
            sound+=.2*np.sin(2*np.pi*(160*t+700*t*t))*u
    elif cue.effect in ('hit','impact','bass_drop','pop'):
        sound=np.sin(2*np.pi*(50*t+40*(1-np.exp(-12*t))))*np.exp(-8*u)+n*np.exp(-35*u)
    elif cue.effect=='glitch':
        sound=n*(np.sin(2*np.pi*30*t)>0)*np.exp(-3*u)
    else:
        freq={'click':1700,'notification':880,'mechanical':180,'scifi':420}.get(cue.effect,440)
        sound=np.sin(2*np.pi*freq*t)*np.exp(-6*u)
    sound*=np.minimum(t*200,1)*np.minimum((cue.duration-t)*100,1)
    return np.column_stack([sound*math.sqrt((1-cue.pan)/2),sound*math.sqrt((1+cue.pan)/2)])*cue.gain

def music(spec: Spec) -> np.ndarray:
    audio=spec.audio; duration=spec.video.duration
    data=np.zeros((round(duration*RATE),2),dtype=np.float32)
    roots={'C':48,'D':50,'E':52,'F':53,'G':55,'A':45,'B':47}
    beat=60/audio.bpm
    progression=[0,5,3,7] if audio.mood=='cinematic' else [0,5,7,0]
    for i,start in enumerate(np.arange(0,duration,beat)):
        length=min(beat*1.7,duration-start)
        count=round(length*RATE)
        t=np.arange(count,dtype=np.float32)/RATE
        root=roots[audio.key]+progression[(i//8)%4]
        interval=[0,7,12,3 if audio.mood!='bright' else 4][i%4]
        f=440*2**((root+interval-69)/12)
        envelope=np.minimum(t/.03,1)*np.exp(-t/max(.1,length*.4))*np.minimum((length-t)/.05,1)
        note=(np.sin(2*np.pi*f*t)+.2*np.sin(2*np.pi*2*f*t))*envelope*.24
        offset=round(start*RATE); end=min(len(data),offset+count)
        # Build, climax, outro; no promise of neural music generation.
        structure=.4+.6*math.sin(math.pi*start/duration)
        data[offset:end]+=note[:end-offset,None]*structure*(.4+audio.intensity*.6)
    fade=min(RATE*2,len(data)//2)
    data[:fade]*=np.linspace(0,1,fade)[:,None]
    data[-fade:]*=np.linspace(1,0,fade)[:,None]
    return data

def build_audio(spec: Spec, project: Path, work: Path, runner: Runner) -> tuple[Path,list[dict],list[str]]:
    if spec.video.duration>600:
        raise ProductionError('Core synthesis is bounded to 600 seconds. Split longer projects before rendering.')
    count=round(spec.video.duration*RATE)
    narration=np.zeros((count,2),dtype=np.float32)
    sfx=np.zeros_like(narration)
    records=[]; warnings=[]; offset=0.0
    for idx,scene in enumerate(spec.scenes):
        if spec.audio.narration and (scene.narration or scene.narration_asset):
            raw=work/f'{scene.id}_voice_raw.wav'
            tts=binary('espeak-ng') or binary('espeak')
            if scene.narration_asset:
                raw=safe_path(project,scene.narration_asset.path)
                method='user-narration'
            elif tts:
                text=work/f'{scene.id}_script.txt'; text.write_text(scene.narration,encoding='utf-8')
                runner.run([tts,'-v',spec.audio.voice,'-s',str(spec.audio.speaking_rate),'-f',str(text),'-w',str(raw)])
                method='espeak-local'
            elif spec.audio.missing_tts=='skip':
                warnings.append(f'{scene.id}: narration omitted; TTS unavailable (explicit skip policy)')
                raw=None
            else:
                raise ProductionError('Narration requested but eSpeak NG missing. Install it, supply narration_asset or explicitly set missing_tts: skip.')
            if raw:
                length=float(probe(raw)['format']['duration'])
                speed=max(1,length/max(.1,scene.duration-.15))
                if speed>2:
                    raise ProductionError(f'{scene.id}: narration too long ({length:.1f}s). Shorten script or extend scene.')
                fitted=work/f'{scene.id}_voice.wav'
                runner.run(ffbase()+['-i',str(raw),'-af',f'atempo={speed},apad',
                                    '-t',str(scene.duration),'-ar',str(RATE),'-ac','2','-c:a','pcm_s16le',str(fitted)])
                with wave.open(str(fitted),'rb') as w:
                    samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)/32768
                start=round(offset*RATE); end=min(count,start+len(samples))
                narration[start:end]=samples[:end-start]
                records.append({'path':str(fitted),'method':method,'start':offset,'duration':scene.duration,'speed':speed})
        if spec.audio.sound_effects:
            for j,cue in enumerate(scene.audio_cues):
                sound=effect(cue,idx*100+j)
                start=round((offset+cue.time)*RATE); end=min(count,start+len(sound))
                sfx[start:end]+=sound[:end-start]
                records.append({'method':'procedural-sfx','effect':cue.effect,'start':offset+cue.time,'duration':cue.duration})
        offset+=scene.duration
    voice=work/'narration.wav'; bed=work/'music.wav'; effects=work/'sfx.wav'
    save(voice,narration); save(bed,music(spec) if spec.audio.music else np.zeros_like(narration)); save(effects,sfx)
    master=work/'master.wav'
    graph=(f'[0:a]highpass=f=70,acompressor=threshold=0.15:ratio=3,asplit=2[voice][side];'
           f'[1:a]volume={spec.audio.music_gain}[bed];'
           '[bed][side]sidechaincompress=threshold=0.025:ratio=6:attack=20:release=300[duck];'
           '[voice][duck][2:a]amix=inputs=3:normalize=0:duration=longest')
    if spec.audio.reverb:
        graph+=',aecho=0.8:0.5:60:0.12'
    graph+=(f',afade=t=in:d=0.08,afade=t=out:st={max(0,spec.video.duration-.4)}:d=0.4,'
            f'loudnorm=I={spec.audio.target_loudness}:TP=-1.5:LRA=11,alimiter=limit=0.9[out]')
    runner.run(ffbase()+['-i',str(voice),'-i',str(bed),'-i',str(effects),'-filter_complex',graph,
                        '-map','[out]','-t',str(spec.video.duration),'-ar','48000','-ac','2',str(master)])
    records.extend([{'path':str(bed),'method':'procedural-music' if spec.audio.music else 'silence',
                    'bpm':spec.audio.bpm,'key':spec.audio.key,'mood':spec.audio.mood},
                    {'path':str(master),'method':'sidechain-duck + single-pass-loudnorm + limiter'}])
    return master,records,warnings
