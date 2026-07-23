"""
Ejecutar LOCALMENTE para actualizar la lista de vídeos.
Este script usa las cookies de Chrome (con Chrome ABIERTO)
para scrapear Instagram y guardar los resultados en data/videos_queue.json

Uso: python src/local_scraper.py
"""

import instaloader
import json
import os
import time
import base64
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
QUEUE_FILE = os.path.join(DATA_DIR, 'videos_queue.json')
SESSION_DIR = os.path.expanduser('~/.config/instaloader')

INSTAGRAM_CHANNELS = [
    'natubeac', 'space_aur', 'curiosamente', 'planetacurioso',
    'sabiasque', 'datoscuriososoficial', 'curiosidad_mental',
    'ciencia_curiosa', 'mundocurioso', 'naturaleza_curiosa',
    'sabiasque_ok', 'elplanetacurioso',
]


def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE) as f:
            return json.load(f)
    return []


def save_queue(queue):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2, default=str)


def get_existing_shortcodes(queue):
    return {v['shortcode'] for v in queue if v.get('status') != 'done'}


def try_scrape(username, L):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        posts = list(profile.get_posts())[:50]
        results = []
        for p in posts:
            if p.is_video_class and p.video_duration and p.video_duration <= 60:
                results.append({
                    'shortcode': p.shortcode,
                    'url': f'https://www.instagram.com/p/{p.shortcode}/',
                    'channel': username,
                    'timestamp': str(p.date),
                    'duration': p.video_duration,
                    'status': 'pending',
                })
        return results
    except Exception as e:
        print(f'  Error scraping {username}: {e}')
        return []


def main():
    print('=' * 60)
    print(f'  LOCAL SCRAPER - {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('=' * 60)
    
    queue = load_queue()
    existing = get_existing_shortcodes(queue)
    print(f'Current queue: {len(queue)} videos ({len(existing)} pending)')
    
    L = instaloader.Instaloader(
        download_pictures=False, download_videos=False, compress_json=False
    )
    
    session_file = os.path.join(SESSION_DIR, 'session-shadow4stories')
    if os.path.exists(session_file):
        L.load_session_from_file('shadow4stories')
        print('Session loaded from file')
    else:
        print('No session file found')
        print('Please login first or place a session file at:')
        print(f'  {session_file}')
        return
    
    total_new = 0
    for channel in INSTAGRAM_CHANNELS:
        print(f'\nScraping @{channel}...')
        videos = try_scrape(channel, L)
        new_count = 0
        for v in videos:
            if v['shortcode'] not in existing:
                queue.append(v)
                existing.add(v['shortcode'])
                new_count += 1
                total_new += 1
        print(f'  Found {len(videos)} videos, {new_count} new')
        time.sleep(2)
    
    save_queue(queue)
    print(f'\nTotal new videos added: {total_new}')
    print(f'Total queue size: {len(queue)}')
    
    statuses = {}
    for v in queue:
        s = v.get('status', 'pending')
        statuses[s] = statuses.get(s, 0) + 1
    print(f'Status: {statuses}')


if __name__ == '__main__':
    main()
