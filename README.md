# V_Creator — استوديو تمهيدي للفيديو الخيالي السينمائي

**يعمل هنا الآن، على CPU بلا حساب مدفوع:** خط المشاهد والتحريك والمونتاج بـPillow وFFmpeg، عناوين موشن بـHyperFrames/Chromium، موسيقى ومؤثرات إجرائية مع MIDI، وترجمة عربية؛ وكذلك **توليد تعليق عربي محلي إلى WAV** بـsherpa-onnx ونموذج Supertonic 3. أنتجنا عينة كلام 44.1 kHz ومعاينة 21 ثانية تمزج الراوي والموسيقى واجتازتا فحص الترميز. **الصوت توليدي اصطناعي بنبرة نموذج جاهزة، وليس تسجيلاً بشرياً؛ لم تُحسم طبيعته أو سلامة نطقه بالاستماع البشري.** هذا إعداد وتجربة قصة خيالية قصيرة، لا الفيلم السينمائي النهائي أو مولّد قصة كاملة من جملة واحدة.

## ماذا فُحص من `main`؟

أصل `main` كان أربعة ملفات: عنوان README، وثيقة متطلبات مطولة، أرشيف ٣٣ لقطة شاشة لروابط وآراء، وPDF عن **تحليل** الفيديو لا إنشائه. الجرد والتوصيات وروابط البدائل المجانية وحالة تشغيل كل منها في [الدراسة](docs/analysis-ar.md) و[سجل الأدوات](config/tools.yaml). لا تعني قائمة اقتراحات تثبيت الجميع؛ اخترنا ما يعمل فعلاً على عتاد هذا الخادم (3.85 GiB RAM، بلا GPU).

## ثبّت وشغّل الأدوات هنا

تحتاج Python 3.11/3.12 وNode.js 22+ وnpm، واتصالاً بمستودعي PyPI وnpm عند التثبيت، وقرصاً يقارب 1 GB. لا مفاتيح API ولا اشتراك. `install.sh` يثبّت إصدارات Python/Node المقفلة ويجلب **أوزان صوت محلية ~145 MB** من ثلاث حزم npm مثبتة بالنسخة وSHA512؛ تُقرأ البيانات ولا تُشغّل شيفرة JavaScript الخاصة بالحزم. الأوزان خارج Git (`models/`)؛ شغّل المثبّت مجدداً عند نقل المشروع. إن أردت مسار الفيديو وحده مؤقتاً: `V_CREATOR_SKIP_LOCAL_VOICE=1 ./scripts/install.sh`، لكن `narrate` لن يعمل قبل تنزيل الأوزان.

```bash
./scripts/install.sh
./scripts/doctor.sh
.venv/bin/python -m pytest -q
.venv/bin/v-creator plan videos/fantasy-intro/video.yaml
.venv/bin/v-creator render videos/fantasy-intro/video.yaml --preview
.venv/bin/v-creator validate videos/fantasy-intro/video.yaml output/forgotten-gate/preview.mp4
```

المعاينة الأساسية `output/forgotten-gate/preview.mp4` مدتها ١٣ ثانية **من دون كلام**، وليست فيديو نهائياً. تحفظ الأصول الفرعية وSRT وMIDI وmanifest وتقرير الاختبار في `output/` المتجاهل من Git.

### استمع إلى الصوت العربي وشاهد دمجه الفعلي

```bash
.venv/bin/python scripts/local-voice.py \
  --text 'حينَ أَطْبَقَ الليلُ جَناحَيْهِ، وَجَدَتْ لَيْلى خَريطَةً لا تَعْرِفُ الطَّريقَ.' \
  --output output/arabic-voice-test.wav --speaker 0

# نسخة تجريبية أوسع توقيتاً (21 ثانية) تترك المجال للأداء غير المستعجل.
.venv/bin/v-creator narrate videos/fantasy-intro/voice-demo.yaml \
  --out output/forgotten-gate-voice-demo/narration.wav --speaker 0
.venv/bin/v-creator render videos/fantasy-intro/voice-demo.yaml --preview \
  --narration output/forgotten-gate-voice-demo/narration.wav \
  --out output/forgotten-gate-voice-demo
.venv/bin/v-creator validate videos/fantasy-intro/voice-demo.yaml \
  output/forgotten-gate-voice-demo/preview.mp4
```

