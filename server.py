from flask import Flask, Response
import socket
import struct
import pickle
import pygame
import time

app = Flask(__name__)


def receive_video_stream():
    # Create a socket to listen for incoming connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('192.168.7.12', 5151))  # Replace with your server IP
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
        frame_str = pickle.loads(frame_data)

        # Convert string back to image format
        image = pygame.image.fromstring(frame_str, (640, 480), 'RGB')

        # Convert the image to JPEG format for MJPEG streaming
        jpeg_image = pygame.image.tostring(image, "RGB")

        # Yield the frame as MJPEG to the web client
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg_image + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(receive_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
