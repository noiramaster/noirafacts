import yake
import re


HASHTAGS_POOL = [
    'datoscuriosos', 'curiosidades', 'sabiasque', 'datos', 'curioso',
    'aprende', 'conocimiento', 'sabiduria', 'mente', 'ciencia',
    'naturaleza', 'espacio', 'mundo', 'interesante', 'educativo',
    'reels', 'shorts', 'viral', 'datosinteresantes', 'noira'
]

EMOJI_MAP = {
    'ciencia': '🔬', 'naturaleza': '🌿', 'espacio': '🚀',
    'mundo': '🌍', 'mente': '🧠', 'curiosidad': '💡',
    'aprende': '📚', 'dato': '💎', 'sabias': '🤔',
    'historia': '📜', 'tecnologia': '💻', 'animal': '🐾',
    'cuerpo': '🫀', 'universo': '🌌', 'default': '✨'
}


def extract_keywords(text, max_keywords=5):
    if not text or len(text) < 3:
        return []
    try:
        kw_extractor = yake.KeywordExtractor(
            lan='es', n=1, dedupLim=0.9,
            top=10, features=None
        )
        keywords = kw_extractor.extract_keywords(text)
        return [kw.strip().lower() for kw, _ in keywords[:max_keywords]]
    except:
        return []


def get_emoji(text):
    text_lower = text.lower()
    for key, emoji in EMOJI_MAP.items():
        if key in text_lower:
            return emoji
    return EMOJI_MAP['default']


def generate_title(translated_text, keywords):
    emoji = get_emoji(translated_text)
    text_preview = translated_text[:60].strip()
    if len(translated_text) > 60:
        text_preview += '...'

    keywords_str = ', '.join(keywords[:3]) if keywords else ''

    templates = [
        f'{emoji} {text_preview}',
        f'{emoji} ¡{text_preview}!',
        f'¿Sabías esto? {emoji} {text_preview}',
        f'{text_preview} {emoji} #shorts',
    ]

    title = templates[0][:100]
    return title


def generate_description(translated_text, keywords, channel_name='Noira'):
    desc = f'{translated_text}\n\n'
    if keywords:
        desc += f'📌 {", ".join(keywords[:5])}\n\n'
    desc += f'🔥 Síguenos en @{channel_name} para más datos curiosos.\n'
    desc += f'🔔 Activa la campanita para no perderte ningún video.\n'
    desc += f'💬 ¿Conocías este dato? Déjanos tu comentario.\n\n'
    desc += '#Noira #DatosCuriosos #Shorts'
    return desc[:5000]


def generate_hashtags(keywords, max_tags=8):
    all_tags = set()
    for kw in keywords:
        tag = re.sub(r'[^a-zA-Z0-9]', '', kw)
        if len(tag) > 2:
            all_tags.add(tag.lower())

    for tag in HASHTAGS_POOL[:5]:
        all_tags.add(tag)

    while len(all_tags) < min(5, max_tags):
        for tag in HASHTAGS_POOL:
            all_tags.add(tag)
            if len(all_tags) >= max_tags:
                break

    return list(all_tags)[:max_tags]
