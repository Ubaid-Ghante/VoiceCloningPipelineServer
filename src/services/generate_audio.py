import numpy as np
if not hasattr(np, "bool8"):
    np.bool8 = np.bool_

from indextts.infer_v2 import IndexTTS2

def generate_audio():
    tts = IndexTTS2(cfg_path="src/models/indextts/checkpoints/config.yaml", model_dir="src/models/indextts/checkpoints", use_fp16=False, use_cuda_kernel=False, use_deepspeed=False)
    text = "Hi there, this is a test for voice cloning."
    tts.infer(spk_audio_prompt='input/voice_12.wav', text=text, output_path="output/gen.wav", verbose=True)

if __name__ == "__main__":
    generate_audio()

    # uv run python -m src.services.generate_audio