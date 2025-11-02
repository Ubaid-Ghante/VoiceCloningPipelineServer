import json
import shutil
import os
import subprocess
import uuid

from src.services.download_video import download_video
from src.services.transcribe_video import transcribe_video, _load_models
from src.services.generate_audio import generate_audio, _load_tts_model
from src.services.overlay_audio_on_video import overlay_audio_on_video, _chunk_transcript

from src.config.logger_config import logger

logger.info("Loading WhisperX Model...")
_load_models()
logger.info("WhisperX Loaded Successfully.")

logger.info("Loading IndexTTS Model...")
_load_tts_model()
logger.info("IndexTTS Loaded Successfully.")


CHUNK_LENGTH=10

async def main_pipeline(youtube_url="", sample_file="", video_file=""):
    video_details = {}
    run_id = str(uuid.uuid4())
    if video_file:
        video_details["video_path"] = video_file
        source_video_path = video_file
    else:
        try:
            logger.debug(f"Downloading video from YouTube URL: {youtube_url}")
            video_details = await download_video(url = youtube_url, source="youtube", output_dir="input")
            source_video_path = video_details.get("video_path", None)
        except:
            raise Exception("Failed to download video")

    try:
        logger.debug(f"Transcribing video: {source_video_path}")
        transcription = await transcribe_video(video_path=source_video_path)
        with open(f"output/{run_id}_transcript.json", "w", encoding='utf-8') as fh:
            json.dump(transcription, fh, ensure_ascii=False, indent=4)

        word_level_timestamps = transcription.get("word_level_timestamps", None)
    except:
        raise Exception("Failed to transcribe the audio.")

    
    try:
        logger.debug("Generating audio chunks...")
        if sample_file.endswith(".mp3"):
            wav_file_path = sample_file[:-4]+".wav"
            subprocess.call(['ffmpeg', '-i', sample_file, wav_file_path])
            sample_file = wav_file_path
        clips = _chunk_transcript(word_level_timestamps, default_sample=sample_file, chunk_size_seconds=CHUNK_LENGTH)
        os.makedirs(f"output/audio_chunks/{run_id}", exist_ok=True)
        for i, clip in enumerate(clips):
            await generate_audio(text=clip.text, output_filepath=f"output/audio_chunks/{run_id}/chunk{i}.wav", sample_filepath=clip.sample_to_use, video_sec=clip.end - clip.start)
    except:
        raise Exception("Failed to Audio Generation")

    try:
        logger.info("Overlaying generated audio on video...")
        overlay_audio_on_video(
            video_path=source_video_path,
            chunk_audio_dir=f"output/audio_chunks/{run_id}",
            output_video_path=f"output/{run_id}_final_dubbed_video.mp4",
            clips=clips
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
        shutil.rmtree(f"output/audio_chunks/{run_id}", ignore_errors=True)

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
    asyncio.run(main_pipeline(video_file="./input/MiniCropSteve Jobs' 2005 Stanford Commencement Address.mp4", sample_file="./input/VoiceSample1.mp3"))
    
    # uv run python main.py
    