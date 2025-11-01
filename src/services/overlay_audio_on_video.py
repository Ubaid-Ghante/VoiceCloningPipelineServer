import os
import subprocess
import librosa
import soundfile as sf
from typing import List

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


def overlay_audio_on_video(video_path: str, chunk_audio_dir: str, output_video_path: str) -> str:
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

    print(f"Merging {len(chunk_files)} audio chunks...")
    _merge_audio_chunks(chunk_files, merged_audio_path)

    print("Overlaying dubbed audio onto video...")
    _mux_video_with_audio(video_path, merged_audio_path, output_video_path)

    print(f"Final dubbed video saved at: {output_video_path}")
    return output_video_path


if __name__ == "__main__":
    # Example standalone test
    video = "input/Steve Jobs' 2005 Stanford Commencement Address.mp4"
    chunks_dir = "output"
    output = "output/final_dubbed_video.mp4"

    overlay_audio_on_video(video_path=video, chunk_audio_dir=chunks_dir, output_video_path=output)

    # Run via: uv run python -m src.services.overlay_audio_on_video
