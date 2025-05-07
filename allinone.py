#!/usr/bin/env python3
import os
import threading
import time
from flask import Flask, Response, send_from_directory, render_template_string
import cv2

# ───── CONFIG ───────────────────────────────────────────────────────────────
CLIP_DIR = os.path.join(os.path.dirname(__file__), "clips")
SEGMENT_DURATION = 30  # seconds per clip
MAX_CLIPS = 10         # keep at most this many

os.makedirs(CLIP_DIR, exist_ok=True)

# shared latest frame
global_frame = None

# ───── CAMERA CAPTURE THREAD ─────────────────────────────────────────────────
def capture_loop():
    global global_frame
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera")
    try:
        while True:
            ret, frame = cap.read()
            if ret:
                global_frame = frame.copy()
            else:
                time.sleep(0.01)
    finally:
        cap.release()

# ───── RECORDER THREAD ───────────────────────────────────────────────────────
def recorder_loop():
    # wait for first frame
    while global_frame is None:
        time.sleep(0.1)

    # probe resolution & fps
    probe = cv2.VideoCapture(0)
    width  = int(probe.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = probe.get(cv2.CAP_PROP_FPS) or 25.0
    probe.release()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    while True:
        # prepare new filename
        ts = time.strftime("%Y%m%d-%H%M%S")
        out_path = os.path.join(CLIP_DIR, f"clip-{ts}.mp4")

        # record for SEGMENT_DURATION
        writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
        t0 = time.time()
        while time.time() - t0 < SEGMENT_DURATION:
            if global_frame is not None:
                writer.write(global_frame)
            time.sleep(1.0 / fps)
        writer.release()

        # cleanup oldest if > MAX_CLIPS
        files = sorted(
            os.listdir(CLIP_DIR),
            key=lambda f: os.path.getmtime(os.path.join(CLIP_DIR, f))
        )
        while len(files) > MAX_CLIPS:
            old = files.pop(0)
            try:
                os.remove(os.path.join(CLIP_DIR, old))
                print(f"[-] Removed old clip: {old}", flush=True)
            except Exception as e:
                print(f"[!] Could not remove {old}: {e}", flush=True)

# ───── FLASK APP ────────────────────────────────────────────────────────────
app = Flask(__name__)

def gen_mjpeg():
    """Yield MJPEG frames from the latest camera frame."""
    global global_frame
    while True:
        if global_frame is None:
            time.sleep(0.01)
            continue
        _, buf = cv2.imencode('.jpg', global_frame)
        frame = buf.tobytes()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame +
            b'\r\n'
        )
        time.sleep(0.01)

@app.route('/video_feed')
def video_feed():
    return Response(gen_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/clips/<path:filename>')
def clips_static(filename):
    return send_from_directory(CLIP_DIR, filename)

@app.route('/')
def index():
    files = sorted(
        os.listdir(CLIP_DIR),
        key=lambda f: os.path.getmtime(os.path.join(CLIP_DIR, f)),
        reverse=True
    )
    html = """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>PythonCam</title>
    </head>
    <body>
      <h1>Live Feed</h1>
      <img src="/video_feed" style="max-width:100%;">

      <h2>Clip Browser</h2>
      {% if files %}
        <video id="clipPlayer" controls width="640">
          <source src="/clips/{{ files[0] }}" type="video/mp4">
          Your browser does not support the video tag.
        </video>
        <br>
        <select id="clipSelect">
          {% for f in files %}
            <option value="/clips/{{ f }}">{{ f }}</option>
          {% endfor %}
        </select>

        <script>
        const select = document.getElementById('clipSelect');
        const player = document.getElementById('clipPlayer');
        select.addEventListener('change', () => {
          player.src = select.value;
          player.load();
          player.play();
        });
        </script>
      {% else %}
        <p>No clips recorded yet. Check back in 30 s!</p>
      {% endif %}
    </body>
    </html>
    """
    return render_template_string(html, files=files)

# ───── ENTRY POINT ───────────────────────────────────────────────────────────
def main():
    threading.Thread(target=capture_loop, daemon=True).start()
    threading.Thread(target=recorder_loop, daemon=True).start()

    app.run(
        host='0.0.0.0',
        port=8000,
        threaded=True,
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    main()
