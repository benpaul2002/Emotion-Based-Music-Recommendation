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

YOUTUBE_API_KEY = "AIzaSyB3YTjRbS3H4ylFdzHz7185MrmCyJbMQdk"

# def get_youtube_video(VIDEO_PLACEHOLDER, song_name, artist_name):
#     video_url = None
#     base_url = "https://www.googleapis.com/youtube/v3/search"
#     search_query = f"{song_name} {artist_name}"
#     params = {
#         "part": "snippet",
#         "q": search_query,
#         "key": YOUTUBE_API_KEY,
#         "type": "video",
#         "maxResults": 1,
#     }
#     response = requests.get(base_url, params=params)
#     if response.status_code == 200:
#         results = response.json()
#         if results.get("items"):
#             video_id = results["items"][0]["id"]["videoId"]
#             video_url = f"https://www.youtube.com/embed/{video_id}"
#     if video_url:
#         VIDEO_PLACEHOLDER.empty()
#         VIDEO_PLACEHOLDER.markdown(f"<iframe width='560' height='315' src='{video_url}' frameborder='0' allowfullscreen></iframe>", unsafe_allow_html=True)
#     else:
#         VIDEO_PLACEHOLDER.markdown("Could not fetch a song. Try again later.")

def get_youtube_video(VIDEO_PLACEHOLDER, song_details_list):
    video_ids = []
    base_url = "https://www.googleapis.com/youtube/v3/search"
    
    # First collect all video IDs
    for song_detail in song_details_list:
        song_name = song_detail[0]
        artist_name = song_detail[1]
        query_str = f"{song_name} {artist_name}" 
        params = {
            "part": "snippet",
            "q": query_str,
            "key": YOUTUBE_API_KEY,
            "type": "video",
            "maxResults": 1,
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            results = response.json()
            if results.get("items"):
                video_ids.append(results["items"][0]["id"]["videoId"])
    
    if video_ids:
        # Create a playlist URL by joining video IDs with commas
        playlist_string = ",".join(video_ids)
        playlist_url = f"https://www.youtube.com/embed/{video_ids[0]}?playlist={playlist_string}"
        
        VIDEO_PLACEHOLDER.empty()
        VIDEO_PLACEHOLDER.markdown(
            f"<iframe width='560' height='315' src='{playlist_url}' frameborder='0' allowfullscreen></iframe>",
            unsafe_allow_html=True
        )
    else:
        VIDEO_PLACEHOLDER.markdown("Could not fetch any songs. Try again later.")
