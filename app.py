from flask import Flask, render_template, request, jsonify
import yt_dlp
import rawpy
import imageio
import os
import re
import platform
from pathlib import Path
from werkzeug.utils import secure_filename
from PIL import Image

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

IMAGE_UPLOAD_FOLDER = os.path.join(DOWNLOAD_DIR, 'converted_images')
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)
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
    messages = []
    errors = []
    if request.method == 'POST':
        files = request.files.getlist('image')
        target_format = request.form.get('format', '').lower()

        if not files or len(files) == 0:
            errors.append("❌ No files selected.")
        elif len(files) > 10:
            errors.append("❌ You can upload up to 10 images at a time.")
        else:
            for file in files:
                if file and allowed_file(file.filename):
                    try:
                        filename = secure_filename(file.filename)
                        input_path = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
                        file.save(input_path)

                        output_filename = f"{os.path.splitext(filename)[0]}.{target_format}"
                        output_path = os.path.join(IMAGE_UPLOAD_FOLDER, output_filename)

                        file_ext = filename.rsplit('.', 1)[1].lower()

                        if file_ext == 'arw':
                            with rawpy.imread(input_path) as raw:
                                rgb = raw.postprocess()
                                imageio.imwrite(output_path, rgb)
                        else:
                            with Image.open(input_path) as img:
                                img = img.convert("RGB")
                                img.save(output_path, format=target_format.upper())

                        messages.append(f"✅ {filename} → {output_filename}")
                    except Exception as e:
                        errors.append(f"❌ Error converting {filename}: {e}")
                else:
                    errors.append(f"❌ Invalid file type for {file.filename}")

    return render_template('convert_image.html', message="<br>".join(messages), error="<br>".join(errors))

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

if __name__ == '__main__':
    app.run(debug=True)
