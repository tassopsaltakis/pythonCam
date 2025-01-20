# server_single.py

import cv2
import imagezmq
import zmq
from tkinter import *
from PIL import Image, ImageTk
import threading
import time

def main():
    print("Starting Single-View Server...")

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
    root.title("Single Client View Server")
    root.geometry("800x600")

    # A frame for the video label
    video_frame = Frame(root)
    video_frame.pack(side=TOP, fill=BOTH, expand=True)

    # A frame for client selection buttons
    button_frame = Frame(root)
    button_frame.pack(side=BOTTOM, fill=X)

    # We'll store frames: {client_name: frame}
    clients = {}
    # The currently selected client
    selected_client = None

    # A single label to display the chosen client's feed
    video_label = Label(video_frame, text="No client selected")
    video_label.pack()

    lock = threading.Lock()

    def receive_thread():
        print("Receive thread started...")
        while True:
            try:
                client_name, frame = image_hub.recv_image()
                # Store frame
                with lock:
                    clients[client_name] = frame
                # Send reply
                image_hub.send_reply(b'OK')
            except zmq.error.Again:
                pass
            except Exception as e:
                print("Error receiving image:", e)
                time.sleep(1)

    def select_client(client_name):
        """When user clicks a button to pick which client's feed to show."""
        nonlocal selected_client
        selected_client = client_name
        video_label.config(text=f"Selected: {client_name}")
        print(f"Switched to client: {client_name}")

    def create_client_button(client_name):
        """Add a button for a newly discovered client."""
        btn = Button(button_frame, text=client_name, command=lambda: select_client(client_name))
        btn.pack(side=LEFT, padx=5, pady=5)

    def update_view():
        """
        Periodically display the selected client's latest frame.
        If none selected or no frame, do nothing.
        """
        with lock:
            if selected_client and selected_client in clients:
                frame = clients[selected_client]
            else:
                frame = None

        if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
            # Convert BGR->RGB->TkImage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            tk_img = ImageTk.PhotoImage(image=pil_img)

            # Display in video_label
            video_label.config(image=tk_img, text="")
            video_label.image = tk_img  # keep reference
        else:
            # If no frame, show placeholder text
            if selected_client:
                video_label.config(text=f"No valid frame from {selected_client}")

        root.after(30, update_view)

    # Also, check for new clients to add a button for them
    def detect_new_clients():
        with lock:
            current_clients = list(clients.keys())
        for cname in current_clients:
            # If the button doesn't exist yet, create one
            # We can track them in a local set if we want
            # but let's just do a naive check:
            found_btn = False
            for w in button_frame.winfo_children():
                if isinstance(w, Button) and w.cget("text") == cname:
                    found_btn = True
                    break
            if not found_btn:
                create_client_button(cname)

        root.after(1000, detect_new_clients)  # check every 1 second

    t = threading.Thread(target=receive_thread, daemon=True)
    t.start()

    root.after(30, update_view)
    root.after(1000, detect_new_clients)

    root.mainloop()

if __name__ == "__main__":
    main()
