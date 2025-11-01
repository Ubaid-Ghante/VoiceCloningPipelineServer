import numpy as np
if not hasattr(np, "bool8"):
    np.bool8 = np.bool_

import subprocess
import librosa
import os
from indextts.infer_v2 import IndexTTS2

async def generate_audio(text: str, output_filepath: str, sample_filepath: str, video_sec: float=None):
    """Generate audio using IndexTTS with a speaker audio prompt. Optionally stretch to match video duration.
    Args:
        text: Text to be synthesized.
        output_filepath: Path to save the generated audio.
        sample_filepath: Path to speaker audio prompt file.
        video_sec: Optional target duration in seconds to stretch the audio to match.
    Returns:
        Creates the audio file at output_filepath.
    """

    tts = IndexTTS2(cfg_path="src/models/indextts/checkpoints/config.yaml", model_dir="src/models/indextts/checkpoints", use_fp16=False, use_cuda_kernel=False, use_deepspeed=False)

    tts.infer(spk_audio_prompt=sample_filepath, text=text, output_path=output_filepath, verbose=True)
    if video_sec:
        # measure actual vs target
        y, sr = librosa.load(output_filepath, sr=None)
        actual_duration_s = librosa.get_duration(y=y, sr=sr)

        if actual_duration_s > 0.1 and abs(actual_duration_s - video_sec) > 0.05:
            stretch_rate = actual_duration_s / video_sec

            temp_dir = "_temp_dub_segments_for_stretch"
            if 0.5 <= stretch_rate <= 2.0:
                stretched_dub_path =  os.path.join(temp_dir, "stretched_dub.wav")
                os.makedirs(temp_dir, exist_ok=True)

                cmd = [
                    "ffmpeg", "-y", "-i", str(output_filepath),
                    "-filter:a", f"atempo={stretch_rate}",
                    str(stretched_dub_path)
                ]
                subprocess.run(cmd, check=True, capture_output=True)

                
                os.replace(stretched_dub_path, output_filepath)

if __name__ == "__main__":
    import asyncio

    asyncio.run(generate_audio("Hi there, this is a test for voice cloning.", "output/gen.wav", "input/voice_12.wav"))

    # uv run python -m src.services.generate_audio