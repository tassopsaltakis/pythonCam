# server.py
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
import base64

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('video_frame')
def handle_video_frame(data):
    # Receive base64 encoded frame from client
    frame_data = base64.b64decode(data)
    np_arr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Display frame on the server (for debug purposes)
    cv2.imshow("Server Stream", frame)
    cv2.waitKey(1)

    # Emit frame back to the webpage
    emit('server_video', data)


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
