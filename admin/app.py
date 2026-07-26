"""Flask Admin Panel for YT Downloader Bot."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import secrets
from database import (
    init_db, get_setting, set_setting, get_all_users, get_user,
    toggle_ban, set_user_limit, get_stats, search_users,
    log_broadcast, get_broadcast_logs
)
from config import ADMIN_DEFAULT_PASSWORD

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = secrets.token_hex(32)


def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    """Redirect to dashboard."""
    if session.get("admin_logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page."""
    if request.method == "POST":
        password = request.form.get("password", "")
        stored_password = get_setting("admin_password", ADMIN_DEFAULT_PASSWORD)
        if password == stored_password:
            session["admin_logged_in"] = True
            session.permanent = True
            flash("ورود موفق! ✅", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("رمز عبور اشتباه است! ❌", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Admin logout."""
    session.clear()
    flash("خروج موفق بودید.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@admin_required
def dashboard():
    """Admin dashboard with stats."""
    stats = get_stats()
    return render_template("dashboard.html", stats=stats)


@app.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    """Bot settings (token, password, daily limit)."""
    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "update_token":
            token = request.form.get("bot_token", "").strip()
            set_setting("bot_token", token)
            flash("توکن ربات ذخیره شد! ✅", "success")

        elif action == "update_password":
            new_pass = request.form.get("new_password", "").strip()
            confirm = request.form.get("confirm_password", "").strip()
            if new_pass and new_pass == confirm:
                set_setting("admin_password", new_pass)
                flash("رمز عبور تغییر کرد! ✅", "success")
            else:
                flash("رمزهای عبور مطابقت ندارند! ❌", "danger")

        elif action == "update_limit":
            limit = request.form.get("daily_limit", "10")
            try:
                limit = int(limit)
                if 1 <= limit <= 100:
                    set_setting("default_daily_limit", str(limit))
                    flash(f"محدودیت روزانه به {limit} دانلود تغییر کرد! ✅", "success")
                else:
                    flash("مقدار باید بین ۱ تا ۱۰۰ باشد! ❌", "danger")
            except ValueError:
                flash("مقدار نامعتبر! ❌", "danger")

        return redirect(url_for("settings"))

    return render_template("settings.html",
                         bot_token=get_setting("bot_token"),
                         daily_limit=get_setting("default_daily_limit", "10"))


@app.route("/users")
@admin_required
def users():
    """Manage users."""
    search = request.args.get("q", "").strip()
    if search:
        user_list = search_users(search)
    else:
        user_list = get_all_users()
    return render_template("users.html", users=user_list, search=search)


@app.route("/users/<int:user_id>/toggle-ban", methods=["POST"])
@admin_required
def user_toggle_ban(user_id):
    """Ban/unban a user."""
    toggle_ban(user_id)
    flash("وضعیت بن کاربر تغییر کرد! ✅", "success")
    return redirect(url_for("users"))


@app.route("/users/<int:user_id>/set-limit", methods=["POST"])
@admin_required
def user_set_limit(user_id):
    """Set user's daily download limit."""
    limit = request.form.get("limit", "10")
    try:
        set_user_limit(user_id, int(limit))
        flash(f"محدودیت روزانه کاربر به {limit} تغییر کرد! ✅", "success")
    except ValueError:
        flash("مقدار نامعتبر! ❌", "danger")
    return redirect(url_for("users"))


@app.route("/broadcast", methods=["GET", "POST"])
@admin_required
def broadcast():
    """Send broadcast message to all users."""
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message:
            from database import get_db
            conn = get_db()
            all_users = conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
            conn.close()

            sent = 0
            for user in all_users:
                try:
                    import urllib.request
                    token = get_setting("bot_token")
                    if token:
                        url = f"https://api.telegram.org/bot{token}/sendMessage"
                        data = f'{{"chat_id": {user["user_id"]}, "text": "{message}", "parse_mode": "HTML"}}'.encode()
                        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                        urllib.request.urlopen(req, timeout=5)
                        sent += 1
                except Exception:
                    pass

            log_broadcast(message, sent)
            flash(f"پیام به {sent} کاربر ارسال شد! ✅", "success")
        else:
            flash("پیام خالی نمی‌تواند ارسال شود! ❌", "danger")
        return redirect(url_for("broadcast"))

    logs = get_broadcast_logs()
    return render_template("broadcast.html", logs=logs)


@app.route("/api/stats")
@admin_required
def api_stats():
    """API endpoint for live stats."""
    stats = get_stats()
    return jsonify({
        "total_users": stats["total_users"],
        "active_today": stats["active_today"],
        "total_downloads": stats["total_downloads"],
        "today_downloads": stats["today_downloads"],
    })


def run_admin(host="0.0.0.0", port=5001):
    """Run the admin panel."""
    init_db()
    print(f"🌐 Admin Panel: http://{host}:{port}")
    print(f"🔑 Default Password: {ADMIN_DEFAULT_PASSWORD}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_admin()
