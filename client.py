import cv2
import imagezmq
import socket

def find_working_camera(max_tests=5):
    """
    Try camera indices from 0..max_tests-1 and return the first that
    can read a valid frame.
    """
    for i in range(max_tests):
        cap = cv2.VideoCapture(i)  # or cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Using camera index {i}")
                return cap
            cap.release()
    return None

def main():
    client_name = socket.gethostname()
    sender = imagezmq.ImageSender(connect_to="tcp://192.168.7.12:5555")

    cap = find_working_camera(max_tests=5)
    if not cap:
        print("Error: Could not find a working camera among indices 0..4.")
        return

    print(f"Client '{client_name}' started streaming video...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame from camera.")
                break

            # Send the frame to the server
            sender.send_image(client_name, frame)

            # (Optional) Show the frame locally
            cv2.imshow("Client Stream", frame)

            # Press 'q' to quit the client-side stream
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
