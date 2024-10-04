import cv2
import socket
import struct
import pickle

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.7.12', 5151))

# Set up the camera
camera = cv2.VideoCapture(0)  # 0 is usually the default camera

while True:
    ret, frame = camera.read()
    if not ret:
        break

    # Serialize the frame
    data = pickle.dumps(frame)
    # Send the size of the data first
    client_socket.sendall(struct.pack(">L", len(data)) + data)

camera.release()
client_socket.close()
