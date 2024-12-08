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
import sqlite3
from streamlit.components.v1 import html

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

    try:
        with open("access_token.txt", "r") as f:
            access_token = f.read().strip()
        st.session_state.spotify = Spotify(auth=access_token)
        
        user_profile = st.session_state.spotify.me()
        st.success(f"Welcome, {user_profile['display_name']}!")
        return st.session_state.spotify
    except FileNotFoundError:
        st.warning("Log in to Spotify to proceed.")

    return None

def init_db():
    conn = sqlite3.connect('music_emotions.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uri TEXT NOT NULL,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            album TEXT NOT NULL,
            album_art TEXT,
            emotion TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def add_song(uri, title, artist, album, album_art, emotion):
    conn = sqlite3.connect('music_emotions.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO songs (uri, title, artist, album, album_art, emotion)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (uri, title, artist, album, album_art, emotion))
    
    conn.commit()
    conn.close()

def get_songs_by_emotion(emotion):
    conn = sqlite3.connect('music_emotions.db')
    c = conn.cursor()
    c.execute('SELECT * FROM songs WHERE emotion = ?', (emotion,))
    songs = c.fetchall()
    conn.close()
    
    return [
        {
            'uri': song[1],
            'title': song[2],
            'artist': song[3],
            'album': song[4],
            'album_art': song[5]
        }
        for song in songs
    ]

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

    with st.expander("Explore/Add Songs by Emotion", expanded=True):
        selected_emotion = st.selectbox(
            "Choose an emotion",
            options=list(st.session_state.song_metadata.keys()),
            index=0,
        )
        
        if selected_emotion:
            if not st.session_state.song_metadata[selected_emotion]:
                st.info("No songs found for this emotion. Try searching for songs to add!")
            else:
                songs = st.session_state.song_metadata[selected_emotion]
                carousel_items = []
                for song in songs:
                    item = {
                        "style": {
                            "color": "#fff",
                            "fontSize": "24px",
                            "textAlign": "left"
                        },
                        "content": f"""
                            <div style="display: flex; align-items: center; gap: 20px; justify-content: space-between;">
                                <div style="display: flex; align-items: center; gap: 20px;">
                                    <img src="{song['album_art']}" style="width: 200px; height: 200px; border: 2px solid #595963;" />
                                    <p style="margin: 0;">{song['title']} - {song['artist']}</p>
                                </div>
                                <form action="http://localhost:8888/delete_song" method="post" style="margin: 0;">
                                    <input type="hidden" name="uri" value="{song['uri']}" />
                                    <input type="hidden" name="emotion" value="{selected_emotion}" />
                                    <button 
                                        type="submit" 
                                        style="background: none; border: none; cursor: pointer; padding: 5px;"
                                        onclick="window.parent.location.reload();">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="#FF5252">
                                            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                                        </svg>
                                    </button>
                                </form>
                            </div>
                        """
                    }
                    carousel_items.append(item)
                    
                carousel_style = {
                    "background-color": "#27272f",
                    "border-radius": "8px",
                    "padding": "20px",
                }

                st_ant_carousel(
                    carousel_items,
                    height=250,
                    adaptiveHeight=True,
                    autoplay=True,
                    easing="ease-in-out",
                    carousel_style=carousel_style
                )
        
        st.divider()
    
        with st.form("search_form"):
            col1, col2 = st.columns([4,1])
            with col1:
                placeholder_str = f"Search for a song to add to {selected_emotion} playlist"
                search_query = st.text_input("Search for a song", placeholder=placeholder_str, label_visibility="collapsed")
            with col2:
                search_button = st.form_submit_button("Search", type="primary")
            if search_button and search_query:
                results = st.session_state.spotify.search(search_query, type='track', limit=5)
                st.session_state.search_results = results

        if "search_results" in st.session_state:
            results = st.session_state.search_results
            if results['tracks']['items']:
                st.write("Search Results:")
                for track in results['tracks']['items']:
                    col1, col2, col3 = st.columns([1,3,1])
                    with col1:
                        st.image(track['album']['images'][0]['url'], width=100)
                    with col2:
                        st.write(f"**{track['name']}** - {track['artists'][0]['name']}")
                    with col3:
                        if st.button("Add to Playlist", key=f"add_{track['id']}"):
                            add_song(
                                track['uri'],
                                track['name'],
                                track['artists'][0]['name'],
                                track['album']['name'],
                                track['album']['images'][0]['url'],
                                selected_emotion
                            )
                            st.success(f"Added to {selected_emotion} playlist!")
                            html("<script>window.parent.location.reload();</script>")



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
    if not st.session_state.song_metadata[dominant_emotion]:
        st.warning("No songs found for this emotion. Try adding songs to the playlist.")
        return
    if platform_choice == "Spotify":
        song_metadata = st.session_state.song_metadata[dominant_emotion]
        get_spotify_song(spotify, user_product, song_placeholder, song_metadata)
    elif platform_choice == "YouTube":
        song_name = st.session_state.song_metadata[dominant_emotion][0]['title']
        artist_name = st.session_state.song_metadata[dominant_emotion][0]['artist']
        song_details_list = []
        for song in st.session_state.song_metadata[dominant_emotion]:
            song_details_list.append((song['title'], song['artist']))
        get_youtube_video(video_placeholder, song_details_list)

def process_video_feed(cap, frame_window, detector, song_placeholder, video_placeholder, emotion_container):
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
            
            emotion = process_emotion(rgb_frame, detector)
            if emotion:
                emotion_history.append((emotion, datetime.now()))
                
                dominant_emotion = last_dominant_emotion
                if datetime.now() - emotion_history[0][1] > timedelta(minutes=5):
                    dominant_emotion = get_dominant_emotion(emotion_history)
                    if dominant_emotion:
                        emotion_history = []

                if last_dominant_emotion is None:
                    dominant_emotion = emotion
                
                if dominant_emotion != last_dominant_emotion:
                    last_dominant_emotion = dominant_emotion
                    
                    if st.session_state.notifications_enabled:
                        show_notification(dominant_emotion, "http://localhost:8501")
                    emotion_container.markdown(f"**Current dominant emotion: {dominant_emotion.capitalize()}**")
                    
                    handle_media_playback(
                        st.session_state.platform_choice,
                        st.session_state.spotify,
                        st.session_state.user_product,
                        # dominant_emotion,
                        "happy",
                        song_placeholder,
                        video_placeholder
                    )

def run_main_app():
    if 'db_initialized' not in st.session_state:
        init_db()
        st.session_state.db_initialized = True

    if 'song_metadata' not in st.session_state:
        emotions = ['happy', 'sad', 'angry', 'surprise', 'neutral', 'fear', 'disgust']
        st.session_state.song_metadata = {}

        for emotion in emotions:
            st.session_state.song_metadata[emotion] = get_songs_by_emotion(emotion)


    setup_ui_and_auth()
    
    input_container = st.empty()
    frame_container = st.empty()
    media_container = st.empty()
    emotion_container = st.empty()
    
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
    
    # run = st.checkbox("Start Webcam")
    # if run:
    #     cap = cv2.VideoCapture(0)

    FRAME_WINDOW = frame_container.image([])
    
    with media_container:
        SONG_PLACEHOLDER = st.empty()
        VIDEO_PLACEHOLDER = st.empty()
    
    if cap:
        try:
            process_video_feed(cap, FRAME_WINDOW, detector, SONG_PLACEHOLDER, VIDEO_PLACEHOLDER, emotion_container)
        finally:
            cap.release()

run_main_app()
