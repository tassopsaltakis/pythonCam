# client.py

import cv2
import imagezmq
import socket

def main():
    # Unique client name (e.g., hostname)
    client_name = socket.gethostname()

    # Connect to the server
    sender = imagezmq.ImageSender(connect_to="tcp://<SERVER_IP>:5555")
    # Replace <SERVER_IP> with the actual IP or hostname of your server machine

    # Open default camera (index=0). Adjust if you need a different camera.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print(f"Client '{client_name}' is sending frames...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read from camera.")
                break

            # Send frame. The client will block until server replies b'OK'.
            sender.send_image(client_name, frame)
    finally:
        cap.release()

if __name__ == "__main__":
    main()
