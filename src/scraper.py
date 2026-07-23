import subprocess
import json
import os
import time
import re
from datetime import datetime
from src.config import (
    YOUTUBE_CHANNELS, TEMP_DIR, DATA_DIR, YT_VIDEO_MAX_DURATION,
    YT_VIDEO_MIN_VIEWS
)


def get_channel_url(channel):
    if 'handle' in channel:
        return f'https://www.youtube.com/{channel["handle"]}/shorts'
    return f'https://www.youtube.com/channel/{channel["id"]}/shorts'


def scrape_channel(channel, max_videos=30):
    name = channel.get('name', channel.get('handle', channel.get('id', '')))
    channel_url = get_channel_url(channel)
    cache_file = os.path.join(DATA_DIR, f'yt_cache_{name.replace("/","_")}.json')

    if os.path.exists(cache_file):
        try:
            age = time.time() - os.path.getmtime(cache_file)
            if age < 1800:
                with open(cache_file) as f:
                    return json.load(f)
        except:
            pass

    videos = []
    try:
        result = subprocess.run(
            ['yt-dlp', '--flat-playlist', '--dump-json',
             '--no-warnings', '--no-check-certificate',
             channel_url, '-I', f'1:{max_videos}'],
            capture_output=True, text=True, timeout=60
        )
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                duration = item.get('duration', 0)
                if duration == 0:
                    continue
                if duration > YT_VIDEO_MAX_DURATION:
                    continue
                views = item.get('view_count', 0)
                if views < YT_VIDEO_MIN_VIEWS:
                    continue
                video_id = item.get('id', '')
                if not video_id:
                    continue
                videos.append({
                    'id': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'title': item.get('title', ''),
                    'channel_name': name,
                    'channel_handle': channel.get('handle', ''),
                    'duration': duration,
                    'view_count': item.get('view_count', 0),
                    'timestamp': item.get('timestamp', 0),
                    'source': 'youtube',
                })
            except json.JSONDecodeError:
                continue
    except subprocess.TimeoutExpired:
        pass
    except Exception as e:
        pass

    if videos:
        with open(cache_file, 'w') as f:
            json.dump(videos, f)

    return videos


def download_video(url, output_path):
    try:
        result = subprocess.run(
            ['yt-dlp', '-f', 'best[height<=720]', '-o', output_path,
             '--no-playlist', '--no-warnings', '--no-check-certificate',
             url],
            capture_output=True, text=True, timeout=120
        )
        return os.path.exists(output_path) and os.path.getsize(output_path) > 10000
    except:
        return False


def scrape_all_channels(existing_ids=None):
    if existing_ids is None:
        existing_ids = set()

    all_videos = []
    for channel in YOUTUBE_CHANNELS:
        try:
            videos = scrape_channel(channel, max_videos=30)
            new_videos = [v for v in videos if v['id'] not in existing_ids]
            all_videos.extend(new_videos)
            time.sleep(1)
        except Exception as e:
            continue

    return all_videos
