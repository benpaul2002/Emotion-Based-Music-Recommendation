import streamlit as st
from app import run_spotify_app
from app2 import run_youtube_app

# Title and Description
st.title("Emotion-Based Music Recommendation 🎵")
# st.write("Choose your preferred platform to get started:")

# Sidebar for Navigation
st.sidebar.title("Navigation")
platform_choice = st.sidebar.radio(
    "Select your platform",
    ("Spotify", "YouTube")
)

# Main Page Logic
if platform_choice == "Spotify":
    # st.header("Spotify Music Recommendation")
    run_spotify_app()  # Call Spotify app function
elif platform_choice == "YouTube":
    # st.header("YouTube Music Recommendation")
    run_youtube_app()  # Call YouTube app function
