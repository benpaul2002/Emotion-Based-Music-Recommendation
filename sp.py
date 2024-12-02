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
from streamlit.components.v1 import html

def fetch_song_metadata(sp, song_name):
    results = sp.search(q=song_name, type='track', limit=1)
    if not results['tracks']['items']:
        return None
    
    track = results['tracks']['items'][0]
    metadata = {
        "uri": track["uri"],
        "title": track["name"],
        "artist": ", ".join([artist["name"] for artist in track["artists"]]),
        "album": track["album"]["name"],
        "album_art": track["album"]["images"][0]["url"],
    }
    return metadata

def get_spotify_song(sp, user_product, SONG_PLACEHOLDER, song_uri):
    track = sp.track(song_uri)
    song_name = track['name']
    artist_names = ', '.join(artist['name'] for artist in track['artists'])

    SONG_PLACEHOLDER.empty()
    SONG_PLACEHOLDER.markdown(
        f"""
        ### 🎵 **{song_name}** by {artist_names}
        [Play on Spotify Web Player]({song_uri})
        """
    )

    if user_product == "premium":
        try:
            with open("access_token.txt", "r") as f:
                token = f.read().strip()
        except FileNotFoundError:
            st.warning("Log in to Spotify to proceed.")
        SONG_PLACEHOLDER.markdown("**Playing in-app...**")
        html_content = f"""
            <div style="width: 100%; max-width: 500px; margin: 20px auto; padding: 20px; border-radius: 10px; background-color: #222; color: white; text-align: center; font-family: Arial, sans-serif;">
                <h3 style="margin-bottom: 20px;">Spotify Player</h3>

                <div id="coverArtContainer" style="width: 100%; height: 250px; background-color: #333; border-radius: 10px; margin-bottom: 20px;">
                    <img id="coverArt" src="" alt="Track Cover Art" style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px;">
                </div>

                <div style="display: flex; justify-content: space-evenly; margin-top: 20px;">
                    <button id="playPauseButton" style="background-color: #1db954; border: none; color: white; padding: 15px 30px; font-size: 16px; border-radius: 5px; cursor: pointer;">Pause</button>
                    <button id="skipButton" style="background-color: #1db954; border: none; color: white; padding: 15px 30px; font-size: 16px; border-radius: 5px; cursor: pointer;">Next</button>
                </div>

                <div style="margin-top: 20px;">
                    <label for="volume" style="color: white; font-size: 14px; margin-right: 10px;">Volume</label>
                    <input type="range" id="volume" name="volume" min="0" max="1" step="0.01" value="0.5" style="width: 100%; max-width: 300px;"/>
                </div>
            </div>

            <script src="https://sdk.scdn.co/spotify-player.js"></script>
            <script>
                window.onSpotifyWebPlaybackSDKReady = () => {{
                    const token = '{token}';  // Ensure this token is valid
                    const songUri = '{song_uri}';  // Replace with the actual song URI
                    const token_str = "Bearer " + token;

                    const player = new Spotify.Player({{
                        name: 'Streamlit Music Player',
                        getOAuthToken: cb => cb(token),
                        volume: 0.5
                    }});

                    player.addListener('ready', ({{ device_id }}) => {{
                        console.log('Spotify Player ready with Device ID:', device_id);

                        fetch('https://api.spotify.com/v1/me/player/play?device_id=' + device_id, {{
                            method: 'PUT',
                            headers: {{
                                'Authorization': token_str,
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{ uris: [songUri] }})
                        }})
                        .then(response => {{
                            if (response.ok) {{
                                console.log('Track is now playing!');
                                fetch('https://api.spotify.com/v1/me/player/currently-playing', {{
                                    headers: {{
                                        'Authorization': token_str,
                                    }}
                                }})
                                .then(response => {{
                                    if (response.status === 204) {{
                                        console.log('No track is currently playing.');
                                        document.getElementById('coverArt').src = 'https://via.placeholder.com/500x250.png?text=No+Track+Playing';
                                        return;  // Exit early since there is no track info
                                    }}

                                    const contentType = response.headers.get('Content-Type');
                                    if (!contentType || !contentType.includes('application/json')) {{
                                        console.error('Response is not in JSON format');
                                        return Promise.reject('Response is not JSON');
                                    }}

                                    return response.json();
                                }})
                                .then(data => {{
                                    if (data && data.item && data.item.album && data.item.album.images[0]) {{
                                        const coverArtUrl = data.item.album.images[0].url;  // Get the largest cover image
                                        document.getElementById('coverArt').src = coverArtUrl;  // Set the cover art source
                                    }} else {{
                                        console.warn('No album image found');
                                        document.getElementById('coverArt').src = 'https://via.placeholder.com/500x250.png?text=No+Album+Image';
                                    }}
                                }})
                                .catch(error => {{
                                    console.error('Error fetching track details:', error);
                                    document.getElementById('coverArt').src = 'https://via.placeholder.com/500x250.png?text=Error+Fetching+Track';
                                }});

                            }} else {{
                                console.error('Failed to play track:', response.statusText);
                            }}
                        }})
                        .catch(error => console.error('Error while playing track:', error));
                    }});

                    player.addListener('not_ready', ({{ device_id }}) => {{
                        console.warn('Spotify Player device ID has gone offline:', device_id);
                    }});

                    player.addListener('playback_error', ({{ message }}) => {{
                        console.error('Spotify Player Playback Error:', message);
                    }});

                    player.connect().then(success => {{
                        if (success) {{
                            console.log('Spotify Player connected successfully.');
                        }} else {{
                            console.error('Failed to connect Spotify Player.');
                        }}
                    }});

                    document.getElementById('playPauseButton').addEventListener('click', () => {{
                        player.togglePlay().then(() => {{
                            console.log('Toggled play/pause');
                            const button = document.getElementById('playPauseButton');
                            if (button.innerHTML === 'Play') {{
                                button.innerHTML = 'Pause';
                            }} else {{
                                button.innerHTML = 'Play';
                            }}
                        }});
                    }});

                    document.getElementById('skipButton').addEventListener('click', () => {{
                        player.nextTrack().then(() => {{
                            console.log('Skipped to next track');
                        }});
                    }});

                    document.getElementById('volume').addEventListener('input', (event) => {{
                        const volume = event.target.value;
                        player.setVolume(volume).then(() => {{
                            console.log('Volume set to ' + volume);
                        }});
                    }});
                }};
            </script>
        """

        html(html_content, height=600)

    else:
        SONG_PLACEHOLDER.markdown("Upgrade to Spotify Premium for in-app playback.")
