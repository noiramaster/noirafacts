import time
import json
import os
import subprocess
import re
import requests
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


def scrape_channel_via_instagram_api(username, max_videos=30):
    videos = []
    try:
        result = subprocess.run(
            ['yt-dlp', '--flat-playlist', '--dump-json',
             '--no-warnings', '--extractor-args', 'instagram:webpage_limit=50',
             f'https://www.instagram.com/{username}/reels/',
             '-I', f'1:{max_videos}'],
            capture_output=True, text=True, timeout=60
        )
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                shortcode = item.get('id', '')
                duration = item.get('duration', 0)
                if shortcode and duration <= 60:
                    videos.append({
                        'shortcode': shortcode,
                        'url': f'https://www.instagram.com/p/{shortcode}/',
                        'title': item.get('title', ''),
                        'timestamp': item.get('timestamp', 0),
                        'duration': duration,
                    })
            except json.JSONDecodeError:
                continue
    except subprocess.TimeoutExpired:
        pass
    except Exception as e:
        pass
    return videos


def scrape_channel_via_graphql(username, max_videos=30):
    videos = []
    try:
        url = f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': f'https://www.instagram.com/{username}/',
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            user = data.get('data', {}).get('user', {})
            edges = (user.get('edge_owner_to_timeline_media', {})
                     .get('edges', []))
            for edge in edges[:max_videos]:
                node = edge.get('node', {})
                shortcode = node.get('shortcode', '')
                if not shortcode:
                    continue
                is_video = node.get('is_video', False) or node.get('__typename') == 'GraphVideo'
                if not is_video:
                    continue
                duration = 0
                video_url = node.get('video_url', '')
                if video_url:
                    try:
                        probe = subprocess.run(
                            ['ffprobe', '-v', 'error', '-show_entries',
                             'format=duration', '-of', 'csv=p=0', video_url],
                            capture_output=True, text=True, timeout=10
                        )
                        if probe.stdout.strip():
                            duration = float(probe.stdout.strip())
                    except:
                        pass
                if duration <= 60:
                    videos.append({
                        'shortcode': shortcode,
                        'url': f'https://www.instagram.com/p/{shortcode}/',
                        'title': node.get('caption', ''),
                        'timestamp': node.get('taken_at_timestamp', 0),
                        'duration': duration,
                    })
    except:
        pass
    return videos


def scrape_channel(username, max_videos=30):
    cache_file = os.path.join(DATA_DIR, f'cache_{username}.json')

    if os.path.exists(cache_file):
        try:
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < 1800:
                with open(cache_file) as f:
                    return json.load(f)
        except:
            pass

    videos = scrape_channel_via_instagram_api(username, max_videos)

    if not videos:
        videos = scrape_channel_via_graphql(username, max_videos)

    if videos:
        with open(cache_file, 'w') as f:
            json.dump(videos, f)

    return videos


def filter_new_videos(videos, existing_shortcodes):
    return [v for v in videos if v['shortcode'] not in existing_shortcodes]


def is_short_video(duration):
    return duration <= 60 or duration == 0


def download_video(url, output_path):
    try:
        result = subprocess.run(
            ['yt-dlp', '-f', 'best[height<=1080]', '-o', output_path,
             '--no-playlist', '--no-warnings', '--no-check-certificate',
             url],
            capture_output=True, text=True, timeout=120
        )
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except:
        return False


def discover_new_channels():
    hashtags = ['datoscuriosos', 'curiosidades', 'ciencia',
                'naturaleza', 'space', 'datos_curiosos']
    candidates = set()

    for tag in hashtags:
        try:
            url = f'https://www.instagram.com/explore/tags/{tag}/'
            result = subprocess.run(
                ['yt-dlp', '--flat-playlist', '--dump-json',
                 '--no-warnings', url, '-I', '1:10'],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    uploader = item.get('channel_id', item.get('uploader', ''))
                    if uploader and uploader.lower() not in [c.lower() for c in INSTAGRAM_CHANNELS]:
                        candidates.add(uploader)
                except:
                    continue
        except:
            continue

    return list(candidates)[:5]


def scrape_all_channels(existing_shortcodes=None, max_per_channel=30):
    if existing_shortcodes is None:
        existing_shortcodes = get_existing_shortcodes()

    all_new = []
    for channel in INSTAGRAM_CHANNELS:
        try:
            videos = scrape_channel(channel, max_per_channel)
            new_videos = [v for v in videos
                         if v['shortcode'] not in existing_shortcodes
                         and is_short_video(v.get('duration', 0))]
            for v in new_videos:
                v['channel'] = channel
            all_new.extend(new_videos)
            time.sleep(2)
        except Exception as e:
            continue

    return all_new
