from django.shortcuts import render

# Create your views here.
from django.shortcuts import render  #
from django.http import HttpResponseBadRequest
from django.conf import settings
from gtts import gTTS
from gtts.lang import tts_langs
from deep_translator import GoogleTranslator
import uuid
from pathlib import Path

SUPPORTED_TTS = tts_langs()  # dict of supported language codes

def index(request):
    # default: translate is ON so English → Marathi works out of the box
    return render(request, "index.html", {"translate_first": True})

def convert_text(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    text = (request.POST.get("text") or "").strip()
    lang = (request.POST.get("lang") or "en").strip()
    translate_first = request.POST.get("translate_first") == "on"
    slow = request.POST.get("slow") == "on"

    if not text:
        return render(request, "index.html", {"error": "Please enter some text.", "translate_first": translate_first})

    if lang not in SUPPORTED_TTS:
        return render(request, "index.html", {"error": f"Language '{lang}' not supported by gTTS.", "translate_first": translate_first})

    # 1) Translate (English → chosen language) if enabled
    translated_text = None
    translation_error = None
    text_for_tts = text
    if translate_first:
        try:
            translated_text = GoogleTranslator(source="auto", target=lang).translate(text)
            if translated_text and translated_text.strip():
                text_for_tts = translated_text.strip()
        except Exception as e:
            translation_error = f"Auto-translate failed ({e}). Speaking original text instead."

    # 2) Generate the MP3
    media_dir = Path(settings.MEDIA_ROOT) / "tts"
    media_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.mp3"
    file_path = media_dir / filename
    rel_url = f"{settings.MEDIA_URL}tts/{filename}"

    try:
        tts = gTTS(text=text_for_tts, lang=lang, slow=slow)
        tts.save(str(file_path))
    except Exception as e:
        return render(request, "index.html", {"error": f"TTS failed: {e}", "translate_first": translate_first})

    return render(request, "index.html", {
        "audio_file": rel_url,
        "entered_text": text,
        "selected_lang": lang,
        "translated_text": translated_text,
        "translation_error": translation_error,
        "slow": slow,
        "translate_first": translate_first,
    })