# from flask import Flask, request, redirect
# import spotipy
# from spotipy.oauth2 import SpotifyOAuth

# app = Flask(__name__)

# SPOTIFY_CLIENT_ID = "94d868e7e3a94675bd84281027898e84"
# SPOTIFY_CLIENT_SECRET = "301a09e8829e41e498a12408cc4a553f"
# SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"

# # Initialize SpotifyOAuth
# sp_oauth = SpotifyOAuth(
#     client_id=SPOTIFY_CLIENT_ID,
#     client_secret=SPOTIFY_CLIENT_SECRET,
#     redirect_uri=SPOTIFY_REDIRECT_URI,
#     scope="user-read-private user-read-email"
# )

# @app.route('/')
# def home():
#     return "Flask server is running!"

# @app.route('/callback')
# def callback():
#     # Extract the authorization code from the query parameters
#     code = request.args.get('code')
#     if code:
#         # Exchange the code for an access token
#         token_info = sp_oauth.get_access_token(code)
#         access_token = token_info['access_token']
        
#         # Save the access token somewhere (e.g., a file or database)
#         with open("access_token.txt", "w") as token_file:
#             token_file.write(access_token)

#         return "Authorization successful! You can return to Streamlit now."
#     else:
#         return "Authorization failed. No code received."

# if __name__ == "__main__":
#     app.run(port=8888)

from flask import Flask, request, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

# Spotify credentials
SPOTIFY_CLIENT_ID = "94d868e7e3a94675bd84281027898e84"
SPOTIFY_CLIENT_SECRET = "301a09e8829e41e498a12408cc4a553f"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
scope = "user-read-playback-state user-modify-playback-state streaming user-read-private"

app = Flask(__name__)

# Cache path to store token info
CACHE_PATH = ".spotify_cache"

@app.route("/login")
def login():
    # Initialize SpotifyOAuth
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        cache_path=CACHE_PATH
    )
    # Redirect user to Spotify login
    return redirect(auth_manager.get_authorize_url())

@app.route("/callback")
def callback():
    # Extract the authorization code from the request
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        cache_path=CACHE_PATH
    )
    code = request.args.get("code")
    token_info = auth_manager.get_access_token(code)
    
    # Save the token to a file for use in Streamlit
    with open("access_token.txt", "w") as f:
        f.write(token_info['access_token'])
    
    return "Authentication successful! You can close this window and return to Streamlit."

if __name__ == "__main__":
    app.run(port=8888)

