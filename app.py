from flask import Flask, render_template, request
import yt_dlp
import os
import re
import platform
from pathlib import Path

app = Flask(__name__)

# Determine the appropriate Downloads directory
if platform.system() == "Windows":
    DOWNLOAD_DIR = str(Path(os.environ['USERPROFILE']) / "Downloads")
elif platform.system() == "Darwin":  # macOS
    DOWNLOAD_DIR = str(Path.home() / "Downloads")
else:  # Linux and others
    DOWNLOAD_DIR = str(Path.home() / "Downloads")

# Ensure the download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    error = None
    if request.method == 'POST':
        url = request.form['url']
        if url:
            try:
                downlaod_video(url)
                message = "✅ Video downloaded successfully!"
            except Exception as e:
                # Remove ANSI color codes
                cleaned_error = re.sub(r'\x1b\[[0-9;]*m', '', str(e))
                error = f"❌ {cleaned_error}"
    return render_template('index.html', message=message, error=error)

def downlaod_video(url):
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',  # MP4 format (widely supported)
        'audioquality': 0,  # Best audio quality
        'quiet': True,
        'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == '__main__':
    app.run(debug=True)
