# --------- Imports & Global Setup ---------
import os
import openai
import streamlit as st
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
import zipfile

openai.api_key = st.secrets["OPENAI_API_KEY"]


# --------- Utility Functions (Modules) ---------
def ask_chatgpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']


def get_surah_assets(surah_name):
    prompt = f"""
You are a YouTube Islamic video assistant. For the surah '{surah_name}', generate the following:
1. Cinematic background prompt for DALL·E
2. A .srt subtitle file for text overlays — Arabic + English with timings
3. YouTube video title
4. Description
5. Tags (comma separated)

Respond with clear sections: [BACKGROUND], [SRT], [TITLE], [DESCRIPTION], [TAGS]
"""
    return ask_chatgpt(prompt)


def save_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


def make_subtitles_clip(subtitles_path, font_path='DejaVu-Sans'):
    generator = lambda txt: TextClip(txt, font=font_path, fontsize=42, color='white')
    return SubtitlesClip(subtitles_path, generator)


def generate_quran_video(audio_path, bg_image_path, subtitles_path, output_path):
    audio = AudioFileClip(audio_path)
    bg = ImageClip(bg_image_path).set_duration(audio.duration).resize((1280, 720))
    subs = make_subtitles_clip(subtitles_path)
    video = CompositeVideoClip([
        bg,
        subs.set_position(('center', 'bottom'))
    ]).set_audio(audio)
    video.write_videofile(output_path, fps=24)


def export_assets_zip():
    with zipfile.ZipFile("LightofQuran_Assets.zip", 'w') as zipf:
        for asset_file in ["generated_subtitles.srt", "title.txt", "description.txt", "tags.txt", "background_prompt.txt"]:
            if os.path.exists(asset_file):
                zipf.write(asset_file)


# --------- Streamlit App UI ---------
def run_streamlit_ui():
    st.title("🕌 Test Load – LightofQuran Agent Working")
    st.write("Auto-generate cinematic Qur’an recitation videos with text overlays.")

    surah_name = st.text_input("Enter Surah Name (e.g., Al-Adiyat)")
    if st.button("🔍 Generate Surah Assets"):
        assets = get_surah_assets(surah_name)
        st.session_state['assets'] = assets

        for section in ["[BACKGROUND]", "[SRT]", "[TITLE]", "[DESCRIPTION]", "[TAGS]"]:
            if section in assets:
                st.subheader(section.replace('[', '').replace(']', ''))
                content = assets.split(section)[1].split("[")[0].strip()
                st.text_area(f"{section}", value=content, height=200)

                if section == "[SRT]":
                    save_file("generated_subtitles.srt", content)
                elif section == "[BACKGROUND]":
                    save_file("background_prompt.txt", content)
                elif section == "[TITLE]":
                    save_file("title.txt", content)
                elif section == "[DESCRIPTION]":
                    save_file("description.txt", content)
                elif section == "[TAGS]":
                    save_file("tags.txt", content)

    if st.button("📦 Download All Metadata & Subtitles"):
        export_assets_zip()
        with open("LightofQuran_Assets.zip", "rb") as f:
            st.download_button("⬇️ Download ZIP", f, file_name="LightofQuran_Assets.zip")

    audio_file = st.file_uploader("Upload Recitation Audio (mp3)", type=["mp3"])
    bg_file = st.file_uploader("Upload Background Image (jpg/png)", type=["jpg", "png"])
    subtitles_file = st.file_uploader("Upload Subtitles (.srt) or use generated", type=["srt"])

    if audio_file and bg_file and (subtitles_file or os.path.exists("generated_subtitles.srt")):
        if st.button("🎬 Generate Video"):
            audio_path = "recitation.mp3"
            bg_path = "background.jpg"
            subs_path = "subtitles.srt" if subtitles_file else "generated_subtitles.srt"
            output_path = "final_surah_video.mp4"

            with open(audio_path, "wb") as f: f.write(audio_file.read())
            with open(bg_path, "wb") as f: f.write(bg_file.read())
            if subtitles_file:
                with open(subs_path, "wb") as f: f.write(subtitles_file.read())

            generate_quran_video(audio_path, bg_path, subs_path, output_path)
            st.success("✅ Video Generated Successfully!")
            st.video(output_path)


# --------- Streamlit Entry Point ---------
if __name__ == "__main__":
    run_streamlit_ui()


