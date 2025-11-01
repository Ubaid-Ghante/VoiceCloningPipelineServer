import os
import yt_dlp
import re
import json

from src.config.logger_config import logger

def _sanitize_ascii(text: str) -> str:
    """Remove non-ascii characters from text.
    Args:
        text (str): Input text.
    Returns:
        str: Sanitized text with only ascii characters.
    """
    return re.sub(r'[^\x00-\x7F]', '', text)

async def download_video(url: str,
                   source: str = "youtube",
                   output_dir: str = ".",
                   filename: str = None,
                   best_quality: bool = True) -> dict:
    """Download video from given URL using yt-dlp.
    Args:
        url: URL of the video to download.
        source: Source platform of the video (default: "youtube").
        output_dir: Directory to save the downloaded video (default: current directory).
        filename: Desired filename for the downloaded video (default: None, uses video title).
        best_quality: Whether to download the best quality video (default: True).
    Returns:
        dict: Information about the downloaded video including path, title, and extension.
    """
    
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestvideo+bestaudio/best" if best_quality else "best",
        "merge_output_format": "mp4",
        "cookiefile": "src/config/cookies.txt",
    }

    if filename:
        ydl_opts["outtmpl"] = os.path.join(output_dir, filename + ".%(ext)s")
    else:
        ydl_opts["outtmpl"] = os.path.join(output_dir, "%(title)s.%(ext)s")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    info_dict = ydl.extract_info(url, download=False)
    video_title = info_dict.get('title', None)
    video_ext = info_dict.get('ext', 'mp4')
    video_filename = filename + "." + video_ext if filename else video_title + "." + video_ext
    video_path = os.path.join(output_dir, video_filename)

    if not filename and video_title != _sanitize_ascii(video_title):
        sanitized_title = _sanitize_ascii(video_title)
        sanitized_path = os.path.join(output_dir, sanitized_title + "." + video_ext)
        os.rename(video_path, sanitized_path)
        video_path = sanitized_path
        video_title = sanitized_title
    
    return {
        "video_path": video_path,
        "title": video_title,
        "ext": video_ext
    }

def delete_video(video_path: str) -> bool:
    """Delete the video file at the specified path.
    Args:
        video_path: Path to the video file to delete.
    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    try: 
        if os.path.exists(video_path):
            os.remove(video_path)
            return True
        else:
            logger.warning(f"Video file {video_path} does not exist.")
            return False
    except Exception as e:
        logger.error(f"Error deleting video file {video_path}: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    url = "https://youtu.be/UF8uR6Z6KLc?si=2Xydno-OH-QJYbcL"
    output_dir = "./input"

    video_info = asyncio.run(download_video(url, "youtube", output_dir, best_quality=True))

    logger.info(f"Downloaded video info: {json.dumps(video_info, indent=4)}")
    
    # Command to test __main__ block
    # uv run python -m src.services.download_video