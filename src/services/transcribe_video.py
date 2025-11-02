import json
import os
import subprocess
import tempfile
from typing import Dict, Optional
import torch
import whisperx

from src.config.logger_config import logger

WHISPERX_MODEL = None
ALIGN_MODEL_EN = None
METADATA_EN = None
DEVICE = "cpu"

def _load_models():
    global WHISPERX_MODEL, ALIGN_MODEL_EN, METADATA_EN, DEVICE
    try:
        DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float32" if DEVICE == "cpu" else "float16"
        logger.info(f"Loading whisperx model on {DEVICE} ...")

        if not os.path.exists("src/models/whisperx"):
            os.makedirs("src/models/whisperx", exist_ok=True)
        
        WHISPERX_MODEL = whisperx.load_model(
            "small",
            device=DEVICE,
            download_root="src/models/whisperx",
            compute_type=compute_type,
        )

        logger.info("Loading alignment model for language en ...")
        ALIGN_MODEL_EN, METADATA_EN = whisperx.load_align_model(
            language_code="en", device=DEVICE
        )
        
        logger.info("Models loaded successfully.")
    except Exception as e:
        WHISPERX_MODEL = None
        ALIGN_MODEL_EN = None
        METADATA_EN = None
        logger.error(f"Model loading failed: {e}")
        raise e

def _extract_audio_to_wav(video_path: str, out_wav: str) -> bool:
    """Extract audio as 16 kHz mono WAV for ASR."""
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            out_wav,
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return os.path.exists(out_wav) and os.path.getsize(out_wav) > 0
    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
        return False

def _whisperx_transcribe(audio_path: str, language: Optional[str]) -> Dict:
    """Uses whisperx to get word-level timestamps if available.
    Args: 
        audio_path: Path to audio file.
        language: Language code (e.g., 'en' for English).
    Returns:
        Transcription result with word-level timestamps.
    """
    global WHISPERX_MODEL, ALIGN_MODEL_EN, METADATA_EN, DEVICE
    # Transcribe
    logger.info("Running initial transcription (whisper) ...")
    audio = whisperx.load_audio(audio_path)
    result = WHISPERX_MODEL.transcribe(audio, language=language)

    # Align
    logger.info("Running alignment to produce word timestamps ...")
    if language and language != "en":
        align_model, metadata = whisperx.load_align_model(
            language_code=language, device=DEVICE
        )
    else:
        align_model, metadata = ALIGN_MODEL_EN, METADATA_EN
    result_aligned = whisperx.align(
        result["segments"], align_model, metadata, audio_path, DEVICE
    )

    words = []
    for seg in result_aligned["segments"]:
        for w in seg.get("words", []):
            words.append(
                {
                    "word": w.get("word"),
                    "start": round(w.get("start", 0.0), 3),
                    "end": round(w.get("end", 0.0), 3),
                }
            )

    final_response = {
        "complete_transcript": " ".join([_.get("text", "") for _ in result["segments"]]),
        "word_level_timestamps": words,
    }

    return final_response

async def transcribe_video(
    video_path: str,
    language: Optional[str] = None,
    tmp_dir: Optional[str] = None,
) -> Dict:
    """
    Create a word-level transcript from a video.
    Args:
        video_path: Path to the video file.
        language: Optional language code for transcription (e.g., 'en' for English).
        tmp_dir: Optional temporary directory for intermediate files.
    Returns:
        A list of {"word": str, "start": float, "end": float} entries with entire transcript.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    tmp_dir = tmp_dir or tempfile.mkdtemp(prefix="transcribe_video_")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir, exist_ok=True)

    
    wav_path = os.path.join(tmp_dir, "extracted_audio.wav")
    logger.info("Extracting audio for ASR...")
    if not _extract_audio_to_wav(video_path, wav_path):
        raise RuntimeError("Failed to extract audio for transcription.")
    
    try:
        logger.info("Attempting whisperx transcription ...")
        return _whisperx_transcribe(wav_path, language)
    except Exception as e_whx:
        logger.info(f"whisperx failed or not available: {e_whx}")


if __name__ == "__main__":
    import asyncio
    video = "input/Steve Jobs' 2005 Stanford Commencement Address.mp4"
    lang = "en"
    _load_models()
    words = asyncio.run(transcribe_video(video, language=lang, tmp_dir="./output"))
    print(json.dumps(words, indent=2))

    # Command to test __main__ block
    # uv run python -m src.services.transcribe_video
