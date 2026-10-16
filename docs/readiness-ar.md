# جاهزية الاستوديو الآن — فحص تشغيلي حقيقي (2026-10-16)

> نطاق الفحص: فرع العمل `arena/966aa81c-v-creator` عند `1387218`، وهو **نفس التزام `main`** بلا أي فرق (`git diff main HEAD` فارغ). نفّذنا التثبيت الكامل ثم خط إنتاج كامل من الصفر: تعليق عربي → رندر معاينة → رندر نهائي → فحص، وعنوان موشن مستقل. كل رقم في الجدول أدناه مأخوذ من مخرجات فعلية لا من نوايا.

## الخلاصة

**نعم — الخط جاهز لإنتاج فيديو كامل قصير على هذا الخادم** (مونتاج + تحريك + تعليق عربي + موسيقى ومؤثرات + ترجمة + تقرير فحص)، بشرط أن تكون المشاهد **لوحات/صوراً أصلية أو تملكها** (Pillow أو صورة تقدّمها)، لأن مولّد لقطات فوتوغرافية/سينمائية بالوصف النصي غير موجود هنا. أُنتج فعلاً ملف نهائي 1280×720 بمدة 21 ثانية مع كلام وموسيقى وducking وترجمة، واجتاز كل الفحوص.

## الأدوات المثبّتة والجاهزة للعمل (مُختبرة في هذه الجلسة)

| # | الأداة | الإصدار | دورها في الفيديو | الدليل المنفَّذ | الحالة |
|---|---|---|---|---|---|
| 1 | **FFmpeg** (عبر imageio-ffmpeg) | 7.0.2 static | المونتاج والقص، `zoompan`، تلاشي المشاهد، ترميز H.264 + AAC، خفض الموسيقى تحت الكلام، `loudnorm` | أنتج `final.mp4` و`preview.mp4` واجتاز فك الترميز الكامل | ✅ جاهز |
| 2 | **ffprobe** (@ffprobe-installer) | 2023 static | قياس المدة/الدقة/الإطارات وحفظ `validation-report.json` | `v-creator validate` → `ok: true` على الملفين | ✅ جاهز |
| 3 | **Pillow + خطوط Noto Arabic** + `arabic-reshaper` + `python-bidi` | 11.3.0 / OFL | توليد لوحة لكل مشهد ورسم العناوين العربية (تشكيل واتجاه صحيحان) | استُخرج إطار من الفيديو النهائي: العنوان «خريطةٌ لا تعرف الطريق» ظهر سليماً 1280×720 | ✅ جاهز |
| 4 | **numpy + mido** (توليد إجرائي أصلي) | 2.3.4 / 1.3.3 | موسيقى جوّية بمزاج/BPM، مؤثرات انتقال (whoosh/impact)، وملف `score.mid` قابل للتحرير | أُنتج `music_mysterious_72.wav` و`effects.wav` و`score.mid` داخل مخرجات الرندر | ✅ جاهز |
| 5 | **HyperFrames + Chromium محلي** | 0.8.163 / Chromium 153 | موشن غرافيك HTML/WAAPI: عناوين، HUD، خلفيات متحركة | `lint` = 0 أخطاء، ورندر 3 ثوانٍ (72 إطاراً، 640×360) في 6.2 ثانية → `output/motion-title.mp4` | ✅ جاهز |
| 6 | **sherpa-onnx + أوزان Supertonic 3** | 1.13.8 / 145 MB | **توليد التعليق العربي** إلى WAV 44.1 kHz بنبرة نموذجية (10 متحدثين) على CPU | `v-creator narrate` أنتج 21.0 ثانية كلام عربي + `narration.voice.json` بالبصمة والرخصة | ✅ مثبّت ومُشغَّل |
| 7 | **v-creator CLI** | 0.1.0 | `plan` / `narrate` / `render --preview\|--final` / `validate` / `doctor` + manifest وأثر المصادر | رندر نهائي 1280×720 في 8.3 ثانية؛ معاينة 640×360؛ الاثنان `ok: true` | ✅ جاهز |
| 8 | **pytest** | 8.4.2 | ثقة السبيكة والحقوق والكاش والصوت والمدد والترميز | **31 اختباراً ناجحاً** في 4.87 ثانية | ✅ جاهز |
| 9 | **ImageMagick** (اختياري) | 6.9.11 | تحويلات الصور النقطية؛ البديل الفعلي هو Pillow | ظهر في `doctor` كأداة مكتشَفة | ✅ متاح |
| 10 | **Chromium مضمّن (Sparticuz)** | 153.0.0 | متصفح headless بلا تنزيل خارجي لعناوين HyperFrames | استُخدم فعلاً في رندر الموشن (`software gpu` بلا WebGL) | ✅ جاهز |

## المخرجات المتوفرة الآن في `output/` (محلية ومتجاهلة من Git)

