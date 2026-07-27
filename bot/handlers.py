
import os
import sys
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from database import (
    init_db, register_user, can_user_download, increment_download,
    get_setting, get_user
)
from bot.downloader import get_video_info, download_video, is_youtube_url, extract_youtube_id

logger = logging.getLogger(__name__)

pending_downloads = {}


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username, user.full_name)
    
    welcome = f"""🎬 **سلام {user.first_name}!**

به ربات دانلود ویدیو یوتیوب خوش آمدید!

**نحوه استفاده:**
1️⃣ لینک ویدیوی یوتیوب را بفرستید
2️⃣ کیفیت مورد نظر را انتخاب کنید
3️⃣ ویدیو برای شما دانلود و ارسال می‌شود! 🚀

**کیفیت‌های موجود:**
• 480p (SD)
• 720p (HD)
• 1080p (Full HD)

📝 لینک یوتیوب رو بفرستید تا شروع کنیم!"""
    
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📖 **راهنمای ربات**

🔹 لینک ویدیوی یوتیوب را بفرستید
🔹 کیفیت دلخواه را انتخاب کنید
🔹 ویدیو دانلود و ارسال می‌شود

⚡ **کیفیت‌ها:**
• 480p - مناسب اینترنت کم
• 720p - کیفیت استاندارد
• 1080p - بالاترین کیفیت

📊 **دستورات:**
/start - شروع
/help - راهنما
/status - وضعیت اشتراک

👨‍💻 **سازنده:** @KingJFG
📢 **کانال:** @AnyCodeGP"""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ شما هنوز ثبت‌نام نکرده‌اید. /start را بزنید.")
        return
    
    if user["is_banned"]:
        await update.message.reply_text("🚫 شما بن شده‌اید و امکان دانلود ندارید.")
        return
    
    remaining = max(0, user["daily_limit"] - user["daily_downloads"])
    status_text = f"""📊 **وضعیت شما:**

📥 دانلود امروز: {user['daily_downloads']} / {user['daily_limit']}
📈 کل دانلودها: {user['total_downloads']}
✅ باقی‌مانده امروز: {remaining}

💡 محدودیت روزانه شما {user['daily_limit']} دانلود است."""
    
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    
    text = message.text.strip()
    user = update.effective_user
    
    register_user(user.id, user.username, user.full_name)
    
    if not is_youtube_url(text):
        await message.reply_text(
            "🔗 لطفاً یک لینک معتبر یوتیوب بفرستید.\n\n"
            "مثال: `https://www.youtube.com/watch?v=xxxxx`\n"
            "یا: `https://youtu.be/xxxxx`",
            parse_mode="Markdown"
        )
        return
    
    can_dl, reason = can_user_download(user.id)
    if not can_dl:
        if reason == "banned":
            await message.reply_text("🚫 شما بن شده‌اید و امکان دانلود ندارید.")
        elif reason == "limit_reached":
            await message.reply_text(
                "⏳ به محدودیت دانلود روزانه رسیده‌اید.\n"
                "فردا دوباره تلاش کنید یا با ادمین تماس بگیرید."
            )
        return
    
    status_msg = await message.reply_text("🔍 در حال دریافت اطلاعات ویدیو...")
    
    video_info = get_video_info(text)
    if not video_info:
        await status_msg.edit_text(
            "❌ نتونستم اطلاعات ویدیو رو بگیرم.\n"
            "لطفاً مطمئن شوید لینک صحیح است و ویدیو خصوصی نباشد."
        )
        return
    
    pending_downloads[user.id] = {
        "url": video_info["webpage_url"],
        "title": video_info["title"],
        "thumbnail": video_info.get("thumbnail", ""),
        "duration": video_info.get("duration", 0),
    }
    
    duration = video_info.get("duration", 0)
    if duration:
        mins, secs = divmod(int(duration), 60)
        dur_str = f"{mins}:{secs:02d}"
    else:
        dur_str = "نامشخص"
    
    title = video_info["title"][:80]
    info_text = f"""🎬 **{title}**

👤 سازنده: {video_info.get('uploader', 'نامشخص')}
⏱️ مدت: {dur_str}

