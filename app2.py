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

# YouTube API key
YOUTUBE_API_KEY = "AIzaSyB3YTjRbS3H4ylFdzHz7185MrmCyJbMQdk"

# Emotion to song mapping (keywords for YouTube search)
emotion_to_songs = {
    "happy": ["Happy Pharrell Williams", "Uptown Funk Mark Ronson", "Can't Stop The Feeling Justin Timberlake"],
    "sad": ["Someone Like You Adele", "Fix You Coldplay", "Let Her Go Passenger"],
    "angry": ["Break Stuff Limp Bizkit", "Killing in the Name Rage Against the Machine", "Last Resort Papa Roach"],
    "surprise": ["Beautiful Day U2", "I Gotta Feeling Black Eyed Peas", "Wake Me Up Avicii"],
    "neutral": ["Shape of You Ed Sheeran", "Blinding Lights The Weeknd", "Perfect Ed Sheeran"],
    "fear": ["Boulevard of Broken Dreams Green Day", "Creep Radiohead", "Smells Like Teen Spirit Nirvana"],
    "disgust": ["Bad Guy Billie Eilish", "Toxic Britney Spears", "Animals Maroon 5"]
}

# Function to fetch YouTube video
def get_youtube_video(dominant_emotion, VIDEO_PLACEHOLDER):
    if dominant_emotion in emotion_to_songs:
        # video_url = get_youtube_video(emotion_to_songs[dominant_emotion][0])
        video_url = None
        base_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": emotion_to_songs[dominant_emotion][0],
            "key": YOUTUBE_API_KEY,
            "type": "video",
            "maxResults": 1,
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            results = response.json()
            if results.get("items"):
                video_id = results["items"][0]["id"]["videoId"]
                video_url = f"https://www.youtube.com/embed/{video_id}"
        if video_url:
            VIDEO_PLACEHOLDER.empty()
            VIDEO_PLACEHOLDER.markdown(f"<iframe width='560' height='315' src='{video_url}' frameborder='0' allowfullscreen></iframe>", unsafe_allow_html=True)
        else:
            VIDEO_PLACEHOLDER.markdown("Could not fetch a song. Try again later.")
