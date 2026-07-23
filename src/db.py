import sqlite3
import json
from datetime import datetime, date
from src.config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT,
            is_active INTEGER DEFAULT 1,
            added_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER REFERENCES channels(id),
            shortcode TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending',
            source_language TEXT,
            original_text TEXT,
            translated_text TEXT,
            ocr_confidence REAL,
            youtube_video_id TEXT,
            youtube_url TEXT,
            title TEXT,
            description TEXT,
            hashtags TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            processed_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER REFERENCES videos(id),
            step TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            duration_ms INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS daily_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT UNIQUE NOT NULL,
            total_scraped INTEGER DEFAULT 0,
            total_processed INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            total_skipped INTEGER DEFAULT 0,
            total_uploaded INTEGER DEFAULT 0,
            total_duration_seconds INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
        CREATE INDEX IF NOT EXISTS idx_videos_shortcode ON videos(shortcode);
        CREATE INDEX IF NOT EXISTS idx_logs_video ON logs(video_id);
    ''')
    conn.commit()
    conn.close()


def add_channel(username):
    conn = get_connection()
    conn.execute(
        'INSERT OR IGNORE INTO channels (username) VALUES (?)',
        (username,)
    )
    conn.commit()
    conn.close()


def get_active_channels():
    conn = get_connection()
    rows = conn.execute(
        'SELECT * FROM channels WHERE is_active = 1'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def is_video_processed(shortcode):
    conn = get_connection()
    row = conn.execute(
        'SELECT id FROM videos WHERE shortcode = ?',
        (shortcode,)
    ).fetchone()
    conn.close()
    return row is not None


def add_video(channel_id, shortcode):
    conn = get_connection()
    conn.execute(
        'INSERT OR IGNORE INTO videos (channel_id, shortcode) VALUES (?, ?)',
        (channel_id, shortcode)
    )
    conn.commit()
    conn.close()


def get_pending_videos(limit=6):
    conn = get_connection()
    rows = conn.execute(
        '''SELECT v.*, c.username as channel_name
           FROM videos v
           JOIN channels c ON c.id = v.channel_id
           WHERE v.status = 'pending'
           ORDER BY v.created_at ASC
           LIMIT ?''',
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_count():
    today = date.today().isoformat()
    conn = get_connection()
    row = conn.execute(
        '''SELECT COUNT(*) as cnt FROM videos
           WHERE status = 'uploaded'
           AND date(processed_at) = ?''',
        (today,)
    ).fetchone()
    conn.close()
    return row['cnt'] if row else 0


def update_video_status(video_id, status, **kwargs):
    fields = ['status = ?', 'updated_at = datetime(\'now\')']
    values = [status]
    for key, val in kwargs.items():
        fields.append(f'{key} = ?')
        values.append(val)
    values.append(video_id)
    conn = get_connection()
    conn.execute(
        f'UPDATE videos SET {", ".join(fields)} WHERE id = ?',
        values
    )
    conn.commit()
    conn.close()


def add_log(video_id, step, status, message='', duration_ms=0):
    conn = get_connection()
    conn.execute(
        '''INSERT INTO logs (video_id, step, status, message, duration_ms)
           VALUES (?, ?, ?, ?, ?)''',
        (video_id, step, status, message, duration_ms)
    )
    conn.commit()
    conn.close()


def get_daily_summary():
    conn = get_connection()
    rows = conn.execute(
        '''SELECT run_date, total_scraped, total_processed,
                  total_failed, total_skipped, total_uploaded,
                  total_duration_seconds
           FROM daily_summary
           ORDER BY run_date DESC
           LIMIT 30'''
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_daily_summary(run_date, **kwargs):
    conn = get_connection()
    existing = conn.execute(
        'SELECT id FROM daily_summary WHERE run_date = ?',
        (run_date,)
    ).fetchone()
    if existing:
        fields = []
        values = []
        for key, val in kwargs.items():
            fields.append(f'{key} = {key} + ?')
            values.append(val)
        values.append(run_date)
        conn.execute(
            f'UPDATE daily_summary SET {", ".join(fields)} WHERE run_date = ?',
            values
        )
    else:
        fields = ['run_date'] + list(kwargs.keys())
        values = [run_date] + list(kwargs.values())
        placeholders = ','.join(['?'] * len(values))
        conn.execute(
            f'INSERT INTO daily_summary ({", ".join(fields)}) VALUES ({placeholders})',
            values
        )
    conn.commit()
    conn.close()


def get_all_videos_for_dashboard(limit=100):
    conn = get_connection()
    rows = conn.execute(
        '''SELECT v.*, c.username as channel_name
           FROM videos v
           JOIN channels c ON c.id = v.channel_id
           ORDER BY v.created_at DESC
           LIMIT ?''',
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = get_connection()
    stats = conn.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'uploaded' THEN 1 ELSE 0 END) as uploaded,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing
        FROM videos
    ''').fetchone()
    conn.close()
    return dict(stats)