یک کیفیت انتخاب کنید:"""
    
    keyboard = [
        [
            InlineKeyboardButton("📱 480p (SD)", callback_data="dl_480"),
            InlineKeyboardButton("💻 720p (HD)", callback_data="dl_720"),
        ],
        [
            InlineKeyboardButton("🖥️ 1080p (Full HD)", callback_data="dl_1080"),
        ],
        [
            InlineKeyboardButton("❌ لغو", callback_data="dl_cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if video_info.get("thumbnail"):
        try:
            await status_msg.delete()
            await message.reply_photo(
                photo=video_info["thumbnail"],
                caption=info_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception:
            await status_msg.edit_text(info_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await status_msg.edit_text(info_text, parse_mode="Markdown", reply_markup=reply_markup)


async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    await query.answer()
    
    if data == "dl_cancel":
        pending_downloads.pop(user_id, None)
        await query.edit_message_text("❌ دانلود لغو شد.")
        return
    
    if not data.startswith("dl_"):
        return
    
    quality = data.replace("dl_", "")
    
    if user_id not in pending_downloads:
        await query.edit_message_text("⚠️ لطفاً ابتدا لینک ویدیو را بفرستید.")
        return
    
    can_dl, reason = can_user_download(user_id)
    if not can_dl:
        pending_downloads.pop(user_id, None)
        if reason == "banned":
            await query.edit_message_text("🚫 شما بن شده‌اید.")
        elif reason == "limit_reached":
            await query.edit_message_text("⏳ به محدودیت دانلود روزانه رسیده‌اید.")
        return
    
    video_data = pending_downloads[user_id]
    url = video_data["url"]
    title = video_data["title"]
    
    quality_names = {"480": "480p (SD)", "720": "720p (HD)", "1080": "1080p (Full HD)"}
    await query.edit_message_text(
        f"⏳ **در حال دانلود...**\n\n"
        f"🎬 {title[:50]}\n"
        f"📐 کیفیت: {quality_names.get(quality, quality)}\n\n"
        f"لطفاً صبر کنید...",
        parse_mode="Markdown"
    )
    
    try:
        filepath = download_video(url, quality)
        
        if filepath and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > 50:
                pending_downloads.pop(user_id, None)
                await query.edit_message_text(
                    f"❌ حجم ویدیو بیشتر از 50 مگابایت است ({file_size_mb:.1f} MB).\n"
                    f"کیفیت پایین‌تر را انتخاب کنید."
                )
                return
            
            await query.edit_message_text("📤 در حال ارسال ویدیو...")
            
            with open(filepath, "rb") as video_file:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video_file,
                    caption=f"🎬 {title[:100]}\n📐 کیفیت: {quality_names.get(quality, quality)}\n\n👨‍💻 سازنده: @KingJFG\n📢 کانال: @AnyCodeGP",
                    read_timeout=120,
                    write_timeout=120,
                )
            
            increment_download(user_id, url, title, quality, file_size)
            
            try:
                os.remove(filepath)
            except OSError:
                pass
            
            await query.edit_message_text(
                f"✅ **دانلود موفق!**\n\n"
                f"🎬 {title[:50]}\n"
                f"📐 کیفیت: {quality_names.get(quality, quality)}\n"
                f"📦 حجم: {file_size_mb:.1f} MB",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ خطا در دانلود ویدیو.\n"
                "لطفاً دوباره تلاش کنید."
            )
    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.edit_message_text(
            f"❌ خطا در دانلود: {str(e)[:100]}\n"
            "لطفاً دوباره تلاش کنید."
        )
    
    pending_downloads.pop(user_id, None)


async def post_init(application: Application):
    commands = [
        BotCommand("start", "شروع و خوش‌آمدگویی"),
        BotCommand("help", "راهنمای استفاده"),
        BotCommand("status", "وضعیت دانلود"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set successfully!")


def run_bot(token: str):
    init_db()
    
    application = Application.builder().token(token).post_init(post_init).build()
    
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CallbackQueryHandler(quality_callback, pattern=r"^dl_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot is running...")
    application.run_polling(drop_pending_updates=True)
