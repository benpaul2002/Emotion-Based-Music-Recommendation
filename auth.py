from flask import Flask, request, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import time
import sqlite3

# Spotify credentials
SPOTIFY_CLIENT_ID = "94d868e7e3a94675bd84281027898e84"
SPOTIFY_CLIENT_SECRET = "301a09e8829e41e498a12408cc4a553f"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "user-read-email streaming user-read-private"
CACHE_PATH = ".spotify_cache"

app = Flask(__name__)

# Initialize SpotifyOAuth
auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE_PATH
)

@app.route("/login")
def login():
    # Redirect user to Spotify login
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    # Extract the authorization code
    code = request.args.get("code")
    token_info = auth_manager.get_access_token(code)
    save_token(token_info)
    return "Authentication successful! You can close this tab."

def save_token(token_info):
    # Save token info (access and refresh tokens) to a file
    with open("access_token.txt", "w") as f:
        f.write(token_info["access_token"])

def get_valid_token():
    # Check if token exists and is valid; refresh if necessary
    token_info = auth_manager.get_cached_token()
    if not token_info or auth_manager.is_token_expired(token_info):
        token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
        save_token(token_info)
    return token_info["access_token"]

@app.route("/token")
def token():
    # Return a valid access token
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
