import cv2
import imagezmq
import zmq
from tkinter import *
from PIL import Image, ImageTk
import threading
import time

def main():
    print("Starting Single-Host Server on a single IP...")

    # 1) Bind specifically to one IP, e.g. 192.168.1.50
    #    Adjust to match your server machine’s network IP.
    SERVER_IP = "192.168.192.127"
    PORT = "5555"

    try:
        # Only listen on 192.168.1.50, not * (all interfaces).
        address = f"tcp://{SERVER_IP}:{PORT}"
        image_hub = imagezmq.ImageHub(open_port=address)
        # Avoid blocking forever
        image_hub.zmq_socket.setsockopt(zmq.RCVTIMEO, 1000)
        print(f"ImageHub bound to {address}, RCVTIMEO=1000ms")
    except Exception as e:
        print("Error initializing ImageHub:", e)
        return

    # 2) Tkinter setup
    root = Tk()
    root.title("Single-Host View Server (Single IP)")
    root.geometry("800x600")

    # A frame for the video label
    video_frame = Frame(root)
    video_frame.pack(side=TOP, fill=BOTH, expand=True)

    # A single label to display the chosen client's feed
    video_label = Label(video_frame, text="Waiting for the first client...")
    video_label.pack()

    lock = threading.Lock()

    # We will lock onto whichever client connects first
    fixed_client_name = None
    latest_frame = None

    def receive_thread():
        nonlocal fixed_client_name, latest_frame
        print("Receive thread started...")

        while True:
            try:
                # Attempt to receive a frame within 1s
                client_name, frame = image_hub.recv_image()

                with lock:
                    # If we haven’t locked in a client yet, do so now.
                    if fixed_client_name is None:
                        fixed_client_name = client_name
                        print(f"Locked onto client '{fixed_client_name}'.")

                    # Only accept frames from the locked-in client
                    if client_name == fixed_client_name:
                        latest_frame = frame

                # Always send reply so client doesn't block
                image_hub.send_reply(b'OK')

            except zmq.error.Again:
                # Timed out (no frames in 1s), just keep looping
                pass
            except Exception as e:
                print("Error receiving image:", e)
                time.sleep(1)

    def update_view():
        nonlocal fixed_client_name, latest_frame

        with lock:
            frame = latest_frame

        if fixed_client_name is None:
            # Still waiting for the first client
            video_label.config(text="No client connected yet.")
        else:
            if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                # Convert BGR->RGB->TkImage
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                tk_img = ImageTk.PhotoImage(image=pil_img)

                # Display
                video_label.config(image=tk_img, text="")
                video_label.image = tk_img  # must keep reference
            else:
                video_label.config(text=f"No valid frame from '{fixed_client_name}'")

        root.after(30, update_view)

    # Start the receiving thread
    t = threading.Thread(target=receive_thread, daemon=True)
    t.start()

    # Periodic GUI update
    root.after(30, update_view)

    root.mainloop()

if __name__ == "__main__":
    main()
