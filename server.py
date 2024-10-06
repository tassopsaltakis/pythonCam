import socket
import struct
import pickle
import numpy as np
import cv2


def receive_video_stream():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('192.168.7.12', 7854))
    server_socket.listen(5)

    conn, addr = server_socket.accept()
    data = b""
    payload_size = struct.calcsize(">L")

    while True:
        try:
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

            # Deserialize the frame
            frame = pickle.loads(frame_data)

            if frame is None:
                print("Error: Received frame is None")
                continue

            # Check if the frame is a valid NumPy array
            if not isinstance(frame, np.ndarray):
                print("Error: Frame is not a valid NumPy array")
                continue

            # Encode the frame as JPEG and yield it for MJPEG streaming
            _, jpeg = cv2.imencode('.jpg', frame)
            frame = jpeg.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

        except Exception as e:
            print(f"Error decoding frame: {e}")
            continue
