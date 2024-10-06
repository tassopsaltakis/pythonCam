import pygame
import pygame.camera
import socket
import struct
import pickle
import time

# Initialize pygame camera
pygame.camera.init()

# List available cameras
cameras = pygame.camera.list_cameras()
if not cameras:
    print("No camera found!")
    exit()

# Start the camera
camera = pygame.camera.Camera(cameras[0], (640, 480))
camera.start()

# Create a socket to send video data
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.7.12', 7854))  # Send video to port 7854

while True:
    # Capture an image from the camera
    if camera.query_image():
        image = camera.get_image()

        # Serialize the pygame surface (image) using pickle
        data = pickle.dumps(image)

        # Send the size of the data first (so the server knows how much to receive)
        message_size = struct.pack(">L", len(data))
        client_socket.sendall(message_size + data)
    else:
        print("No frame captured")

    time.sleep(0.05)  # Optional delay to reduce the load

# Clean up
camera.stop()
client_socket.close()
