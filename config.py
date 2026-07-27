
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "bot.db")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

ADMIN_DEFAULT_PASSWORD = "admin1234"
ADMIN_SECRET_KEY = os.urandom(32).hex()

DEFAULT_DAILY_LIMIT = 10
MAX_FILE_SIZE_MB = 2000

QUALITIES = {
    "1080": "1080p (Full HD)",
    "720": "720p (HD)",
    "480": "480p (SD)",
}
