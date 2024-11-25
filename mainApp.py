import streamlit as st
import cv2
from fer import FER
from PIL import Image
import numpy as np
import time
import requests
import streamlit.components.v1 as components
import tempfile
from collections import Counter
from datetime import datetime, timedelta
import tempfile
from app import get_spotify_song
from app2 import get_youtube_video

# Title and Description
st.title("Emotion-Based Music Recommendation 🎵")
# st.write("Choose your preferred platform to get started:")

# Sidebar for Navigation
st.sidebar.title("Navigation")
platform_choice = st.sidebar.radio(
    "Select your platform",
    ("Spotify", "YouTube")
)

st.components.v1.html("""
<script>
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }
</script>
""", height=0)

def get_dominant_emotion(emotions_list):
    if not emotions_list:
        return None
    emotion_counts = Counter([e[0] for e in emotions_list])
    return emotion_counts.most_common(1)[0][0]

def run_main_app():
    input_type = st.radio("Choose Input Source", ["Webcam", "Upload Video"])
    notifications_enabled = st.checkbox("Enable Notifications", value=True)

    FRAME_WINDOW = st.image([])
    detector = FER(mtcnn=True)
    cap = None

    emotion_history = []  # Stores tuples of (emotion, timestamp)
    last_dominant_emotion = None

    if input_type == "Webcam":
        run = st.checkbox("Start Webcam")
        if run:
            cap = cv2.VideoCapture(0)

    elif input_type == "Upload Video":
        uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])
        if uploaded_video:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_video.read())
            cap = cv2.VideoCapture(tfile.name)

    SONG_PLACEHOLDER = st.empty()
    VIDEO_PLACEHOLDER = st.empty()

    if cap:
        last_emotion_time = time.time()
        current_emotion = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to read video frame. Check your webcam or video file.")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            FRAME_WINDOW.image(rgb_frame, channels="RGB")

            current_time = time.time()
            if current_time - last_emotion_time >= 5:
                last_emotion_time = current_time
                st.write("Analyzing emotion...")
                emotions = detector.top_emotion(rgb_frame)

                if emotions:
                    emotion, score = emotions
                    emotion_history.append((emotion, datetime.now()))
                    st.write(f"Detected emotion: **{emotion.capitalize()}** (confidence: {score * 100:.2f}%)")

                    one_minute_ago = datetime.now() - timedelta(minutes=1)
                    emotion_history = [(e, t) for e, t in emotion_history if t > one_minute_ago]

                    dominant_emotion = get_dominant_emotion(emotion_history)
                    
                    if dominant_emotion != last_dominant_emotion:
                        last_dominant_emotion = dominant_emotion

                        if notifications_enabled:
                            app_url = "http://localhost:8501"
                            st.components.v1.html(f"""
                            <script>
                                const appUrl = "{app_url}";

                                const notification = new Notification("New Emotion Detected!", {{
                                    body: "Detected Emotion: {emotion.capitalize()}",
                                    icon: "https://cdn-icons-png.flaticon.com/512/847/847969.png"
                                }});

                                notification.onclick = function(event) {{
                                    event.preventDefault();
                                    
                                    // Open or focus the app tab
                                    const appTab = window.open(appUrl, "_self");
                                    if (appTab) {{
                                        appTab.focus();
                                    }} else {{
                                        console.error("Unable to focus app tab. Ensure pop-ups are allowed.");
                                    }}
                                }};
                            </script>
                            """, height=0)
                        st.write(f"**New Dominant Emotion: {dominant_emotion.capitalize()}**")
                        
                        if platform_choice == "Spotify":
                            get_spotify_song(dominant_emotion, SONG_PLACEHOLDER)
                        elif platform_choice == "YouTube":
                            get_youtube_video(dominant_emotion, VIDEO_PLACEHOLDER)
                else:
                    st.write("Could not detect any emotions. Please try again.")

        cap.release()

run_main_app()