بعد تنفيذ الأوامر تجد عينة المتحدث 0 في `output/arabic-voice-test.wav` والمعاينة بالصوت والموسيقى في `output/forgotten-gate-voice-demo/preview.mp4`. **المخرجات داخل `output/` محلية ومتجاهلة من Git؛ ليست روابط تنزيل على GitHub**. توجد [عينة ترحيب عربية صغيرة قابلة للتنزيل](downloads/arabic-greeting-audio.zip) بصيغتي MP3 وWAV. يولّد `narrate` السطر المشكّل من `scenes[].narration` (أو `caption` إن لم يُذكر)، ويحفظ provenance في ملف `.voice.json`؛ **يرفض قص الكلمات** إذا لم تتسع مدة المشهد، فزِدها بدلاً من تسريع الصوت. `render` يسجل النموذج المصرّح به في manifest ويخفض الموسيقى تحت الكلام. راجع الأداء والنطق واللهجة والمزج **بأذنك**؛ الاختبار التقني لا يشهد بأن الصوت بشري أو طبيعي. يتغير صوت التوليد بين التشغيلات؛ احتفظ بعينة نالت موافقتك.

[Supertonic 3 الأصلي](https://huggingface.co/Supertone/supertonic-3) يتطلب التقيد بترخيص الأوزان **OpenRAIL-M** وشروط الاستخدام/الإسناد. ملفات التشغيل هنا مأخوذة من **إعادة تغليف طرف ثالث** للحزم `@3sln/donki-lle-voice-multi{,-2,-3}@0.1.1` ومحرك [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) المرخص Apache-2.0؛ ضُبطت سلامة الحزم المجلوبة وتحققنا من تشغيلها، **لكن لم نتحقق مستقلاً من التطابق الثنائي مع وزن الناشر الأصلي**. ترخيص شفرة المغلّف MIT ليس ترخيص الأوزان. تفاصيل المقارنة مع بدائل الفصحى البشرية/الاصطناعية في [دليل الصوت](docs/voice-ar.md).

## الموشن الغرافيك والمونتاج النهائي

```bash
./scripts/motion.sh lint motion/fantasy-title
./scripts/motion.sh render motion/fantasy-title -o output/motion-title.mp4 --quality draft --low-memory-mode
```

مثال HTML/WAAPI مستقل للعناوين بـHyperFrames، **لم يُوصل تلقائياً بمشاهد YAML**. استخدم `scripts/motion.sh` على هذا لينكس ليضبط FFmpeg/Chromium/NSS. لاستبدال اللوحات بوسائط تمتلكها عيّن `image: assets/scene.jpg` و`image_license` و`image_source` لكل مشهد. `--preview` يحافظ على ضلع أكبر ≤640px، و`--final` يستخدم دقة YAML. مثال مرحلة ما بعد المراجعة:

```bash
# التسجيل البشري أو صوت AI مستنسخ بموافقة صاحب العينة صالحان للإدخال أيضاً.
.venv/bin/v-creator render videos/fantasy-intro/voice-demo.yaml --final \
  --narration /path/to/reviewed_voice.wav
```

يرفض `--final` غياب الملف الصوتي عندما يتطلبه المشروع، أو إذا تجاوزه زمنياً؛ **وجود ملف لا يثبت أنه إنساني أو مرخّص أو أن نطقه سليم**. لا eSpeak/gTTS كبديل خفي. راجع حقوق المصادر قبل النشر.

## اختيارات أكبر وحدودها

- للتعليق الذي يعني «بشرياً» حرفياً: تعاقد مع راوٍ عربي؛ أدخِل WAV بموافقته. لـTTS بالفصحى قد تقارن لاحقاً [SILMA v1](https://github.com/SILMA-AI/silma-tts) أو [Chatterbox Multilingual V3](https://github.com/resemble-ai/chatterbox) مع النموذج المحلي؛ **لم يُثبتا أو يُشغّلا هنا** بسبب الذاكرة/مصدر الأوزان. ملفات تهيئتهما الاختيارية موجودة في `scripts/install-voice.sh` و`scripts/voice.py` ولا تمثل نجاحاً محلياً لهما.
- الموسيقى الإجرائية أصلية لكنها ليست أوركسترا سينمائية؛ `score.mid` قابل للتحرير. [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) مولّد موسيقى قوي لكن أوزانه الكبيرة وعتاده لا يلائمان هذا الخادم، ولم يُشغّل هنا.
- محررا سطح المكتب [Kdenlive](https://github.com/KDE/kdenlive)/[Blender](https://github.com/blender/blender) غير مثبتين في بيئة headless؛ يمكن فتح المخرجات على جهاز مناسب. المنتج المجاني لا يمنح حقوق صورة/موسيقى/صوت شخص آخر؛ لا ترفع ملفات `private/` أو أوزان `models/` إلى Git.

اقرأ: [تحليل ملفات `main` والأدوات](docs/analysis-ar.md) · [الصوت والحقوق](docs/voice-ar.md) · [تراخيص الأصول](docs/licensing.md) · [الهندسة والاختبارات](docs/architecture.md).
