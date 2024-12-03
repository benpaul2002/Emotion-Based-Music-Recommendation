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
import streamlit.components.v1 as components

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

def get_spotify_song(sp, user_product, SONG_PLACEHOLDER, song_metadata_list):
    first_song = song_metadata_list[0]
    song_uri = first_song["uri"]
    album_art = first_song["album_art"]
    track = sp.track(song_uri)
    song_name = track['name']
    artist_names = ', '.join(artist['name'] for artist in track['artists'])
    duration_ms = track['duration_ms']

    SONG_PLACEHOLDER.empty()
    SONG_PLACEHOLDER.markdown(
        f"""
        **{song_name}** by {artist_names}
        [Play on Spotify Web Player]({song_uri})
        """
    )

    if user_product == "premium":
        try:
            with open("access_token.txt", "r") as f:
                token = f.read().strip()
        except FileNotFoundError:
            st.warning("Log in to Spotify to proceed.")
            return
        
        html_content = f"""
            <div id="player-container">
                <div style="width: 100%; max-width: 500px; margin: 20px auto; padding: 20px; border-radius: 10px; background-color: #222; color: white; text-align: center; font-family: Arial, sans-serif;">
                    <h3 id="trackInfo" style="margin-bottom: 20px;">{song_name} - {artist_names}</h3>

                    <div id="coverArtContainer" style="width: 100%; height: 250px; background-color: #333; border-radius: 10px; margin-bottom: 20px;">
                        <img id="coverArt" src="{album_art}" alt="Track Cover Art" style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px;">
                    </div>

                    <div id="playbackStatus" style="margin: 10px 0; color: #1db954; font-weight: bold;"></div>

                    <div style="display: flex; justify-content: space-evenly; margin-top: 20px;">
                        <button id="playPauseButton" style="background-color: #1db954; border: none; color: white; padding: 15px 30px; font-size: 16px; border-radius: 5px; cursor: pointer;">Pause</button>
                        <button id="skipButton" style="background-color: #1db954; border: none; color: white; padding: 15px 30px; font-size: 16px; border-radius: 5px; cursor: pointer;">Next</button>
                    </div>

                    <div style="margin-top: 20px;">
                        <label for="volume" style="color: white; font-size: 14px; margin-right: 10px;">Volume</label>
                        <input type="range" id="volume" name="volume" min="0" max="1" step="0.01" value="0.5" style="width: 100%; max-width: 300px;"/>
                    </div>
                </div>
            </div>

            <script src="https://sdk.scdn.co/spotify-player.js"></script>
            <script>
                if (!window.playerInitialized) {{
                    window.onSpotifyWebPlaybackSDKReady = () => {{
                        const token = '{token}';
                        const songUris = {[song["uri"] for song in song_metadata_list]};
                        const token_str = "Bearer " + token;
                        const duration = {duration_ms};
                        let playTimer = null;
                        let startTime = null;
                        let isPaused = false;
                        let remainingTime = duration;
                        let currentTrackIndex = 0;
                        let spotifyDeviceId = null;

                        const player = new Spotify.Player({{
                            name: 'Streamlit Music Player',
                            getOAuthToken: cb => cb(token),
                            volume: 0.5
                        }});

                        player.addListener('player_state_changed', state => {{
                            if (state) {{
                                const currentTrack = state.track_window.current_track;
                                const trackInfo = document.getElementById('trackInfo');
                                const coverArt = document.getElementById('coverArt');
                                trackInfo.innerHTML = `${{currentTrack.name}} - ${{currentTrack.artists.map(artist => artist.name).join(', ')}}`;
                                coverArt.src = currentTrack.album.images[0].url;
                            }}
                        }});

                        function startPlaybackTimer() {{
                            if (playTimer) clearTimeout(playTimer);
                            startTime = Date.now();
                            playTimer = setTimeout(() => {{ 
                                document.getElementById('playPauseButton').innerHTML = 'Play';
                            }}, remainingTime);
                        }}

                        function pausePlaybackTimer() {{
                            if (playTimer) {{
                                clearTimeout(playTimer);
                                remainingTime = remainingTime - (Date.now() - startTime);
                            }}
                        }}

                        player.addListener('ready', ({{ device_id }}) => {{
                            console.log('Spotify Player ready with Device ID:', device_id);
                            spotifyDeviceId = device_id;

                            // Play the first track
                            playTrack(device_id, songUris[currentTrackIndex]);

                            // Add the rest of the tracks to the queue
                            for (let i = 1; i < songUris.length; i++) {{
                                addToQueue(device_id, songUris[i]);
                            }}
                        }});

                        function playTrack(device_id, uri) {{
                            fetch('https://api.spotify.com/v1/me/player/play?device_id=' + device_id, {{
                                method: 'PUT',
                                headers: {{
                                    'Authorization': token_str,
                                    'Content-Type': 'application/json',
                                }},
                                body: JSON.stringify({{ uris: [uri] }})
                            }})
                            .then(response => {{
                                if (response.ok) {{
                                    console.log('Track is now playing!');
                                    startPlaybackTimer();
                                }}
                            }})
                            .catch(error => console.error('Error while playing track:', error));
                        }}

                        function addToQueue(device_id, uri) {{
                            fetch('https://api.spotify.com/v1/me/player/queue?uri=' + encodeURIComponent(uri) + '&device_id=' + device_id, {{
                                method: 'POST',
                                headers: {{
                                    'Authorization': token_str,
                                }}
                            }})
                            .then(response => {{
                                if (response.ok) {{
                                    console.log('Track added to queue');
                                }}
                            }})
                            .catch(error => console.error('Error while adding track to queue:', error));
                        }}

                        player.connect().then(success => {{
                            if (success) {{
                                console.log('Spotify Player connected successfully.');
                            }} else {{
                                console.error('Failed to connect Spotify Player.');
                            }}
                        }});

                        document.getElementById('playPauseButton').addEventListener('click', () => {{
                            player.togglePlay().then(() => {{
                                const button = document.getElementById('playPauseButton');
                                if (button.innerHTML === 'Play') {{
                                    button.innerHTML = 'Pause';
                                    document.getElementById('playbackStatus').innerHTML = '';
                                    if (isPaused) {{
                                        startPlaybackTimer();
                                    }}
                                    isPaused = false;
                                }} else {{
                                    button.innerHTML = 'Play';
                                    pausePlaybackTimer();
                                    isPaused = true;
                                }}
                            }});
                        }});

                        document.getElementById('skipButton').addEventListener('click', () => {{
                            player.nextTrack().then(() => {{
                                console.log('Skipped to next track');
                                document.getElementById('playbackStatus').innerHTML = '';
                                if (playTimer) clearTimeout(playTimer);
                            }});
                        }});

                        document.getElementById('volume').addEventListener('input', (event) => {{
                            const volume = event.target.value;
                            player.setVolume(volume).then(() => {{
                                console.log('Volume set to ' + volume);
                            }});
                        }});
                    }};
                    window.playerInitialized = true;
                    window.player = player;
                }}
                else {{
                    // If player exists, just update the track
                    const uri = '{song_uri}';
                    if (window.player) {{
                        window.player.activateElement();
                        fetch('https://api.spotify.com/v1/me/player/play?device_id=' + spotifyDeviceId, {{
                            method: 'PUT',
                            headers: {{
                                'Authorization': 'Bearer {token}',
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{ uris: [uri] }})
                        }});
                    }}
                }}
            </script>
        """

        SONG_PLACEHOLDER.empty()
        with SONG_PLACEHOLDER:
            components.html(
                html_content,
                height=600,
                scrolling=False
            )

    else:
        SONG_PLACEHOLDER.markdown("Upgrade to Spotify Premium for in-app playback.")
