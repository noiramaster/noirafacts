import os
import sys
import json
import time
import shutil
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import INSTAGRAM_CHANNELS, MAX_VIDEOS_PER_DAY, VIDEOS_DIR, TEMP_DIR
from src.db import (init_db, add_channel, get_active_channels, is_video_processed,
                     add_video, get_pending_videos, get_today_count,
                     update_video_status, add_log, upsert_daily_summary)
from src.scraper import scrape_all_channels, download_video, discover_new_channels
from src.ocr import ocr_video
from src.translator import translate_text
from src.editor import edit_video
from src.optimizer import extract_keywords, generate_title, generate_description, generate_hashtags
from src.uploader import upload_video


LOG_STEP = 'pipeline'


def log(video_id, step, status, message='', duration=0):
    add_log(video_id, step, status, message, int(duration * 1000))
    ts = datetime.now().strftime('%H:%M:%S')
    status_icon = '✅' if status == 'success' else '❌' if status == 'error' else '⏳'
    print(f'[{ts}] {status_icon} [{step}] {message}')


def process_video(video_info):
    video_id = video_info['id']
    shortcode = video_info['shortcode']
    channel = video_info.get('channel_name', 'unknown')
    video_url = f'https://www.instagram.com/p/{shortcode}/'

    log(video_id, 'process', 'start', f'Processing {channel}/{shortcode}')
    update_video_status(video_id, 'processing')
    start_time = time.time()

    # Step 1: Download
    log(video_id, 'download', 'start', 'Downloading video...')
    dl_start = time.time()
    video_filename = f'{shortcode}.mp4'
    video_path = os.path.join(TEMP_DIR, video_filename)

    success = download_video(video_url, video_path)
    dl_time = time.time() - dl_start

    if not success or not os.path.exists(video_path):
        log(video_id, 'download', 'error', 'Download failed', dl_time)
        update_video_status(video_id, 'failed',
                            error_message='Download failed',
                            processed_at=datetime.now().isoformat())
        return False
    log(video_id, 'download', 'success', f'Downloaded {video_filename}', dl_time)

    # Step 2: OCR
    log(video_id, 'ocr', 'start', 'Running OCR...')
    ocr_start = time.time()
    original_text, ocr_confidence, source_lang = ocr_video(video_path)
    ocr_time = time.time() - ocr_start

    if not original_text:
        log(video_id, 'ocr', 'error', 'No text detected', ocr_time)
        update_video_status(video_id, 'failed',
                            error_message='No text detected',
                            processed_at=datetime.now().isoformat())
        os.remove(video_path)
        return False
    log(video_id, 'ocr', 'success',
        f'Text: "{original_text[:50]}..." (conf: {ocr_confidence:.0f}%, lang: {source_lang})',
        ocr_time)

    # Step 3: Translate
    log(video_id, 'translate', 'start', 'Translating...')
    trans_start = time.time()
    translated_text = translate_text(original_text, source=source_lang, target='es')
    trans_time = time.time() - trans_start

    if not translated_text:
        translated_text = original_text
        log(video_id, 'translate', 'warning', 'Translation empty, using original', trans_time)
    else:
        log(video_id, 'translate', 'success',
            f'Translated: "{translated_text[:50]}..."', trans_time)

    # Step 4: Edit video
    log(video_id, 'edit', 'start', 'Editing video...')
    edit_start = time.time()
    edited_path = edit_video(video_path, translated_text)
    edit_time = time.time() - edit_start

    if not edited_path:
        log(video_id, 'edit', 'error', 'Video editing failed', edit_time)
        update_video_status(video_id, 'failed',
                            error_message='Editing failed',
                            processed_at=datetime.now().isoformat())
        os.remove(video_path)
        return False
    log(video_id, 'edit', 'success', 'Video edited', edit_time)

    # Step 5: Optimize
    log(video_id, 'optimize', 'start', 'Generating metadata...')
    opt_start = time.time()
    keywords = extract_keywords(translated_text)
    title = generate_title(translated_text, keywords)
    hashtags = generate_hashtags(keywords)
    description = generate_description(translated_text, keywords)
    opt_time = time.time() - opt_start
    log(video_id, 'optimize', 'success',
        f'Title: "{title[:50]}..." Tags: {len(hashtags)}', opt_time)

    # Step 6: Upload
    log(video_id, 'upload', 'start', 'Uploading to YouTube...')
    upload_start = time.time()
    video_id_yt, video_url_yt = upload_video(
        edited_path, title, description, hashtags
    )
    upload_time = time.time() - upload_start

    if video_id_yt:
        log(video_id, 'upload', 'success',
            f'Uploaded: {video_url_yt}', upload_time)
        update_video_status(video_id, 'uploaded',
                            youtube_video_id=video_id_yt,
                            youtube_url=video_url_yt,
                            original_text=original_text,
                            translated_text=translated_text,
                            source_language=source_lang,
                            ocr_confidence=ocr_confidence,
                            title=title,
                            description=description,
                            hashtags=json.dumps(hashtags),
                            processed_at=datetime.now().isoformat())
        total_time = time.time() - start_time
        log(video_id, 'complete', 'success',
            f'Done in {total_time:.0f}s', total_time)
        result = True
    elif video_url_yt == 'quota_exceeded':
        log(video_id, 'upload', 'warning',
            'YouTube quota exceeded, queuing for tomorrow', upload_time)
        update_video_status(video_id, 'queued',
                            original_text=original_text,
                            translated_text=translated_text,
                            source_language=source_lang,
                            ocr_confidence=ocr_confidence)
        result = 'queued'
    else:
        log(video_id, 'upload', 'error',
            f'Upload failed: {video_url_yt}', upload_time)
        update_video_status(video_id, 'failed',
                            error_message=video_url_yt,
                            processed_at=datetime.now().isoformat())
        result = False

    # Cleanup
    try:
        os.remove(video_path)
        if edited_path and os.path.exists(edited_path):
            os.remove(edited_path)
    except:
        pass

    return result


