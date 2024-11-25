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

st.components.v1.html("""
<script>
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }
</script>
""", height=0)


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
def get_youtube_video(search_query):
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": search_query,
        "key": YOUTUBE_API_KEY,
        "type": "video",
        "maxResults": 1,
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        results = response.json()
        if results.get("items"):
            video_id = results["items"][0]["id"]["videoId"]
            return f"https://www.youtube.com/embed/{video_id}"
    return None

def get_dominant_emotion(emotions_list):
    if not emotions_list:
        return None
    # Count occurrences of each emotion and return the most common one
    emotion_counts = Counter([e[0] for e in emotions_list])
    return emotion_counts.most_common(1)[0][0]

# Main function for YouTube app
def run_youtube_app():
    # Title and description
    # st.title("Emotion-Based YouTube Music Recommendation 🎥")
    # st.write("Choose between using a **webcam** or uploading a **video file**, and we'll detect your emotion to recommend music!")

    # Input type selector
    input_type = st.radio("Select Input Type", ("Webcam", "Upload Video"))
    # Notification toggle
    notifications_enabled = st.checkbox("Enable Notifications", value=True)


    detector = FER(mtcnn=True)  # Initialize the emotion detector
    FRAME_WINDOW = st.image([])  # Placeholder for displaying frames
    VIDEO_PLACEHOLDER = st.empty()  # Placeholder for the YouTube video

    emotion_history = []  # Stores tuples of (emotion, timestamp)
    last_dominant_emotion = None

    cap = None

    if input_type == "Webcam":
        run = st.checkbox("Start Webcam")
        if run:
            cap = cv2.VideoCapture(0)  # Open webcam
        
    elif input_type == "Upload Video":
        uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])
        if uploaded_video:
            tfile = tempfile.NamedTemporaryFile(delete=False)  # Save uploaded video temporarily
            tfile.write(uploaded_video.read())
            cap = cv2.VideoCapture(tfile.name)

    if cap:
        last_emotion_time = time.time()
        current_emotion = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to capture video. Check your webcam.")
                break

            # Convert frame to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            FRAME_WINDOW.image(rgb_frame, channels="RGB")

            # Check if 5 seconds have passed since last emotion detection
            current_time = time.time()
            if current_time - last_emotion_time >= 5:
                last_emotion_time = current_time
                st.write("Analyzing emotion...")
                emotions = detector.top_emotion(rgb_frame)

                if emotions:
                    emotion, score = emotions
                    emotion_history.append((emotion, datetime.now()))
                    st.write(f"Detected emotion: **{emotion.capitalize()}** (confidence: {score * 100:.2f}%)")

                    # Keep only last minute's emotions
                    one_minute_ago = datetime.now() - timedelta(minutes=1)
                    emotion_history = [(e, t) for e, t in emotion_history if t > one_minute_ago]

                    # Determine dominant emotion in the last minute
                    dominant_emotion = get_dominant_emotion(emotion_history)
                    if dominant_emotion != last_dominant_emotion:
                        last_dominant_emotion = dominant_emotion
                        if notifications_enabled:
                            app_url = "http://localhost:8501"  # Replace with your ap's URL
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
                        st.write("Fetching a song based on your emotion...")

                        # Get a song for the detected emotion
                        if dominant_emotion in emotion_to_songs:
                            video_url = get_youtube_video(emotion_to_songs[dominant_emotion][0])
                            if video_url:
                                VIDEO_PLACEHOLDER.empty()
                                VIDEO_PLACEHOLDER.markdown(f"<iframe width='560' height='315' src='{video_url}' frameborder='0' allowfullscreen></iframe>", unsafe_allow_html=True)
                            else:
                                st.write("Could not fetch a song. Try again later.")
                        else:
                            st.write("No song mapping found for this emotion.")

                else:
                    st.write("Could not detect any emotions. Please try again.")

        cap.release()
