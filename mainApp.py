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
from sp import get_spotify_song, fetch_song_metadata
from yt import get_youtube_video
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from st_ant_carousel import st_ant_carousel

SPOTIFY_CLIENT_ID = "94d868e7e3a94675bd84281027898e84"
SPOTIFY_CLIENT_SECRET = "301a09e8829e41e498a12408cc4a553f"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
scope = "user-read-email streaming user-read-playback-state user-modify-playback-state app-remote-control user-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                               client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope=scope))

LOGIN_URL = "http://localhost:8888/login"
TOKEN_URL = "http://localhost:8888/token"

def authenticate_spotify():
    if "spotify" not in st.session_state:
        st.session_state.spotify = None

    # Check if Spotify session exists
    if st.session_state.spotify:
        st.success("You are already authenticated!")
        return st.session_state.spotify
    
    st.write("Refresh the page if you have already logged in.")

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

emotion_to_songs = {
    "happy": ["Serenity Painted Death", "Harvest Opeth", "Seize the Day", "Zagreus"],
    "sad": ["Serenity Painted Death"],
    "angry": ["Serenity Painted Death"],
    "surprise": ["Serenity Painted Death"],
    "neutral": ["Serenity Painted Death"],
    "fear": ["Serenity Painted Death"],
    "disgust": ["Serenity Painted Death"]
}

def get_dominant_emotion(emotions_list):
    if not emotions_list:
        return None
    emotion_counts = Counter([e[0] for e in emotions_list])
    return emotion_counts.most_common(1)[0][0]

def setup_notifications():
    st.components.v1.html("""
    <script>
        if (Notification.permission !== "granted") {
            Notification.requestPermission();
        }
    </script>
    """, height=0)

def setup_spotify_auth():
    if "spotify" not in st.session_state or st.session_state.spotify is None:
        response = requests.get(TOKEN_URL)
        token_data = response.json()
        if "access_token" in token_data:
            access_token = token_data["access_token"]
            st.session_state.spotify = Spotify(auth=access_token)
            
            user_profile = st.session_state.spotify.me()
            st.success(f"Welcome, {user_profile['display_name']}!")
        else:
            spotify_client = authenticate_spotify()
            if not spotify_client:
                st.stop()
    
    if st.session_state.spotify:
        try:
            sp = st.session_state.spotify
            user_profile = sp.me()
            st.session_state.user_product = user_profile.get("product", "free")
        except AttributeError:
            st.error("Spotify client is not properly initialized. Please log in again.")

def setup_ui_and_auth():
    st.title("Emotion Based Music Recommendation 🎵")

    st.sidebar.title("Platform selection")
    if "platform_choice" not in st.session_state:
        st.session_state.platform_choice = "Spotify"
    
    spotify_selected = st.sidebar.button("Spotify", use_container_width=True, key="spotify_btn")
    youtube_selected = st.sidebar.button("YouTube", use_container_width=True, key="youtube_btn")
    
    new_platform_choice = st.session_state.platform_choice
    if spotify_selected:
        new_platform_choice = "Spotify"
    elif youtube_selected:
        new_platform_choice = "YouTube"
    
    if new_platform_choice != st.session_state.platform_choice:
        st.session_state.platform_choice = new_platform_choice
        # st.rerun()
    
    sidebar_placeholder = st.sidebar.empty()
    with sidebar_placeholder.expander("Settings", expanded=False):
        st.session_state.notifications_enabled = st.checkbox("Enable Notifications", value=True)

    if st.session_state.platform_choice == "Spotify":
        setup_spotify_auth()
    
    setup_notifications()

    main_container = st.container()
    with main_container:
        st.subheader("Explore Songs by Emotion")
        
        selected_emotion = st.selectbox(
            "Choose an emotion",
            options=list(emotion_to_songs.keys()),
            index=0,
        )
        
        if selected_emotion:
            songs = []
            for song_name in emotion_to_songs[selected_emotion]:
                metadata = fetch_song_metadata(st.session_state.spotify, song_name)
                songs.append(metadata)
               
            carousel_items = []
            for song in songs:
                item = {
                    "style": {
                        "color": "#fff",
                        "fontSize": "24px",
                        "textAlign": "left"
                    },
                    "content": f"""
                        <div style="display: flex; align-items: center; gap: 20px;">
                            <img src="{song['album_art']}" style="width: 200px; height: 200px; border: 2px solid #595963;" />
                            <p style="margin: 0;">{song['title']} - {song['artist']}</p>
                        </div>
                    """
                }
                carousel_items.append(item)

            carousel_style = {
                "background-color": "#27272f",
                "border-radius": "8px",
                "padding": "20px"
            }

            st_ant_carousel(
                carousel_items,
                height=400,
                adaptiveHeight=True,
                autoplay=True,
                easing="ease-in-out",
                carousel_style=carousel_style
            )