def run_pipeline():
    print('=' * 60)
    print(f'  NOIRA PIPELINE - {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('=' * 60)

    init_db()
    overall_start = time.time()

    for channel in INSTAGRAM_CHANNELS:
        add_channel(channel)

    # Check daily quota
    today_uploaded = get_today_count()
    daily_remaining = max(0, MAX_VIDEOS_PER_DAY - today_uploaded)

    print(f'\nToday: {today_uploaded}/{MAX_VIDEOS_PER_DAY} uploaded')
    print(f'Remaining quota: {daily_remaining}')

    if daily_remaining <= 0:
        print('Daily quota reached. Checking if there are queued videos...')
        queued = get_pending_videos(limit=6)
        if queued:
            daily_remaining = 6
            print(f'{len(queued)} queued videos found for today')
        else:
            print('No quota remaining, skipping uploads')
            upsert_daily_summary(
                date.today().isoformat(),
                total_skipped=1
            )
            return

    # Scrape
    print(f'\n--- Scraping {len(INSTAGRAM_CHANNELS)} channels ---')
    scrape_start = time.time()

    new_videos = scrape_all_channels(set(), max_per_channel=30)

    scrape_time = time.time() - scrape_start
    print(f'Found {len(new_videos)} new videos in {scrape_time:.0f}s')

    if not new_videos:
        print('No new videos found. Trying to discover new channels...')
        discovered = discover_new_channels()
        if discovered:
            print(f'Discovered: {discovered}')
            for ch in discovered:
                if ch not in INSTAGRAM_CHANNELS:
                    add_channel(ch)

    # Filter already processed & add to DB
    videos_to_process = []
    for v in new_videos:
        if not is_video_processed(v['shortcode']):
            channel_row = [c for c in get_active_channels()
                          if c['username'] == v.get('channel', '')]
            if channel_row:
                add_video(channel_row[0]['id'], v['shortcode'])

    pending = get_pending_videos(limit=daily_remaining)
    print(f'Videos to process: {len(pending)}')

    if not pending:
        print('Nothing to process')
        upsert_daily_summary(
            date.today().isoformat(),
            total_processed=0,
            total_duration_seconds=int(time.time() - overall_start)
        )
        return

    # Process videos
    results = {'success': 0, 'failed': 0, 'queued': 0}
    for video in pending:
        result = process_video(video)
        if result is True:
            results['success'] += 1
        elif result == 'queued':
            results['queued'] += 1
        else:
            results['failed'] += 1

    # Summary
    total_time = int(time.time() - overall_start)
    print(f'\n{"=" * 60}')
    print(f'  PIPELINE COMPLETE - {total_time}s')
    print(f'  ✅ Success: {results["success"]}')
    print(f'  ⏳ Queued: {results["queued"]}')
    print(f'  ❌ Failed: {results["failed"]}')
    print(f'{"=" * 60}')

    upsert_daily_summary(
        date.today().isoformat(),
        total_scraped=len(new_videos),
        total_processed=results['success'],
        total_failed=results['failed'],
        total_uploaded=results['success'],
        total_duration_seconds=total_time
    )


if __name__ == '__main__':
    run_pipeline()
