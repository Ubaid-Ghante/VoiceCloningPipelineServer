import os
import yt_dlp
import re

# Helper funtion to generate valid filename from video title
def sanitize_ascii(text: str) -> str:
    return re.sub(r'[^\x00-\x7F]', '', text)

# Main function to download video
async def download_video(url: str,
                   source: str = "youtube",
                   output_dir: str = ".",
                   filename: str = None,
                   best_quality: bool = True) -> None:
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

    if not filename and video_title != sanitize_ascii(video_title):
        sanitized_title = sanitize_ascii(video_title)
        sanitized_path = os.path.join(output_dir, sanitized_title + "." + video_ext)
        os.rename(video_path, sanitized_path)
        video_path = sanitized_path
        video_title = sanitized_title
    
    return {
        "video_path": video_path,
        "title": video_title,
        "ext": video_ext
    }

# Function to delete video file
def delete_video(video_path: str) -> None:
    if os.path.exists(video_path):
        os.remove(video_path)

if __name__ == "__main__":
    import asyncio
    url = "https://youtu.be/UF8uR6Z6KLc?si=2Xydno-OH-QJYbcL"
    output_dir = "./input"

    video_info = asyncio.run(download_video(url, "youtube", output_dir, best_quality=True))
    
    print("Downloaded video info:", video_info)
    
    # Command to test __main__ block
    # uv run python -m src.services.download_video