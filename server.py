import os
import shutil
import subprocess
import uuid
from pathlib import Path
from flask import Flask, request, send_file, jsonify, render_template_string
from werkzeug.utils import secure_filename

APP_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = APP_DIR / "uploads"
OUTPUT_DIR = APP_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024 * 1024  # 20 GB

HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")


def ffmpeg_exists():
    return shutil.which("ffmpeg") is not None


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/merge", methods=["POST"])
def merge_videos():
    if not ffmpeg_exists():
        return jsonify({"error": "FFmpeg was not found. Make sure ffmpeg is installed and available in PATH."}), 500

    files = request.files.getlist("videos")
    if len(files) < 2:
        return jsonify({"error": "Please upload at least 2 videos."}), 400

    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    try:
        for index, file in enumerate(files):
            if not file.filename:
                continue
            name = secure_filename(file.filename)
            ext = Path(name).suffix.lower() or ".mp4"
            path = job_dir / f"clip_{index:03d}{ext}"
            file.save(path)
            saved_files.append(path)

        if len(saved_files) < 2:
            return jsonify({"error": "Please upload at least 2 valid video files."}), 400

        normalized_files = []
        for i, input_path in enumerate(saved_files):
            normalized_path = job_dir / f"normalized_{i:03d}.mp4"
            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1",
                "-r", "30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                str(normalized_path)
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                return jsonify({"error": f"Could not process {input_path.name}.", "details": result.stderr[-2000:]}), 500
            normalized_files.append(normalized_path)

        concat_list = job_dir / "concat.txt"
        with concat_list.open("w", encoding="utf-8") as f:
            for path in normalized_files:
                safe_path = str(path).replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        output_path = OUTPUT_DIR / f"merged_{job_id}.mp4"
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c", "copy", str(output_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return jsonify({"error": "Could not merge videos.", "details": result.stderr[-2000:]}), 500

        return jsonify({
            "message": "Videos merged successfully.",
            "download_url": f"/download/{output_path.name}",
            "filename": output_path.name
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/download/<filename>")
def download(filename):
    path = OUTPUT_DIR / secure_filename(filename)
    if not path.exists():
        return jsonify({"error": "File not found."}), 404
    return send_file(path, as_attachment=True, download_name="merged_video.mp4")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