| الملف | المواصفات |
|---|---|
| `output/final-check/final.mp4` | 1280×720 · 24fps · 21.0ث · H.264+AAC 48kHz ستيريو · صورة وكلام وموسيقى ومؤثرات · ~740 KB |
| `output/forgotten-gate-voice-demo/narration.wav` | 21.0ث كلام عربي 44.1kHz + `narration.voice.json` (نموذج صريح + رخصة OpenRAIL-M) |
| `output/forgotten-gate-voice-demo/preview.mp4` | معاينة 640×360 بالصوت، `ok: true` |
| `output/forgotten-gate-novoice/preview.mp4` | معاينة 13ث بلا كلام (المشروع الأساسي) |
| `output/motion-title.mp4` | عنوان عربي متحرك 3.0ث عبر HyperFrames |
| `score.mid` + `subtitles.srt` + `production-manifest.json` + `render-log.txt` | لحن قابل للتحرير، ترجمة بمستوى المشهد، سجل أدوات ومصادر، وتقرير فحص |

## إعادة الإنتاج في 6 أوامر

```bash
./scripts/install.sh                 # .venv + FFmpeg/ffprobe + HyperFrames/Chromium + أوزان الصوت 145MB
./scripts/doctor.sh                  # تقرير ما هو فعلاً قابل للاستخدام
.venv/bin/python -m pytest -q        # 31 اختباراً
.venv/bin/v-creator narrate videos/fantasy-intro/voice-demo.yaml \
  --out output/forgotten-gate-voice-demo/narration.wav --speaker 0
.venv/bin/v-creator render videos/fantasy-intro/voice-demo.yaml --final \
  --narration output/forgotten-gate-voice-demo/narration.wav --out output/final-check
.venv/bin/v-creator validate videos/fantasy-intro/voice-demo.yaml output/final-check/final.mp4
./scripts/motion.sh lint motion/fantasy-title
./scripts/motion.sh render motion/fantasy-title -o output/motion-title.mp4 --quality draft --low-memory-mode
```

## غير مثبّت هنا (وسببه عتادي أو ترخيصي، وليس عيباً في المستودع)

| الأداة | الحالة | السبب |
|---|---|---|
| SILMA v1 · Chatterbox Multilingual · Habibi-TTS | سكربتات تهيئة موجودة، الأوزان غير منزّلة | تحتاج ~2.6 GB+ وذاكرة 8 GB+ أو GPU؛ هذا الخادم 3.85 GiB بلا GPU |
| ACE-Step 1.5 للموسيقى التوليدية | غير مثبّت | ~10 GB checkpoint وGPU موصى به؛ البديل الجاهز هو الموسيقى الإجرائية الأصلية |
| Remotion · MusicGen · XTTS-v2 | مستبعدة افتراضياً | تراخيص غير FOSS/غير تجارية للأوزان |
| Kdenlive · Blender · Audacity · LMMS · FluidSynth | غير مثبّتة | واجهات سطح مكتب/صوتيات؛ تُفتح المخرجات على جهازك |
| Manim · Godot | غير مثبّتة | غير لازمة لقصة سينمائية 2D |

## حدود يجب معرفتها قبل تسليم «فيديو كامل»

1. **لا توليد مشهد فوتوغرافي من الوصف النصي هنا.** اللوحات إجرائية أصلية أو صور تقدّمها أنت مع `image_license` و`image_source`.
2. **الموشن غير موصول آلياً بـ YAML**: تُرندر العناوين بأمر مستقل ثم تُدمج/تُستخدم كقالب.
3. **الترجمة على مستوى المشهد، لا على مستوى الكلمة** (لا forced alignment بعد).
4. **الصوت اصطناعي بنبرة نموذجية جاهزة** (OpenRAIL-M) وليس أداءً بشرياً؛ الاستماع للنطق واللهجة خطوة بشرية إلزامية، ويتغير الصوت بين التشغيلات — احفظ العينة التي نالت موافقتك.
5. **`--final` يرفض الغياب أو الطول الزائد** للتعليق بدل قطعه بصمت (`audio.narration.required: true`).
6. **الموسيقى جوّية إجرائية، ليست أوركسترا سينمائية.** `score.mid` قابل للتنقيح في DAW خارجي.
7. **الأوزان والمخرجات لا تُرفع إلى Git** (`models/`, `output/`, `private/`, وامتدادات الوسائط متجاهلة).

## ملاحظات بيئة

- العتاد: 3.85 GiB RAM · بلا GPU · ~18 GB مساحة حرة — كافٍ لخط المعاينة/النهائي القصير.
- I/O: يلزم اتصال بـ PyPI وnpm عند التثبيت فقط (~1 GB)؛ بعدها كل شيء محلي بلا مفاتيح API.
- الأزمنة المقيسة في هذه الجلسة: التثبيت الكامل مع أوزان الصوت **< 1 دقيقة** (يتغير بحسب الشبكة)، اختبارات 4.9 ثانية، رندر فيديو 21 ثانية ≈ 8 ثوان، رندر موشن 3 ثوان ≈ 6 ثوان.
