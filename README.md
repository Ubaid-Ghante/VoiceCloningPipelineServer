# VoiceCloningPipelineServer

Pipeline of stt and tts models for voice cloning and creating a dubbbed video.

## Table of Contents

- [Overview](#overview)
- [Usage Instructions](#usage-instructions)
- [Improvements and Future Work](#improvements-and-future-work)

## Overview

This repository contains a pipeline that combines speech-to-text (STT) and text-to-speech (TTS) models to facilitate voice cloning and dubbing videos. The pipeline allows users to dub any video in their desired voice. The main components of the pipeline include:

1. Downloading the video from a given URL.
2. Transcribing the audio from the video using a speech-to-text model (whisperx).
3. Generating speech in the desired voice using a text-to-speech model (IndexTTS-2).
4. Merging the generated speech back into the video to create a dubbed version.

<img src="./static/Screenshot 2025-11-02 at 12.20.27 PM.png" alt="Flowchart of the Pipeline" width="50%">

## Usage Instructions

### ⚙️ Environment Setup

1. Install the [uv package manager](https://docs.astral.sh/uv/getting-started/installation/).
   It is _required_ for a reliable, modern installation environment.

> [!TIP] > **Quick & Easy Installation Method:**
>
> There are many convenient ways to install the `uv` command on your computer.
> Please check the link above to see all options. Alternatively, if you want
> a very quick and easy method, you can install it as follows:
>
> ```bash
> pip install -U uv
> ```

> [!WARNING]
> This **only** support the `uv` installation method. Other tools, such as `conda`
> or `pip` will not work. `uv` is [up to 115x faster](https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md)
> than `pip`.

2. Install ffmpeg on your machine from [here](https://www.ffmpeg.org/download.html). We need this to extract audio from video, convert formats, find video lenght, overlay audio and other services in the project. \
   For Linux (Ubuntu/Debian) users, you can install it via the following commands:

```bash
sudo add-apt-repository ppa:savoury1/ffmpeg4
sudo apt-get update
sudo apt-get install ffmpeg
```

3. Install required dependencies: \
   This uses `uv` to manage the project's dependency environment. The following command
   will _automatically_ create a `.venv` project-directory and then installs the correct
   versions of Python and all required dependencies:

```bash
uv sync
```

if you face error related to llvm try to install the following packages in linux:

```bash
sudo apt update
sudo apt install llvm-14 llvm-14-dev llvm-14-tools clang
```

### 🗂️ Download Model

1. Download the required models via [uv tool](https://docs.astral.sh/uv/guides/tools/#installing-tools): \
   Download via `huggingface-cli`:

```bash
uv tool install "huggingface-hub[cli,hf_xet]"

hf download IndexTeam/IndexTTS-2 --local-dir=src/models/indextts/checkpoints
```

### 🚀 Running the Pipeline

> If you are going to use youtube links please make sure to have `cookies.txt` file in the `src/config/` folder for `yt-dlp` to work properly. Add your browser cookies to that file. You can use [this guide](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)

There are two ways to run the pipeline:

1. **Using Streamlit Web App**: \
   Run the Streamlit app to interact with the pipeline via a web interface.

```bash
uv run streamlit run streamlit_app.py
```

Note: Make sure to run this command from the root directory of the project and the output video and audio files will be saved in the `output/` directory. Youtube URL downloading can be a problem if you are behind a proxy or firewall.

2. **Using the main.py Script**: \
   You can also run the pipeline directly using the `main.py` script. Modify the parameters in the script as needed and execute it.

```bash
uv run python main.py
```

Note: You can tweek CHUNK_LENGTH (in [main](./main.py)) if you get missing words or audio overlap is not proper.

## Improvements and Future Work

- Test with GPU for faster processing.
- Add support for more TTS and STT models.
- Detech pauses and do chunking based on that.
- Multiprocessing for faster processing of chunks.
- Lip-syncing the dubbed audio with the video.
