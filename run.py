#!/usr/bin/env python3
"""
YT Downloader Bot + Admin Panel
Main entry point - starts both bot and web admin.

Usage:
    python run.py              # Start both bot + admin
    python run.py --admin      # Start admin panel only
    python run.py --bot        # Start bot only
    python run.py --setup      # First-time setup
"""

import sys
import os
import threading
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_setting
from config import ADMIN_DEFAULT_PASSWORD


def run_admin_panel():
    """Run the Flask admin panel."""
    from admin.app import run_admin
    run_admin(host="0.0.0.0", port=5001)


def run_telegram_bot():
    """Run the Telegram bot."""
    token = get_setting("bot_token")
    if not token:
        print("⚠️  توکن ربات تنظیم نشده!")
        print("   ابتدا پنل ادمین را باز کنید و توکن ربات را وارد کنید:")
        print(f"   http://localhost:5001")
        print(f"   رمز عبور: {ADMIN_DEFAULT_PASSWORD}")
        return
    
    from bot.handlers import run_bot
    run_bot(token)


def first_time_setup():
    """First-time setup wizard."""
    print("=" * 50)
    print("🎬 YT Downloader Bot - Setup Wizard")
    print("=" * 50)
    print()
    
    init_db()
    
    print("✅ دیتابیس ساخته شد!")
    print()
    print("📌 مراحل بعدی:")
    print(f"   1. پنل ادمین را باز کنید: http://localhost:5001")
    print(f"   2. با رمز '{ADMIN_DEFAULT_PASSWORD}' وارد شوید")
    print(f"   3. توکن ربات تلگرام را وارد کنید")
    print(f"   4. ربات را اجرا کنید: python run.py")
    print()
    
    choice = input("آیا می‌خواهید پنل ادمین را الان باز کنید؟ (y/n): ")
    if choice.lower() in ["y", "yes", "بله"]:
        print("\n🌐 پنل ادمین روی http://localhost:5001 باز شد...")
        run_admin_panel()
    else:
        print("\n✅ Setup کامل شد! بعداً با 'python run.py' اجرا کنید.")


def main():
    parser = argparse.ArgumentParser(description="YT Downloader Bot + Admin Panel")
    parser.add_argument("--admin", action="store_true", help="Admin panel only")
    parser.add_argument("--bot", action="store_true", help="Bot only")
    parser.add_argument("--setup", action="store_true", help="First-time setup")
    parser.add_argument("--port", type=int, default=5001, help="Admin panel port")
    
    args = parser.parse_args()
    
    if args.setup:
        first_time_setup()
        return
    
    # Initialize database
    init_db()
    
    print("=" * 50)
    print("🎬 YT Downloader Bot + Admin Panel")
    print("=" * 50)
    print()
    
    if args.admin:
        run_admin_panel()
    elif args.bot:
        run_telegram_bot()
    else:
        # Start admin in a separate thread
        admin_thread = threading.Thread(target=run_admin_panel, daemon=True)
        admin_thread.start()
        
        print(f"🌐 Admin Panel: http://localhost:{args.port}")
        print(f"🔑 Password: {ADMIN_DEFAULT_PASSWORD}")
        print()
        
        # Start bot in main thread
        run_telegram_bot()


if __name__ == "__main__":
    main()
