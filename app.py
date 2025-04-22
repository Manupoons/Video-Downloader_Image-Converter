from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import re
import platform
from pathlib import Path

app = Flask(__name__)

download_progress = {'percent': 0}

# Ensure the appropriate Downloads directory exists
if platform.system() == "Windows":
    DOWNLOAD_DIR = str(Path(os.environ['USERPROFILE']) / "Downloads")
elif platform.system() == "Darwin":  # macOS
    DOWNLOAD_DIR = str(Path.home() / "Downloads")
else:  # Linux and others
    DOWNLOAD_DIR = str(Path.home() / "Downloads")

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
                download_video(url)
                message = "✅ Video downloaded successfully!"
            except Exception as e:
                cleaned_error = re.sub(r'\x1b\[[0-9;]*m', '', str(e))
                error = f"❌ {cleaned_error}"
    return render_template('index.html', message=message, error=error)

@app.route('/progress', methods=['GET'])
def progress():
    return jsonify(download_progress)

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100 if d.get('total_bytes') else 0
        download_progress['percent'] = percent
        print(f"Downloading: {percent:.2f}%")
    elif d['status'] == 'finished':
        download_progress['percent'] = 100
        print("Download finished:", d.get('filename'))

def download_video(url):
    ydl_opts = {
        'format': (
            'bestvideo[height<=1080][vcodec^=avc1]+bestaudio/best/'
            'bestvideo[height<=1080]+bestaudio/best'
        ),
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'audioquality': 0,
        'quiet': False,             
        'verbose': True,            
        'nocheckcertificate': True,
        'progress_hooks': [progress_hook],
        'postprocessors': [         
            {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  
            }
        ]
    }

    print(f"🔍 Downloading from: {url}")
    print(f"📁 Saving to: {DOWNLOAD_DIR}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        print(f"✅ Download completed: {info.get('title', 'Unknown Title')}")

if __name__ == '__main__':
    app.run(debug=True)
