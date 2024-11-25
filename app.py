import streamlit as st
from fer import FER
from PIL import Image
import io
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import tempfile
import cv2
import time
from collections import Counter
from datetime import datetime, timedelta

# Spotify API credentials
SPOTIFY_CLIENT_ID = "94d868e7e3a94675bd84281027898e84"
SPOTIFY_CLIENT_SECRET = "301a09e8829e41e498a12408cc4a553f"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
scope = "user-read-playback-state user-modify-playback-state streaming user-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                               client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope=scope))

st.components.v1.html("""
<script>
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }
</script>
""", height=0)

emotion_to_songs = {
    "happy": ["https://open.spotify.com/track/1ltBhiP2wDvuxkkAfvZvkJ?si=e84f1ccc47304328"],
    "sad": ["https://open.spotify.com/track/1ltBhiP2wDvuxkkAfvZvkJ?si=e84f1ccc47304328"],
    "angry": ["https://open.spotify.com/track/1ltBhiP2wDvuxkkAfvZvkJ?si=e84f1ccc47304328"],
    "surprise": ["https://open.spotify.com/track/1ltBhiP2wDvuxkkAfvZvkJ?si=e84f1ccc47304328"],
    "neutral": ["https://open.spotify.com/track/1ltBhiP2wDvuxkkAfvZvkJ?si=e84f1ccc47304328"],
    "fear": ["https://open.spotify.com/track/1ltBhiP2wDvuxkkAfvZvkJ?si=e84f1ccc47304328"],
    "disgust": ["https://open.spotify.com/track/1ltBhiP2wDvuxkkAfvZvkJ?si=e84f1ccc47304328"]
}

user_profile = sp.me()
user_product = user_profile.get("product", "free")

def get_dominant_emotion(emotions_list):
    if not emotions_list:
        return None
    emotion_counts = Counter([e[0] for e in emotions_list])
    return emotion_counts.most_common(1)[0][0]

def run_spotify_app():
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
                            
                        st.write("### Recommended Songs:")
                        for song_uri in emotion_to_songs.get(emotion, []):
                            track = sp.track(song_uri)
                            st.markdown(f"- {track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")

                        if user_product == "premium":
                            st.success("You have a Premium account! Playing the first recommended song within the app.")
                            selected_song_uri = emotion_to_songs[emotion][0]

                            # Play song using Spotify Web Playback SDK
                            st.components.v1.html(
                                f"""
                                <script src="https://sdk.scdn.co/spotify-player.js"></script>
                                <script>
                                    window.onSpotifyWebPlaybackSDKReady = () => {{
                                        const token = '{sp.auth_manager.get_access_token()}';
                                        const player = new Spotify.Player({{
                                            name: 'Streamlit Music Player',
                                            getOAuthToken: cb => {{ cb(token); }},
                                            volume: 0.5
                                        }});

                                        player.addListener('ready', {{ device_id }} => {{
                                            fetch('https://api.spotify.com/v1/me/player/play', {{
                                                method: 'PUT',
                                                headers: {{
                                                    'Authorization': `Bearer ${token}`,
                                                    'Content-Type': 'application/json',
                                                }},
                                                body: JSON.stringify({{
                                                    uris: ['{selected_song_uri}']
                                                }})
                                            }});
                                        }});

                                        player.connect();
                                    }};
                                </script>
                                """,
                                height=300,
                            )
                        else:
                            st.warning("You have a Free account. Redirecting to Spotify Web Player.")
                            web_url = f"{emotion_to_songs[emotion][0]}"
                            st.markdown(f"[Play on Spotify Web Player]({web_url})")
                else:
                    st.write("Could not detect any emotions. Please try again.")

        cap.release()
