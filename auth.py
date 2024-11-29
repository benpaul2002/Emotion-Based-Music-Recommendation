from flask import Flask, request, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

# Spotify credentials
SPOTIFY_CLIENT_ID = "94d868e7e3a94675bd84281027898e84"
SPOTIFY_CLIENT_SECRET = "301a09e8829e41e498a12408cc4a553f"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
scope = "user-read-email streaming user-read-playback-state user-modify-playback-state app-remote-control user-read-private"
app = Flask(__name__)

# Cache path to store token info
CACHE_PATH = ".spotify_cache"

@app.route("/login")
def login():
    # Initialize SpotifyOAuth with the correct parameters
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        cache_path=CACHE_PATH
    )
    
    # Redirect user to Spotify login
    auth_url = auth_manager.get_authorize_url()
    print("Redirecting to:", auth_url)  # For debugging
    return redirect(auth_url)

@app.route("/callback")
def callback():
    # Extract the authorization code from the request
    code = request.args.get("code")
    
    # Initialize SpotifyOAuth again in the callback to get the token
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        cache_path=CACHE_PATH
    )
    
    # Exchange authorization code for an access token
    token_info = auth_manager.get_access_token(code)
    
    # Save the access token to a file for use
    with open("access_token.txt", "w") as f:
        f.write(token_info['access_token'])
    
    # Return a success message with the access token
    return f"Authentication successful! Access token: {token_info['access_token']}"

if __name__ == "__main__":
    app.run(port=8888)
