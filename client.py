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

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.7.12', 5151))  # Replace with your server IP and port

while True:
    # Capture an image from the camera
    image = camera.get_image()

    # Convert image to string format (for serialization)
    image_str = pygame.image.tostring(image, 'RGB')

    # Serialize the image
    data = pickle.dumps(image_str)

    # Send the size of the data first
    client_socket.sendall(struct.pack(">L", len(data)) + data)

    time.sleep(0.05)  # Optional delay to reduce the load

# Clean up
camera.stop()
client_socket.close()
