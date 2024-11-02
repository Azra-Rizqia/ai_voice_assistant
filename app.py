import re
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
from gtts import gTTS
import os
from dotenv import load_dotenv
import requests

# Memuat variabel lingkungan dari file .env
load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.error("Audio tidak jelas, coba lagi.")
        return ""
    except sr.RequestError:
        st.error("Gagal menghubungi layanan Speech Recognition.")
        return ""

def text_to_audio(text, audio_path):
    tts = gTTS(text=text, lang='en')
    tts.save(audio_path)
    
def search_on_serp_api(query, retries=3):
    url = f"https://serpapi.com/search.json?api_key={SERP_API_KEY}&q={query}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "organic_results" in data and len(data["organic_results"]) > 0:
                # Gabungkan semua snippet
                snippets = [result.get("snippet", "") for result in data["organic_results"]]
                full_response = " ".join(snippets)
                return full_response.strip()

            return "Tidak ada hasil yang ditemukan."
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")
            return "Terjadi kesalahan saat memproses pencarian."

    return "Gagal mengambil data setelah beberapa percobaan."

def summarize_text(text, max_sentences=3):
    """Merangkum teks menjadi beberapa kalimat terpenting."""
    sentences = re.split(r'(?<=[.!?]) +', text)  # Pisahkan kalimat
    summary = " ".join(sentences[:max_sentences])  # Ambil sejumlah kalimat awal
    return summary.strip()

def text_card(text, title="Response"):
    card_html = f"""
    <div style="
        background-color: #2c2e3e;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 2px 2px 10px rgba(255, 255, 0, 0.1);
        display: inline-block;
        max-width: 90%; 
    ">
        <h3 style="color: #ffff;">{title}</h3>
        <p style="color: #ffff; font-size: 16px; line-height: 1.5;">
            {text}
        </p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def main():
    st.sidebar.title("Virtual Voice Assistant - AERA")
    st.title("🔊 **AERA Virtual Assistant** 💬")
    st.write("Hi! Click on the voice recorder to interact with me. How can I assist you?")

    recorded_audio = audio_recorder()

    if recorded_audio:
        audio_file = "user_audio.wav"
        with open(audio_file, "wb") as f:
            f.write(recorded_audio)

        transcribed_text = transcribe_audio(audio_file)
        if transcribed_text:
            text_card(transcribed_text, title="Audio Transcribtion")

            ai_response = search_on_serp_api(transcribed_text)

            response_audio_file = "response_audio.mp3"
            text_to_audio(ai_response, response_audio_file)
            st.audio(response_audio_file)
            summary = summarize_text(ai_response)
            text_card(summary, title="AERA Response")


if __name__ == "__main__":
    if not SERP_API_KEY:
        st.error("API key SERP API tidak ditemukan di environment variable.")
    else:
        main()
