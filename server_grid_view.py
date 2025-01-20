# server_grid_view.py

import cv2
import imagezmq
import zmq
from tkinter import *
from PIL import Image, ImageTk
import threading
import time

def main():
    print("Starting Grid-View Server...")

    # 1) Create ImageHub on port 5555; set 1s recv timeout
    try:
        image_hub = imagezmq.ImageHub(open_port='tcp://*:5555')
        image_hub.zmq_socket.setsockopt(zmq.RCVTIMEO, 1000)
        print("ImageHub bound to tcp://*:5555, RCVTIMEO=1000ms")
    except Exception as e:
        print("Error initializing ImageHub:", e)
        return

    # 2) Tkinter setup
    root = Tk()
    root.title("Grid View Server")
    root.geometry("1200x800")

    # Frame that will hold all video labels in a grid
    video_frame = Frame(root)
    video_frame.pack(fill=BOTH, expand=True)

    # We'll store the latest frames in this dict: {client_name: frame (BGR)}
    clients = {}
    # We'll store Label widgets in this dict: {client_name: Label}
    client_labels = {}

    # For thread safety when modifying 'clients'
    lock = threading.Lock()

    # 3) Background thread to receive images
    def receive_thread():
        print("Receive thread started...")
        while True:
            try:
                # Attempt to receive a frame within 1 second
                client_name, frame = image_hub.recv_image()
                # Store the frame in the dictionary
                with lock:
                    clients[client_name] = frame
                # Send an OK reply
                image_hub.send_reply(b'OK')
            except zmq.error.Again:
                # No frames arrived within 1 second, just loop again
                pass
            except Exception as e:
                print("Error receiving image:", e)
                # Keep looping rather than exiting, so the server stays alive
                time.sleep(1)

    # 4) Update the grid view in the Tkinter mainloop
    def update_grid():
        """
        Display all clients in a grid, each resized to (320x240).
        2 columns by default; adjust as needed.
        """
        with lock:
            # Sort client names so their positions are consistent
            client_names = sorted(clients.keys())

        # Clear the previous layout
        for widget in video_frame.winfo_children():
            widget.grid_forget()

        columns = 2
        target_size = (320, 240)

        row, col = 0, 0
        for idx, cname in enumerate(client_names):
            frame_bgr = clients[cname]

            # Basic checks: skip if frame is empty
            if (frame_bgr is None
                or frame_bgr.shape[0] == 0
                or frame_bgr.shape[1] == 0):
                continue

            # Resize to 320x240
            try:
                resized_frame = cv2.resize(frame_bgr, target_size, interpolation=cv2.INTER_AREA)
            except Exception as re:
                print(f"Error resizing frame from {cname}:", re)
                continue

            # Convert BGR->RGB->TkImage
            frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            tk_img = ImageTk.PhotoImage(image=pil_img)

            # Create or reuse a Label for this client
            if cname not in client_labels:
                lbl = Label(video_frame)
                client_labels[cname] = lbl
            else:
                lbl = client_labels[cname]

            lbl.config(image=tk_img)
            lbl.image = tk_img  # keep a reference
            lbl.grid(row=row, column=col, padx=5, pady=5)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        # Schedule next grid update
        root.after(30, update_grid)

    # Start the receiving thread (daemon=True so it stops with the main program)
    t = threading.Thread(target=receive_thread, daemon=True)
    t.start()

    # Kick off the first grid update
    root.after(30, update_grid)

    # Run the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
