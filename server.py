from flask import Flask, Response
import socket
import struct
import pickle
import cv2

app = Flask(__name__)

def receive_video_stream():
    # Create a socket to listen for incoming connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('192.168.7.12', 5050))  # Bind to a different port, e.g., 5050
    server_socket.listen(5)

    conn, addr = server_socket.accept()
    data = b""
    payload_size = struct.calcsize(">L")

    while True:
        # Receive the size of the data
        while len(data) < payload_size:
            data += conn.recv(8192)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        # Receive the actual image data
        while len(data) < msg_size:
            data += conn.recv(8192)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        # Deserialize the frame
        frame = pickle.loads(frame_data)

        # Encode the frame as JPEG and yield it for MJPEG streaming
        _, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(receive_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5151)  # Flask runs on port 5151
