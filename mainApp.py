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
from sp import get_spotify_song
from yt import get_youtube_video
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify

SPOTIFY_CLIENT_ID = "94d868e7e3a94675bd84281027898e84"
SPOTIFY_CLIENT_SECRET = "301a09e8829e41e498a12408cc4a553f"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
scope = "user-read-email streaming user-read-playback-state user-modify-playback-state app-remote-control user-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                               client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope=scope))

LOGIN_URL = "http://localhost:8888/login"

def authenticate_spotify():
    if "spotify" not in st.session_state:
        st.session_state.spotify = None

    # Check if Spotify session exists
    if st.session_state.spotify:
        st.success("You are already authenticated!")
        return st.session_state.spotify

    # Display login button
    # st.markdown(f"[Log in to Spotify]({LOGIN_URL})")

    st.markdown(
        f"""
        <style>
            .spotify-button {{
                background-color: #0a421e;
                color: white;
                padding: 15px 32px;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .spotify-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                background-color: #116f32;
            }}
            
            .spotify-button:active {{
                transform: translateY(1px);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .spotify-button::before {{
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 100%;
                height: 100%;
                transform: translate(-50%, -50%) scale(0);
                transition: transform 0.5s ease-out;
            }}
            
            .spotify-button:hover::before {{
                transform: translate(-50%, -50%) scale(2);
            }}
            
            .button-container {{
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 40px 0;
            }}
        </style>
        
        <div class="button-container">
            <a href="{LOGIN_URL}">
                <button class="spotify-button">
                    Connect with Spotify
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Check for access token file
    try:
        with open("access_token.txt", "r") as f:
            access_token = f.read().strip()
        st.session_state.spotify = Spotify(auth=access_token)
        
        # Fetch and display user information
        user_profile = st.session_state.spotify.me()
        st.success(f"Welcome, {user_profile['display_name']}!")
        return st.session_state.spotify
    except FileNotFoundError:
        st.warning("Log in to Spotify to proceed.")

    return None

st.title("Emotion-Based Music Recommendation 🎵")

st.sidebar.title("Navigation")
platform_choice = st.sidebar.radio(
    "Select your platform",
    ("Spotify", "YouTube")
)

if platform_choice=="Spotify":
    if "spotify" not in st.session_state or st.session_state.spotify is None:
        # st.write("Log in to Spotify to get personalized song recommendations.")
        spotify_client = authenticate_spotify()
        if not spotify_client:
            st.stop()

if st.session_state.spotify:
    try:
        sp = st.session_state.spotify
        user_profile = sp.me()  # This might fail if `sp` is None
        st.session_state.user_product = user_profile.get("product", "free")
        # st.write(f"Welcome, {user_profile['display_name']}!")
    except AttributeError:
        st.error("Spotify client is not properly initialized. Please log in again.")

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
                            get_spotify_song(st.session_state.spotify, st.session_state.user_product, dominant_emotion, SONG_PLACEHOLDER)
                        elif platform_choice == "YouTube":
                            get_youtube_video(dominant_emotion, VIDEO_PLACEHOLDER)
                else:
                    st.write("Could not detect any emotions. Please try again.")

        cap.release()

run_main_app()
