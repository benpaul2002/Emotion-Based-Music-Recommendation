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

emotion_to_songs = {
    "happy": ["https://open.spotify.com/track/1ltBhiP2wDvuxkkAfvZvkJ?si=e84f1ccc47304328"],
    "sad": ["https://open.spotify.com/track/0ppdt8zRZOHIKh4ZDB0Zp9?si=00e848f2bf174c08"],
    "angry": ["https://open.spotify.com/track/4uJSCrI7r0usNJ3aaHAuC6?si=d3f4ae13b7ef4a42"],
    "surprise": ["https://open.spotify.com/track/3WtsQAngIkmcNeqVeK3fXQ?si=a058080bbe0b4968"],
    "neutral": ["https://open.spotify.com/track/4siXNiLG9VJR6Z2kP6fFjv?si=2d3c3f86522f4314"],
    "fear": ["https://open.spotify.com/track/7IDQX9EUgMNQTgYcZSpO1d?si=0ea5eada7cde4ff0"],
    "disgust": ["https://open.spotify.com/track/0fBPwRmfNmOdpNcxOoli9Q?si=eec02ce571f0432b"]
}

user_profile = sp.me()
user_product = user_profile.get("product", "free")

def get_spotify_song(dominant_emotion, SONG_PLACEHOLDER):
    if dominant_emotion in emotion_to_songs:
        song_uri = emotion_to_songs[dominant_emotion][0]
        track = sp.track(song_uri)
        song_name = track['name']
        artist_names = ', '.join(artist['name'] for artist in track['artists'])

        # Clear previous song and display the new one
        SONG_PLACEHOLDER.empty()
        SONG_PLACEHOLDER.markdown(
            f"""
            ### **{song_name}** by {artist_names}
            [Play on Spotify Web Player]({song_uri})
            """
        )

        if user_product == "premium":
            SONG_PLACEHOLDER.markdown("**Playing in-app...**")
            SONG_PLACEHOLDER.components.v1.html(
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
                                    uris: ['{song_uri}']
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
        SONG_PLACEHOLDER.markdown("No song mapping found for this emotion.")
