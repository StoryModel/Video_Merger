# Local Video Merger

A private, local web app for merging two or more videos into one downloadable MP4 file using your installed FFmpeg.

## Requirements

- Python 3.9 or newer
- FFmpeg installed and available from terminal/command prompt

Check FFmpeg:

```bash
ffmpeg -version
```

## Setup

Open a terminal inside this folder and run:

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

### macOS / Linux

```bash
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

Then open this in your browser:

```text
http://127.0.0.1:5000
```

## How to use

1. Click **Choose videos** or drag videos into the box.
2. Add more than 2 videos if needed.
3. Use ↑ and ↓ to arrange order.
4. Click **Merge videos**.
5. Click **Download complete video**.

## Notes

- Files are processed locally on your device.
- The app creates `uploads` and `outputs` folders.
- Output is MP4 using H.264 video and AAC audio.
