# client.py
import cv2
import imagezmq
import socket

# Grab the machine's hostname as the client name
client_name = socket.gethostname()

# Initialize the ImageSender (client) - change IP as needed
sender = imagezmq.ImageSender(connect_to="tcp://192.168.7.176:5555")

# Attempt to open the default camera (index=0)
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    print("Error: Could not open default camera (index 0). Make sure a camera is connected.")
    exit(1)

print(f"Client '{client_name}' started streaming video...")

try:
    while True:
        # Read a frame from the webcam
        ret, frame = video_capture.read()

        if not ret:
            print("Failed to capture frame from default camera.")
            break

        # Send the frame to the server
        sender.send_image(client_name, frame)

        # (Optional) Display the frame locally
        cv2.imshow("Client Stream", frame)

        # Press 'q' to quit the client-side stream
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    # Release resources
    video_capture.release()
    cv2.destroyAllWindows()