def process_emotion(frame, detector):
    emotions = detector.top_emotion(frame)
    if not emotions:
        st.write("Could not detect any emotions. Please try again.")
        return None
    
    emotion, score = emotions
    if emotion is None:
        st.write("Could not detect any emotions.")
        return None
        
    st.write(f"Detected emotion: **{emotion.capitalize()}** (confidence: {score * 100:.2f}%)")
    return emotion

def show_notification(emotion, app_url):
    st.components.v1.html(f"""
    <script>
        const appUrl = "{app_url}";
        const notification = new Notification("New Emotion Detected!", {{
            body: "Detected Emotion: {emotion.capitalize()}",
            icon: "https://cdn-icons-png.flaticon.com/512/847/847969.png"
        }});
        notification.onclick = function(event) {{
            event.preventDefault();
            const appTab = window.open(appUrl, "_self");
            if (appTab) {{
                appTab.focus();
            }} else {{
                console.error("Unable to focus app tab. Ensure pop-ups are allowed.");
            }}
        }};
    </script>
    """, height=0)

def handle_media_playback(platform_choice, spotify, user_product, dominant_emotion, song_placeholder, video_placeholder):
    if platform_choice == "Spotify":
        song_uri = emotion_to_songs[dominant_emotion][0]
        get_spotify_song(spotify, user_product, dominant_emotion, song_placeholder, song_uri)
    elif platform_choice == "YouTube":
        get_youtube_video(dominant_emotion, video_placeholder)

def process_video_feed(cap, frame_window, detector, song_placeholder, video_placeholder):
    last_emotion_time = time.time()
    emotion_history = []
    last_dominant_emotion = None
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to read video frame. Check your webcam or video file.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_window.image(rgb_frame, channels="RGB")

        current_time = time.time()
        if current_time - last_emotion_time >= 5:
            last_emotion_time = current_time
            st.write("Analyzing emotion...")
            
            emotion = process_emotion(rgb_frame, detector)
            if emotion:
                emotion_history.append((emotion, datetime.now()))
                
                dominant_emotion = last_dominant_emotion
                if datetime.now() - emotion_history[0][1] > timedelta(seconds=10):
                    dominant_emotion = get_dominant_emotion(emotion_history)
                    if dominant_emotion:
                        emotion_history = []
                
                if dominant_emotion != last_dominant_emotion:
                    last_dominant_emotion = dominant_emotion
                    
                    if st.session_state.notifications_enabled:
                        show_notification(emotion, "http://localhost:8501")
                    st.write(f"**New Dominant Emotion: {dominant_emotion.capitalize()}**")
                    
                    handle_media_playback(
                        st.session_state.platform_choice,
                        st.session_state.spotify,
                        st.session_state.user_product,
                        dominant_emotion,
                        song_placeholder,
                        video_placeholder
                    )

def run_main_app():
    setup_ui_and_auth()
    
    input_container = st.empty()
    frame_container = st.empty()
    media_container = st.empty()
    
    with input_container:
        input_type = st.radio("Choose Input Source", ["Webcam", "Upload Video"], index=0)
    
    detector = FER(mtcnn=True)
    cap = None
    
    if input_type == "Webcam":
        run = st.checkbox("Start Webcam")
        if run:
            cap = cv2.VideoCapture(0)
    else:
        uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])
        if uploaded_video:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_video.read())
            cap = cv2.VideoCapture(tfile.name)
    
    FRAME_WINDOW = frame_container.image([])
    
    with media_container:
        SONG_PLACEHOLDER = st.empty()
        VIDEO_PLACEHOLDER = st.empty()
    
    if cap:
        try:
            process_video_feed(cap, FRAME_WINDOW, detector, SONG_PLACEHOLDER, VIDEO_PLACEHOLDER)
        finally:
            cap.release()

run_main_app()
