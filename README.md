# VoiceCloningPipelineServer

Pipeline of stt and tts models for voice cloning.

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
> or `pip` . `uv` is [up to 115x faster](https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md)
> than `pip`.

2. Install ffmpeg on your machine from [here](https://www.ffmpeg.org/download.html). We need this to extract audio from video and other services in the project. \
For Linux
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
if you face error related to llvm try to install the following packages
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
