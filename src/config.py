import os
import json
from dotenv import load_dotenv

load_dotenv()

YT_CLIENT_ID = os.getenv('YT_CLIENT_ID', '')
YT_CLIENT_SECRET = os.getenv('YT_CLIENT_SECRET', '')
YT_REFRESH_TOKEN = os.getenv('YT_REFRESH_TOKEN', '')

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

MAX_VIDEOS_PER_DAY = int(os.getenv('MAX_VIDEOS_PER_DAY', '6'))
TARGET_LANGUAGE = os.getenv('TARGET_LANGUAGE', 'es')
TESSERACT_LANG = os.getenv('TESSERACT_LANG', 'ara+eng')
RUN_HOUR = int(os.getenv('RUN_HOUR', '20'))
RUN_MINUTE = int(os.getenv('RUN_MINUTE', '0'))

YT_VIDEO_MAX_DURATION = int(os.getenv('YT_VIDEO_MAX_DURATION', '60'))
YT_VIDEO_MIN_VIEWS = int(os.getenv('YT_VIDEO_MIN_VIEWS', '0'))

YOUTUBE_CHANNELS = []
channels_file = os.path.join(BASE_DIR, 'data', 'channels.json')
if os.path.exists(channels_file):
    try:
        with open(channels_file) as f:
            YOUTUBE_CHANNELS = json.load(f)
    except:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'pipeline.db')
VIDEOS_DIR = os.path.join(DATA_DIR, 'videos')
TEMP_DIR = os.path.join(DATA_DIR, 'temp')

for d in [DATA_DIR, VIDEOS_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)
