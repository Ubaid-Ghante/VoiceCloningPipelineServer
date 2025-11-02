import streamlit as st
import asyncio
import os

from main import main_pipeline

st.set_page_config(page_title="Video Voice Cloning Pipeline", layout="centered")

st.title("🎬 Video Voice Cloning Pipeline Tester")

st.markdown("""
Upload a **video** or provide a **YouTube URL**, along with a **voice sample**.
""")

# Input options
st.subheader("Step 1: Provide Inputs")

use_youtube = st.checkbox("Use YouTube URL instead of uploading a video", value=False)

youtube_url = ""
video_file = None

if use_youtube:
    youtube_url = st.text_input("🎥 YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
else:
    video_file = st.file_uploader("📁 Upload video file", type=["mp4", "mov", "mkv"])

sample_file = st.file_uploader("🎙️ Upload voice sample", type=["mp3", "wav"])

if st.button("🚀 Start Voice Cloning Pipeline", type="primary"):
    if not sample_file:
        st.error("Please upload a voice sample before starting.")
    elif not (youtube_url or video_file):
        st.error("Please provide either a YouTube URL or upload a video.")
    else:
        # Save uploaded files locally
        os.makedirs("input", exist_ok=True)

        video_path = ""
        sample_path = ""

        if video_file:
            video_path = os.path.join("input", video_file.name)
            with open(video_path, "wb") as f:
                f.write(video_file.read())

        if sample_file:
            sample_path = os.path.join("input", sample_file.name)
            with open(sample_path, "wb") as f:
                f.write(sample_file.read())

        st.info("⚙️ Generation process has started — please wait a few minutes.")
        st.info("You can check the `output/` folder for the final dubbed video shortly.")

        # Run the async pipeline in background
        async def run_pipeline():
            try:
                pass
                await main_pipeline(
                    youtube_url=youtube_url,
                    sample_file=sample_path,
                    video_file=video_path
                )
            except Exception as e:
                st.error(f"Pipeline failed: {e}")

        # Starts background event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(run_pipeline())

        st.success("🎉 Process initiated successfully!")


