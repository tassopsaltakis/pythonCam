# server.py
import cv2
import imagezmq

# Initialize the ImageHub (server) to receive the video stream
image_hub = imagezmq.ImageHub()

print("Server is waiting for incoming video streams...")

while True:
    # Receive a frame from the client
    client_name, frame = image_hub.recv_image()

    # Display the frame in a window
    cv2.imshow(f"Video Stream from {client_name}", frame)

    # Send acknowledgment back to the client
    image_hub.send_reply(b'OK')

    # If 'q' is pressed, quit the stream
    if cv2.waitKey(1) == ord('q'):
        break

cv2.destroyAllWindows()
