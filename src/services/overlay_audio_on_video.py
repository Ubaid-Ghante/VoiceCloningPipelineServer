import json
import os
import subprocess
import librosa
import soundfile as sf
from typing import List
import numpy as np

from pydantic import BaseModel
from typing import List

from src.config.logger_config import logger


class ClipPart(BaseModel):
    text: str = ""
    start: float = 0.0
    end: float = 0.0
    audio_file_path: str = ""
    sample_to_use: str = ""

def _chunk_transcript(word_timestamps, default_sample, chunk_size_seconds=30) -> List[ClipPart]:
    chunks = []

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
        chunk_text = " ".join([_["word"] for _ in chunk_words])
        chunk_text.replace(" ,", ",")
        chunks.append(ClipPart(
            text=chunk_text,
            start=chunk_words[0]['start'],
            end=chunk_words[-1]['end'],
            audio_file_path="",
            sample_to_use=default_sample
        ))
        
        # Move the window forward
        current_time += chunk_size_seconds

    return chunks


def _get_video_duration(video_path: str) -> float:
    import subprocess, json
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of", "json", video_path],
        capture_output=True, text=True
    )
    return float(json.loads(result.stdout)["format"]["duration"])

def _merge_audio_chunks_with_timing(clips, output_path: str, sr: int = 44100, total_video_dur: float | None = None):
    """
    Merge audio chunks according to their start and end timestamps,
    adding silence where needed to match the video timeline.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_audio = np.zeros(0, dtype=np.float32)
    current_time = 0.0

    for clip in clips:
        if not os.path.exists(clip.audio_file_path):
            raise FileNotFoundError(f"Missing chunk: {clip.audio_file_path}")
        
        # Add silence for gap before this clip
        if clip.start > current_time:
            gap_dur = clip.start - current_time
            silence = np.zeros(int(gap_dur * sr), dtype=np.float32)
            final_audio = np.concatenate([final_audio, silence])
            current_time += gap_dur

        # Load the chunk
        y, sr_ = librosa.load(clip.audio_file_path, sr=sr)
        final_audio = np.concatenate([final_audio, y])
        current_time += clip.end - clip.start

    # If total video duration is known, pad silence till the end
    if total_video_dur and total_video_dur > current_time:
        pad_dur = total_video_dur - current_time
        silence = np.zeros(int(pad_dur * sr), dtype=np.float32)
        final_audio = np.concatenate([final_audio, silence])

    sf.write(output_path, final_audio, sr)
    return output_path

def _merge_audio_chunks(chunk_paths: List[str], output_path: str) -> str:
    """
    Merge multiple audio clips into one continuous WAV file.
    """
    if not chunk_paths:
        raise ValueError("No audio chunks provided for merging.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged_audio = []
    sr = None

    for path in chunk_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Chunk file missing: {path}")

        y, sr_ = librosa.load(path, sr=None)
        if sr is None:
            sr = sr_
        elif sr != sr_:
            y = librosa.resample(y, orig_sr=sr_, target_sr=sr)
        merged_audio.append(y)

    final_audio = librosa.util.fix_length(
        librosa.util.flatten(merged_audio),
        sum(len(a) for a in merged_audio)
    )

    sf.write(output_path, final_audio, sr)
    return output_path

def _mux_video_with_audio(video_path: str, audio_path: str, output_path: str):
    """
    Combine the dubbed audio with the original video, replacing its original track.
    Keeps video as-is (copy codec), replaces audio.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",          # keep video as is
        "-map", "0:v:0",         # take video from input 0
        "-map", "1:a:0",         # take audio from input 1
        "-shortest",             # end when shortest stream ends
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def overlay_audio_on_video(video_path: str, chunk_audio_dir: str, output_video_path: str, clips: List[ClipPart]) -> str:
    """
    Merge all audio chunks and overlay the combined dubbed audio over the source video.

    Args:
        video_path: Path to the source/original video.
        chunk_audio_dir: Directory containing chunk{i}.wav audio files.
        output_video_path: Path to save the final dubbed video.

    Returns:
        Path to the final dubbed video.
    """
    # Gather and sort audio chunks
    chunk_files = sorted(
        [os.path.join(chunk_audio_dir, f) for f in os.listdir(chunk_audio_dir) if f.endswith(".wav")],
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0].replace("chunk", "")),
    )

    if not chunk_files:
        raise FileNotFoundError("No chunk audio files found in directory.")

    merged_audio_path = os.path.join(chunk_audio_dir, "merged_dub.wav")

    logger.debug(f"Merging {len(chunk_files)} audio chunks...")  # or use ffprobe inline
    video_dur = _get_video_duration(video_path)

    for i, clip in enumerate(clips):
        clip.audio_file_path = os.path.join(chunk_audio_dir, f"chunk{i}.wav")

    _merge_audio_chunks_with_timing(clips, merged_audio_path, total_video_dur=video_dur)
    # _merge_audio_chunks(chunk_files, merged_audio_path)

    logger.debug("Overlaying dubbed audio onto video...")
    _mux_video_with_audio(video_path, merged_audio_path, output_video_path)

    logger.debug(f"Final dubbed video saved at: {output_video_path}")
    return output_video_path


if __name__ == "__main__":
    # Example standalone test
    video = "input/MiniCropSteve Jobs' 2005 Stanford Commencement Address.mp4"
    chunks_dir = "output/audio_chunks/2dbc4f20-eebc-4c88-8465-19b7da61eef4"
    output = "output/final_dubbed_video.mp4"
    with open("output/2dbc4f20-eebc-4c88-8465-19b7da61eef4_transcript.json", "r") as fh:
        data = json.load(fh)
    clips = _chunk_transcript(data["word_level_timestamps"], default_sample="input/VoiceSample1.wav", chunk_size_seconds=10)
    overlay_audio_on_video(video_path=video, chunk_audio_dir=chunks_dir, output_video_path=output, clips=clips)

    # Run via: uv run python -m src.services.overlay_audio_on_video
