import time
from deep_translator import GoogleTranslator, MicrosoftTranslator


last_request_time = 0


def translate_text(text, source='auto', target='es', max_retries=3):
    global last_request_time
    if not text or not text.strip():
        return ''

    elapsed = time.time() - last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    for attempt in range(max_retries):
        for translator_class, name in [(GoogleTranslator, 'google'),
                                        (MicrosoftTranslator, 'microsoft')]:
            try:
                translator = translator_class(source=source, target=target)
                result = translator.translate(text)
                last_request_time = time.time()
                if result:
                    return result
            except Exception as e:
                continue
            time.sleep(0.5)

    return ''


def translate_title(title, target='es'):
    if not title:
        return ''
    translated = translate_text(title, target=target)
    return translated if translated else title


def translate_description(desc, target='es'):
    if not desc:
        return ''
    translated = translate_text(desc[:5000], target=target)
    return translated if translated else desc[:500]
