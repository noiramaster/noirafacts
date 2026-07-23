import time
import json
import os
import subprocess
from datetime import datetime, timedelta
from src.config import INSTAGRAM_CHANNELS, VIDEOS_DIR, DATA_DIR


def get_existing_shortcodes():
    existing = set()
    for f in os.listdir(VIDEOS_DIR):
        if f.endswith('.json'):
            try:
                data = json.load(open(os.path.join(VIDEOS_DIR, f)))
                existing.add(data.get('shortcode', f.replace('.json', '')))
            except:
                pass
    return existing


def scrape_channel(username, max_videos=50):
    videos = []
    cache_file = os.path.join(DATA_DIR, f'cache_{username}.json')

    cached = []
    if os.path.exists(cache_file):
        try:
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < 3600:
                cached = json.load(open(cache_file))
        except:
            pass

    if cached:
        return cached

    try:
        result = subprocess.run(
            ['yt-dlp', '--flat-playlist', '--dump-json',
             f'https://www.instagram.com/{username}/reels/',
             '-I', f'1:{max_videos}'],
            capture_output=True, text=True, timeout=60
        )
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                videos.append({
                    'shortcode': item.get('id', ''),
                    'url': f'https://www.instagram.com/p/{item.get("id", "")}/',
                    'title': item.get('title', ''),
                    'timestamp': item.get('timestamp', 0),
                    'duration': item.get('duration', 0),
                })
            except json.JSONDecodeError:
                continue
    except Exception as e:
        pass

    try:
        result = subprocess.run(
            ['instaloader', '--no-pictures', '--no-video-thumbnails',
             '--no-metadata-json', '--no-captions',
             '--count', str(max_videos),
             '--dirname-pattern', VIDEOS_DIR,
             f'--', f'-{username}'],
            capture_output=True, text=True, timeout=120
        )
    except:
        pass

    if videos:
        json.dump(videos, open(cache_file, 'w'))

    return videos


def filter_new_videos(videos, existing_shortcodes):
    return [v for v in videos if v['shortcode'] not in existing_shortcodes]


def is_short_video(duration):
    return duration <= 60


def download_video(url, output_path):
    try:
        subprocess.run(
            ['yt-dlp', '-f', 'best[height<=1080]', '-o', output_path,
             '--no-playlist', '--no-warnings', url],
            capture_output=True, text=True, timeout=120
        )
        return os.path.exists(output_path)
    except:
        return False


def discover_new_channels():
    hashtags = ['datoscuriosos', 'curiosidades', 'ciencia',
                'naturaleza', 'space', 'datos_curiosos']
    candidates = set()

    for tag in hashtags:
        try:
            result = subprocess.run(
                ['yt-dlp', '--flat-playlist', '--dump-json',
                 f'https://www.instagram.com/explore/tags/{tag}/',
                 '-I', '1:20'],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    uploader = item.get('channel_id', item.get('uploader', ''))
                    if uploader and uploader not in INSTAGRAM_CHANNELS:
                        candidates.add(uploader)
                except:
                    continue
        except:
            continue

    return list(candidates)[:5]


def scrape_all_channels(existing_shortcodes, max_per_channel=50):
    all_new = []
    for channel in INSTAGRAM_CHANNELS:
        try:
            videos = scrape_channel(channel, max_per_channel)
            new_videos = filter_new_videos(videos, existing_shortcodes)
            short_videos = [v for v in new_videos if is_short_video(v.get('duration', 0))]
            for v in short_videos:
                v['channel'] = channel
            all_new.extend(short_videos)
            time.sleep(3)
        except Exception as e:
            continue

    return all_new
