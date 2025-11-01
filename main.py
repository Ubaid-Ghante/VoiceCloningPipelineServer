from pydantic import BaseModel
from typing import List
import json
import shutil
import os
import subprocess
from src.services.download_video import download_video
from src.services.transcribe_video import transcribe_video
from src.services.generate_audio import generate_audio
from src.services.overlay_audio_on_video import overlay_audio_on_video

from src.config.logger_config import logger

class ClipPart(BaseModel):
    text: str = ""
    start: float = 0.0
    end: float = 0.0
    audio_file_path: str = ""
    sample_to_use: str = ""


def _chunk_transcript(word_timestamps, default_sample) -> List[ClipPart]:
    chunks = []
    chunk_size_seconds = 60

    current_time = 0
    while current_time < word_timestamps[-1]['end']:
        # Find the words that fall within the current chunk window
        chunk_words = [
            word for word in word_timestamps 
            if word['start'] >= current_time and word['end'] <= current_time + chunk_size_seconds
        ]
        
        if not chunk_words:
            # Move to the next potential start time if no words are in this chunk
            current_time += chunk_size_seconds
            continue

        # Create a string representation of the chunk
        chunk_text = " ".join(chunk_words)
        chunks.append(ClipPart(
            chunk_text,
            chunk_words[0]['start'],
            chunk_words[-1]['end'],
            "",
            default_sample
        ))
        
        # Move the window forward
        current_time += chunk_size_seconds

    return chunks

async def main_pipeline(youtube_url, sample_file):
    video_details = {}
    try:
        video_details = await download_video(url = youtube_url, source="youtube", output_dir="input")
        source_video_path = video_details.get("video_path", None)
    except:
        raise Exception("Failed to download video")

    try:
        transcription = await transcribe_video(video_path=source_video_path)
        with open("output/transcript.json", "w", encoding='utf-8') as fh:
            json.dump(transcription, fh, ensure_ascii=False, indent=4)

        word_level_timestamps = transcription.get("word_level_timestamps", None)
    except:
        raise Exception("Failed to transcribe the audio.")

    
    try:
        if sample_file.endswith(".mp3"):
            wav_file_path = sample_file[:-4]+".wav"
            subprocess.call(['ffmpeg', '-i', sample_file, wav_file_path])
            sample_file = wav_file_path
        clips = _chunk_transcript(word_level_timestamps, default_sample=sample_file)
        for i, clip in enumerate(clips):
            await generate_audio(text=clip.text, output_filepath=f"output/audio_chunks/chunk{i}.wav", sample_filepath=clip.sample_to_use, video_sec=clip.end - clip.start)
    except:
        raise Exception("Failed to Audio Generation")

    try:
        overlay_audio_on_video(
            video_path=source_video_path,
            chunk_audio_dir="output/audio_chunks",
            output_video_path="output/final_dubbed_video.mp4"
        )
    except Exception as e:
        raise Exception(f"Failed to overlay audio on video: {e}")

    # Cleanup
    try:
        # 1. Remove temporary transcription audio directory if exists
        tmp_dirs = [d for d in os.listdir(".") if d.startswith("transcribe_video_")]
        for tmp_dir in tmp_dirs:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        # 2. Delete the downloaded source video (optional)
        # if source_video_path and os.path.exists(source_video_path):
        #     os.remove(source_video_path)

        # 3. Remove individual chunk audios (keep merged + final video)
        for f in os.listdir("output/audio_chunks"):
            os.remove(os.path.join("output/audio_chunks", f))

        # 4. Remove temporary stretch directory (if created by generate_audio)
        stretch_tmp = "_temp_dub_segments_for_stretch"
        if os.path.exists(stretch_tmp):
            shutil.rmtree(stretch_tmp, ignore_errors=True)

        # 5. Delete transcript json
        # os.remove("output/transcript.json")

        logger.info("Cleanup completed successfully.")

    except Exception as cleanup_err:
        logger.error(f"Cleanup encountered an error: {cleanup_err}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_pipeline("https://youtu.be/UF8uR6Z6KLc?si=2Xydno-OH-QJYbcL", "input/VoiceSample1.mp3"))
    