import requests
from base64 import b64encode
from dotenv import find_dotenv, load_dotenv
from flask import Flask, Response, jsonify, request
import threading
import time

# Load environment variables
load_dotenv(find_dotenv())

# Define base-64 encoded images
with open("api/base64/placeholder_scan_code.txt") as f:
    B64_PLACEHOLDER_SCAN_CODE = f.read()
with open("api/base64/placeholder_image.txt") as f:
    B64_PLACEHOLDER_IMAGE = f.read()
with open("api/base64/spotify_logo.txt") as f:
    B64_SPOTIFY_LOGO = f.read()

# Function to periodically update the currently playing track
def update_current_track():
    while True:
        # Make a request to the Spotify API to get the currently playing track
        # Update the currently playing track information
        
        # For demonstration purposes, I'll just sleep for 10 seconds
        time.sleep(10)

# Start a new thread to run the update_current_track function
update_thread = threading.Thread(target=update_current_track)
update_thread.daemon = True
update_thread.start()

def get_token():
    """Get a new access token"""
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": getenv("REFRESH_TOKEN"),
            "client_id": getenv("CLIENT_ID"),
            "client_secret": getenv("CLIENT_SECRET"),
        },
    )
    try:
        return r.json()["access_token"]
    except BaseException:
        raise Exception(r.json())


def spotify_request(endpoint):
    """Make a request to the specified endpoint"""
    r = requests.get(
        f"https://api.spotify.com/v1/{endpoint}",
        headers={"Authorization": f"Bearer {get_token()}"},
    )
    return {} if r.status_code == 204 else r.json()


def generate_bars(bar_count, rainbow):
    """Build the HTML/CSS for the bars to be injected"""
    bars = "".join(["<div class='bar'></div>" for _ in range(bar_count)])
    css = "<style>"
    if rainbow and rainbow != "false" and rainbow != "0":
        css += ".bar-container { animation-duration: 2s; }"
    spectrum = [
        "#ffffff", "#f4f3f5", "#eae8eb", "#dfdce1", "#d5d2d7", "#cac6cd",
        "#c0bcc3", "#b5b0ba", "#aba6b0", "#a09ca7", "#96929d", "#8b8793",
        "#817d89", "#76737f", "#6c6976", "#61606c", "#575763", "#4c4a59",
        "#42404f", "#373648", "#2d2b3e", "#232235", "#18162b", "#0e0c21",
        "#030216", "#000000", "#030216", "#0e0c21", "#18162b", "#232235",
        "#2d2b3e", "#373648", "#42404f", "#4c4a59", "#575763", "#61606c",
        "#6c6976", "#76737f", "#817d89", "#8b8793", "#96929d", "#a09ca7",
        "#aba6b0", "#b5b0ba", "#c0bcc3", "#cac6cd", "#d5d2d7", "#dfdce1",
        "#eae8eb", "#f4f3f5", "#ffffff"
    ]
    for i in range(bar_count):
        css += f""".bar:nth-child({i + 1}) {{
                animation-duration: {randint(500, 750)}ms;
                background: {spectrum[i] if rainbow and rainbow != 'false' and rainbow != '0' else '#9524D2'};
            }}"""
    return f"{bars}{css}</style>"


def load_image_base64(url):
    """Get the base-64 encoded image from url"""
    resposne = requests.get(url)
    return b64encode(resposne.content).decode("ascii")


def get_scan_code(spotify_uri):
    """Get the track code for a song"""
    return load_image_base64(
        f"https://scannables.scdn.co/uri/plain/png/000000/white/640/{spotify_uri}"
    )


def make_svg(spin, scan, theme, rainbow):
    """Render the HTML template with variables"""
    data = spotify_request("me/player/currently-playing")
    if data:
        item = data["item"]
    else:
        item = spotify_request("me/player/recently-played?limit=1")["items"][0]["track"]

    if item["album"]["images"] == []:
        image = B64_PLACEHOLDER_IMAGE
    else:
        image = load_image_base64(item["album"]["images"][1]["url"])

    if scan and scan != "false" and scan != "0":
        bar_count = 10
        scan_code = get_scan_code(item["uri"])
    else:
        bar_count = 12
        scan_code = None

    return render_template(
        "index.html",
        **{
            "bars": generate_bars(bar_count, rainbow),
            "artist": item["artists"][0]["name"].replace("&", "&amp;"),
            "song": item["name"].replace("&", "&amp;"),
            "image": image,
            "scan_code": scan_code if scan_code != "" else B64_PLACEHOLDER_SCAN_CODE,
            "theme": theme,
            "spin": spin,
            "logo": B64_SPOTIFY_LOGO,
        },
    )


app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    resp = Response(
        make_svg(
            request.args.get("spin"),
            request.args.get("scan"),
            request.args.get("theme"),
            request.args.get("rainbow"),
        ),
        mimetype="image/svg+xml",
    )
    resp.headers["Cache-Control"] = "s-maxage=1"
    return resp


if __name__ == "__main__":
    app.run(debug=True)
