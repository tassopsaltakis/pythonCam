# client.py
import cv2
import imagezmq

# Initialize the ImageSender (client)
sender = imagezmq.ImageSender(connect_to="tcp://192.168.7.12:5555")

# Open the webcam (0 is usually the default webcam)
video_capture = cv2.VideoCapture(0)

print("Client started streaming video...")

while True:
    # Capture frame-by-frame from the webcam
    ret, frame = video_capture.read()

    if not ret:
        print("Failed to capture frame.")
        break

    # Send the frame to the server
    sender.send_image('client_1', frame)

    # Display the frame on the client side as well (optional)
    cv2.imshow("Client Stream", frame)

    # Press 'q' to quit the client-side stream
    if cv2.waitKey(1) == ord('q'):
        break

# Release the webcam and close all windows
video_capture.release()
cv2.destroyAllWindows()
