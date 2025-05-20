from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import rawpy
import imageio
import os
import sys
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

ffmpeg_path = os.path.join(base_path, "ffmpeg", "bin")
os.environ["PATH"] += os.pathsep + ffmpeg_path
import re
import platform
from pathlib import Path
from werkzeug.utils import secure_filename
from PIL import Image
import webbrowser
import threading
import tempfile

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

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp', 'arw'}

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    error = None
    if request.method == 'POST':
        url = request.form['url']
        format_choice = request.form.get('format', 'mp4')
        if url:
            try:
                download_video(url, format_choice)
                message = f"✅ {format_choice.upper()} downloaded successfully!"
            except Exception as e:
                cleaned_error = re.sub(r'\x1b\[[0-9;]*m', '', str(e))
                error = f"❌ {cleaned_error}"
    return render_template('index.html', message=message, error=error)

@app.route('/convert-image', methods=['GET', 'POST'])
def convert_image():
    if request.method == 'POST':
        files = request.files.getlist('image')
        target_format = request.form.get('format', '').lower()

        if not files or len(files) == 0:
            return render_template('convert_image.html', error="❌ No files selected.")
        elif len(files) > 1:
            return render_template('convert_image.html', error="❌ Only one image allowed for download preview.")

        file = files[0]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_in:
                    file.save(tmp_in.name)
                    input_path = tmp_in.name

                output_filename = f"{os.path.splitext(filename)[0]}.{target_format}"
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{target_format}") as tmp_out:
                    output_path = tmp_out.name

                file_ext = filename.rsplit('.', 1)[1].lower()

                if file_ext == 'arw':
                    with rawpy.imread(input_path) as raw:
                        rgb = raw.postprocess()
                        imageio.imwrite(output_path, rgb)
                else:
                    with Image.open(input_path) as img:
                        img = img.convert("RGB")
                        pillow_format = 'JPEG' if target_format == 'jpg' else target_format.upper()
                        img.save(output_path, format=pillow_format)

                if os.path.exists(input_path):
                    os.unlink(input_path)

                return send_file(output_path, as_attachment=True, download_name=output_filename)

            except Exception as e:
                return render_template('convert_image.html', error=f"❌ Error converting {filename}: {e}")

        else:
            return render_template('convert_image.html', error=f"❌ Invalid file type for {file.filename}")

    return render_template('convert_image.html')

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

def download_video(url, format_choice):
    output_template = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
    ydl_opts = {
        'outtmpl': output_template,
        'quiet': False,
        'verbose': True,
        'nocheckcertificate': True,
        'progress_hooks': [progress_hook]
    }

    if format_choice == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:  # mp4
        ydl_opts.update({
            'format': (
                'bestvideo[height<=1080][vcodec^=avc1]+bestaudio/best/'
                'bestvideo[height<=1080]+bestaudio/best'
            ),
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        })

    print(f"🔍 Downloading {format_choice.upper()} from: {url}")
    print(f"📁 Saving to: {DOWNLOAD_DIR}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        print(f"✅ Download completed: {info.get('title', 'Unknown Title')}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(debug=False, use_reloader=False)
