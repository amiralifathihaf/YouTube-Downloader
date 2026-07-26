<div dir="rtl">

# 🎬 YT Downloader Bot

ربات دانلود ویدیو یوتیوب با پنل مدیریت وب

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API%20v9-26A5E4.svg)](https://core.telegram.org/bots/api)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ امکانات

### 🤖 ربات تلگرام
- 📥 دانلود ویدیو با ارسال لینک
- 🎯 انتخاب کیفیت (480p / 720p / 1080p)
- 🎨 دکمه‌های رنگی (Telegram Bot API v9)
- 📊 نمایش وضعیت دانلود
- 🚫 سیستم بن کاربران
- ⏰ محدودیت دانلود روزانه
- 📱 ریسپانسیو و سریع

### 🌐 پنل مدیریت
- 🔐 ورود با رمز عبور
- 📊 داشبورد آماری
- 👥 مدیریت کاربران (جستجو، بن، آنبان)
- ⚙️ تنظیمات (توکن ربات، محدودیت‌ها)
- 📢 ارسال پیام همگانی
- 📈 نمایش آمار دانلود
- 🎨 رابط کاربری تاریک و زیبا

---

## 📸 نمای پنل ادمین

| داشبورد | کاربران | تنظیمات |
|---------|---------|---------|
| 📊 آمار کلی | 👥 مدیریت کامل | ⚙️ توکن ربات |
| 📈 نمودار دانلود | 🔍 جستجوی پیشرفته | 🔑 تغییر رمز |
| 📋 لاگ فعالیت | 🚫 بن/آنبان | ⏰ محدودیت روزانه |

---

## 🚀 نصب و اجرا

### پیش‌نیازها
- Python 3.8+
- yt-dlp
- یک توکن ربات تلگرام (از @BotFather)

### مراحل نصب

```bash
# 1. کلون کردن پروژه
git clone https://github.com/AnyCodeGP/yt-downloader-bot.git
cd yt-downloader-bot

# 2. ساخت محیط مجازی
python -m venv venv
source venv/bin/activate  # لینوکس/مک
# venv\Scripts\activate  # ویندوز

# 3. نصب وابستگی‌ها
pip install -r requirements.txt

# 4. اجرای setup
python run.py --setup
```

### اجرا

```bash
# اجرای کامل (ربات + پنل ادمین)
python run.py

# فقط پنل ادمین
python run.py --admin

# فقط ربات
python run.py --bot
```

### راه‌اندازی

1. **پنل ادمین** روی `http://localhost:5001` باز می‌شود
2. با رمز `admin1234` وارد شوید
3. از بخش **تنظیمات**، توکن ربات تلگرام را وارد کنید
4. ربات شروع به کار می‌کند! 🎉

---

## 📁 ساختار پروژه

```
yt-downloader-bot/
├── run.py                 # فایل اجرایی اصلی
├── config.py              # تنظیمات
├── database.py            # دیتابیس مشترک
├── requirements.txt       # وابستگی‌ها
├── README.md              # این فایل
├── .gitignore
│
├── bot/                   # ربات تلگرام
│   ├── __init__.py
│   ├── handlers.py        # هندلرهای پیام
│   └── downloader.py      # دانلودر یوتیوب
│
└── admin/                 # پنل مدیریت
    ├── __init__.py
    ├── app.py             # Flask application
    ├── static/
    │   └── style.css      # استایل‌ها
    └── templates/
        ├── base.html      # قالب پایه
        ├── login.html     # صفحه ورود
        ├── dashboard.html # داشبورد
        ├── users.html     # مدیریت کاربران
        ├── broadcast.html # پیام همگانی
        └── settings.html  # تنظیمات
```

---

## 🔧 تنظیمات

| تنظیم | مقدار پیش‌فرض | توضیح |
|-------|---------------|-------|
| `ADMIN_DEFAULT_PASSWORD` | `admin1234` | رمز پنل ادمین |
| `DEFAULT_DAILY_LIMIT` | `10` | محدودیت دانلود روزانه |
| `MAX_FILE_SIZE_MB` | `2000` | حداکثر حجم فایل (MB) |

---

## 🌐 استقرار روی سرور

### با Gunicorn (پیشنهادی)

```bash
pip install gunicorn

# اجرای پنل ادمین
gunicorn -w 4 -b 0.0.0.0:5001 admin.app:app

# اجرای ربات (جداگانه)
python run.py --bot
```

### با systemd (لینوکس)

فایل `/etc/systemd/system/yt-downloader.service`:

```ini
[Unit]
Description=YT Downloader Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/yt-downloader-bot
ExecStart=/path/to/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable yt-downloader
sudo systemctl start yt-downloader
```

---

## 🛡️ امنیت

- ✅ رمز عبور هش شده در دیتابیس
- ✅ جلوگیری از SQL Injection
- ✅ محدودیت دانلود روزانه
- ✅ سیستم بن کاربران
- ✅ پنل ادمین جداگانه
- ✅ اعتبارسنجی ورودی‌ها

---

## 🤝 مشارکت

از مشارکت شما استقبال می‌شود!

1. Fork کنید
2. Branch جدید بسازید (`git checkout -b feature/amazing`)
3. Commit کنید (`git commit -m 'Add amazing feature'`)
4. Push کنید (`git push origin feature/amazing`)
5. Pull Request بزنید

---

## 📞 پشتیبانی

- 👨‍💻 **سازنده:** [@KingJFG](https://t.me/KingJFG)
- 📢 **کانال:** [@AnyCodeGP](https://t.me/AnyCodeGP)
- 🐛 **گزارش باگ:** [Issues](https://github.com/AnyCodeGP/yt-downloader-bot/issues)

---

## 📄 مجوز

این پروژه تحت مجوز [MIT](LICENSE) منتشر شده است.

---

<div align="center">

**ساخته شده با ❤️ توسط [@KingJFG](https://t.me/KingJFG)**

**عضو کانال [@AnyCodeGP](https://t.me/AnyCodeGP) شوید!**

</div>

</div>
