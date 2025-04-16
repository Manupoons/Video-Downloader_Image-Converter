from flask import Flask, render_template, request
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_DIR = './downloads'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        if url:
            try:
                downlaod_video(url)
                return f"Video downloaded successfully! <a href='/'>Go back</a>"
            except Exception as e:
                return f"An error occurred: {str(e)} <a href='/'>Go back</a>"
    return render_template('index.html')

def downlaod_video(url):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
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