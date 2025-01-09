import cv2
import imagezmq
import socket


def try_open_facetime_cam():
    """
    Attempt to open the built-in FaceTime camera on macOS by name first,
    then fall back to index 0 if that fails.
    """
    # Common names for the built-in camera
    possible_names = [
        "FaceTime HD Camera (Built-in)",
        "FaceTime HD Camera",
        # Add more variants if needed
    ]

    # Try each name with the AVFoundation backend
    for name in possible_names:
        cap = cv2.VideoCapture(name, cv2.CAP_AVFOUNDATION)
        if cap.isOpened():
            return cap

    # Fall back to using index=0 with AVFoundation
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if cap.isOpened():
        return cap

    # If none worked, return None
    return None


def main():
    client_name = socket.gethostname()
    sender = imagezmq.ImageSender(connect_to="tcp://192.168.7.176:5555")

    cap = try_open_facetime_cam()
    if not cap or not cap.isOpened():
        print("Error: Could not open the built-in FaceTime camera.")
        exit(1)

    print(f"Client '{client_name}' started streaming from the built-in FaceTime camera...")

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
