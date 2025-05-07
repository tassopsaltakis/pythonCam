#!/usr/bin/env python3
import os
import threading
import time
import subprocess

from flask import Flask, Response, send_from_directory, render_template_string
import cv2

# ───── CONFIG ───────────────────────────────────────────────────────────────
# Fill in your ZeroTier network ID here:
ZEROTIER_NETWORK_ID = "YOUR_NETWORK_ID"

# Where to dump 30 s WebM clips
CLIP_DIR = os.path.join(os.path.dirname(__file__), "clips")
SEGMENT_DURATION = 30  # seconds per clip
MAX_CLIPS = 10         # keep at most this many

os.makedirs(CLIP_DIR, exist_ok=True)

# shared latest frame
global_frame = None

# ───── ZERO­TIER CHECK ───────────────────────────────────────────────────────
def ensure_zerotier(network_id: str):
    """
    Check if the system is online to ZeroTier and joined to network_id;
    if not, join it once.
    """
    try:
        info = subprocess.check_output(
            ["zerotier-cli", "info"], text=True
        )
    except subprocess.CalledProcessError:
        print("[!] zerotier-cli info failed; is zerotier-one running?")
        return

    # look for "200 info <node_id> ONLINE"
    if "ONLINE" in info.upper():
        nets = subprocess.check_output(
            ["zerotier-cli", "listnetworks"], text=True
        )
        if network_id in nets:
            print(f"[+] Already joined ZeroTier network {network_id}")
        else:
            print(f"[+] Joining ZeroTier network {network_id}…")
            subprocess.run(["zerotier-cli", "join", network_id])
            time.sleep(3)  # give it a moment to connect
    else:
        print("[!] ZeroTier not ONLINE. Check service status.")


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

    # probe camera for resolution & fps
    probe = cv2.VideoCapture(0)
    width  = int(probe.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = probe.get(cv2.CAP_PROP_FPS) or 25.0
    probe.release()

    # WebM/VP8 encoding
    fourcc = cv2.VideoWriter_fourcc(*'VP80')

    while True:
        # build filename
        ts = time.strftime("%Y%m%d-%H%M%S")
        out_path = os.path.join(CLIP_DIR, f"clip-{ts}.webm")

        # record SEGMENT_DURATION seconds
        writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
        t0 = time.time()
        while time.time() - t0 < SEGMENT_DURATION:
            if global_frame is not None:
                writer.write(global_frame)
            time.sleep(1.0 / fps)
        writer.release()

        # cleanup oldest if we have more than MAX_CLIPS
        files = sorted(
            [f for f in os.listdir(CLIP_DIR) if f.endswith('.webm')],
            key=lambda f: os.path.getmtime(os.path.join(CLIP_DIR, f))
        )
        while len(files) > MAX_CLIPS:
            old = files.pop(0)
            try:
                os.remove(os.path.join(CLIP_DIR, old))
                print(f"[-] Removed old clip: {old}", flush=True)
            except Exception as e:
                print(f"[!] Failed to remove {old}: {e}", flush=True)


# ───── FLASK SERVER ─────────────────────────────────────────────────────────
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
    return send_from_directory(CLIP_DIR, filename, mimetype='video/webm')

@app.route('/')
def index():
    files = sorted(
        [f for f in os.listdir(CLIP_DIR) if f.endswith('.webm')],
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
          <source id="clipSource" src="/clips/{{ files[0] }}" type="video/webm">
          Your browser does not support HTML5 video.
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
          const source = document.getElementById('clipSource');
          select.addEventListener('change', () => {
            source.src = select.value;
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
    # 1) Ensure we're on the ZeroTier network
    ensure_zerotier(ZEROTIER_NETWORK_ID)

    # 2) Start camera capture and recorder threads
    threading.Thread(target=capture_loop, daemon=True).start()
    threading.Thread(target=recorder_loop, daemon=True).start()

    # 3) Launch Flask (no reloader so there's only one process)
    app.run(
        host='0.0.0.0',
        port=8000,
        threaded=True,
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    main()
