import pygame
import pygame.camera
import socket
import struct
import pickle
import time
import numpy as np

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

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.7.12', 7854))  # Send video to port 7854

while True:
    # Capture an image from the camera
    if camera.query_image():
        image = camera.get_image()

        # Convert the pygame surface to a NumPy array
        image_np = pygame.surfarray.array3d(image)  # Convert pygame surface to NumPy array
        image_np = np.rot90(image_np)  # Rotate if needed (adjust based on orientation)
        image_np = np.flipud(image_np)  # Fix axis to match orientation
        image_np = np.ascontiguousarray(image_np)  # Ensure the array is contiguous for OpenCV

        # Serialize the image
        data = pickle.dumps(image_np)

        # Send the size of the data first
        client_socket.sendall(struct.pack(">L", len(data)) + data)
    else:
        print("No frame captured")

    time.sleep(0.05)  # Optional delay to reduce the load

# Clean up
camera.stop()
client_socket.close()
