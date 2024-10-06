from flask import Flask, Response
import socket
import struct
import pickle
import pygame
import numpy as np
import cv2

app = Flask(__name__)

def receive_video_stream():
    # Create a socket to receive video data
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('192.168.7.12', 7854))  # Ensure the port matches the client
    server_socket.listen(5)

    conn, addr = server_socket.accept()
    data = b""
    payload_size = struct.calcsize(">L")

    while True:
        # Receive the size of the data
        while len(data) < payload_size:
            data += conn.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        # Receive the actual image data
        while len(data) < msg_size:
            data += conn.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        try:
            # Deserialize the image using pickle
            image = pickle.loads(frame_data)

            # Convert the pygame surface to a NumPy array
            image_np = pygame.surfarray.array3d(image)  # Convert pygame surface to NumPy array
            image_np = np.rot90(image_np)  # Adjust orientation
            image_np = np.flipud(image_np)  # Flip vertically if needed
            image_np = np.ascontiguousarray(image_np[:, :, ::-1])  # Convert RGB to BGR for OpenCV

            # Encode the frame as JPEG for MJPEG streaming
            _, jpeg = cv2.imencode('.jpg', image_np)
            frame = jpeg.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except Exception as e:
            print(f"Error decoding frame: {e}")
            continue

@app.route('/video_feed')
def video_feed():
    return Response(receive_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5151)
