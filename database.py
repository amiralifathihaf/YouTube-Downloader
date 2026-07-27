
import sqlite3
import os
from datetime import datetime, date
from config import DATABASE_PATH, ADMIN_DEFAULT_PASSWORD, DEFAULT_DAILY_LIMIT


def get_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_banned INTEGER DEFAULT 0,
            daily_downloads INTEGER DEFAULT 0,
            daily_limit INTEGER DEFAULT 10,
            download_date TEXT,
            total_downloads INTEGER DEFAULT 0,
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            last_active TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            video_url TEXT NOT NULL,
            video_title TEXT,
            quality TEXT,
            file_size INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS broadcast_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            sent_to INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def register_user(user_id, username=None, full_name=None):
    conn = get_db()
    today = date.today().isoformat()
    existing = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()

    if existing:
        if existing["download_date"] != today:
            conn.execute("""UPDATE users SET download_date=?, daily_downloads=0,
                          last_active=CURRENT_TIMESTAMP, username=?, full_name=?
                          WHERE user_id=?""",
                         (today, username or existing["username"],
                          full_name or existing["full_name"], user_id))
        else:
            conn.execute("""UPDATE users SET last_active=CURRENT_TIMESTAMP,
                          username=?, full_name=? WHERE user_id=?""",
                         (username or existing["username"],
                          full_name or existing["full_name"], user_id))
    else:
        daily_limit = int(get_setting("default_daily_limit", str(DEFAULT_DAILY_LIMIT)))
        conn.execute("""INSERT INTO users (user_id, username, full_name, download_date, daily_limit)
                      VALUES (?, ?, ?, ?, ?)""",
                     (user_id, username, full_name, today, daily_limit))

    conn.commit()
    conn.close()


def can_user_download(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()

    if not user:
        return True, "ok"

    if user["is_banned"]:
        return False, "banned"

    today = date.today().isoformat()
    if user["download_date"] != today:
        return True, "ok"

    if user["daily_downloads"] >= user["daily_limit"]:
        return False, "limit_reached"

    return True, "ok"


def increment_download(user_id, video_url, video_title, quality, file_size=0):
    conn = get_db()
    today = date.today().isoformat()

    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if user and user["download_date"] != today:
        conn.execute("UPDATE users SET download_date=?, daily_downloads=0 WHERE user_id=?",
                      (today, user_id))

    conn.execute("UPDATE users SET daily_downloads = daily_downloads + 1, total_downloads = total_downloads + 1 WHERE user_id=?", (user_id,))
    conn.execute("""INSERT INTO downloads (user_id, video_url, video_title, quality, file_size, status)
                  VALUES (?, ?, ?, ?, ?, 'completed')""",
                 (user_id, video_url, video_title, quality, file_size))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY first_seen DESC").fetchall()
    conn.close()
    return users


def get_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return user


def toggle_ban(user_id):
    conn = get_db()
    user = conn.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,)).fetchone()
    if user:
        new_status = 0 if user["is_banned"] else 1
        conn.execute("UPDATE users SET is_banned=? WHERE user_id=?", (new_status, user_id))
        conn.commit()
    conn.close()


def set_user_limit(user_id, limit):
    conn = get_db()
    conn.execute("UPDATE users SET daily_limit=? WHERE user_id=?", (limit, user_id))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    active_today = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE download_date=?", (date.today().isoformat(),)
    ).fetchone()["c"]
    total_downloads = conn.execute("SELECT COALESCE(SUM(total_downloads), 0) as c FROM users").fetchone()["c"]
    today_downloads = conn.execute(
        "SELECT COUNT(*) as c FROM downloads WHERE date(created_at)=?", (date.today().isoformat(),)
    ).fetchone()["c"]
    banned_users = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_banned=1").fetchone()["c"]
    recent_downloads = conn.execute(
        "SELECT * FROM downloads ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return {
        "total_users": total_users,
        "active_today": active_today,
        "total_downloads": total_downloads,
        "today_downloads": today_downloads,
        "banned_users": banned_users,
        "recent_downloads": recent_downloads,
    }


def log_broadcast(message, sent_to):
    conn = get_db()
    conn.execute("INSERT INTO broadcast_logs (message, sent_to) VALUES (?, ?)", (message, sent_to))
    conn.commit()
    conn.close()


def get_broadcast_logs():
    conn = get_db()
    logs = conn.execute("SELECT * FROM broadcast_logs ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()
    return logs


def search_users(query):
    conn = get_db()
    users = conn.execute(
        "SELECT * FROM users WHERE username LIKE ? OR user_id LIKE ? OR full_name LIKE ?",
        (f"%{query}%", f"%{query}%", f"%{query}%")
    ).fetchall()
    conn.close()
    return users
