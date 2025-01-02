from flask import Flask, request, redirect, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import time
import sqlite3
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = os.getenv("SCOPE")
CACHE_PATH = os.getenv("CACHE_PATH")

app = Flask(__name__)

auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE_PATH
)

@app.route("/login")
def login():
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = auth_manager.get_access_token(code)
    save_token(token_info)
    return "Authentication successful! You can close this tab."

def save_token(token_info):
    with open("access_token.txt", "w") as f:
        f.write(token_info["access_token"])

def get_valid_token():
    token_info = auth_manager.get_cached_token()
    if not token_info or auth_manager.is_token_expired(token_info):
        token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
        save_token(token_info)
    return token_info["access_token"]

@app.route("/token")
def token():
    try:
        access_token = get_valid_token()
        return {"access_token": access_token}
    except Exception as e:
        return {"error": str(e)}
    
def delete_song_from_emotion(uri, emotion):
    conn = sqlite3.connect('music_emotions.db')
    c = conn.cursor()
    c.execute('DELETE FROM songs WHERE uri = ? AND emotion = ?', (uri, emotion))
    conn.commit()
    conn.close()

@app.route("/delete_song", methods=["POST"])
def delete_song():
    try:
        uri = request.form.get("uri")
        emotion = request.form.get("emotion")
        delete_song_from_emotion(uri, emotion)
        
        return """
            <div style="color: #155724; background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; 
                        margin-top: 10px; border-radius: 4px;">
                Song deleted successfully!
            </div>
        """
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(port=8888)
