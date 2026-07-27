
import os
import re
import subprocess
import json
from config import DOWNLOAD_DIR


def get_video_info(url):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    try:
        result = subprocess.run(
            ["yt-dlp", "--no-download", "--print-json", "--no-playlist", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        info = json.loads(result.stdout)
        return {
            "id": info.get("id"),
            "title": info.get("title", "ویدیوی بدون عنوان"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "uploader": info.get("uploader", ""),
            "webpage_url": info.get("webpage_url", url),
            "formats": info.get("formats", []),
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None


def is_youtube_url(url):
    patterns = [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(?:https?://)?(?:www\.)?youtu\.be/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+",
        r"(?:https?://)?m\.youtube\.com/watch\?v=[\w-]+",
    ]
    return any(re.match(p, url) for p in patterns)


def download_video(url, quality="720", message_callback=None):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    quality_map = {
        "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
        "720": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
        "480": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
    }
    
    fmt = quality_map.get(quality, quality_map["720"])
    
    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "-f", fmt,
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--no-playlist",
        "--no-overwrites",
        "--print-json",
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            print(f"yt-dlp error: {result.stderr}")
            return None
        
        info = json.loads(result.stdout)
        video_id = info.get("id", "")
        ext = info.get("ext", "mp4")
        filepath = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")
        
        if os.path.exists(filepath):
            return filepath
        
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(video_id):
                return os.path.join(DOWNLOAD_DIR, f)
        
        return None
        
    except subprocess.TimeoutExpired:
        print("Download timed out!")
        return None
    except Exception as e:
        print(f"Download error: {e}")
        return None


def extract_youtube_id(url):
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([\w-]{11})",
        r"(?:shorts/)([\w-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None
