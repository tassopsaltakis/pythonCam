import cv2
import imagezmq
import zmq
import time
from tkinter import *
from PIL import Image, ImageTk
import threading
import queue

def main():
    print("Starting Video Stream Server...")

    # --- 1) Initialize ImageHub with a 1s receive timeout ---
    try:
        image_hub = imagezmq.ImageHub(open_port='tcp://*:5555')
        # Set 1-second timeout to avoid blocking indefinitely
        image_hub.zmq_socket.setsockopt(zmq.RCVTIMEO, 1000)
        print("ImageHub initialized on tcp://*:5555 (1s recv timeout).")
    except Exception as e:
        print(f"Failed to initialize ImageHub: {e}")
        return

    # --- 2) Create the Tkinter GUI Window ---
    root = Tk()
    root.title("Video Stream Server")
    # You can adjust window size as needed
    root.geometry("1200x800")
    print("Tkinter window created.")

    # Top frame for single/grid controls & status
    top_frame = Frame(root)
    top_frame.pack(side=TOP, fill=X, pady=5)

    # Main frame for displaying videos
    video_frame = Frame(root)
    video_frame.pack(side=TOP, fill=BOTH, expand=True)

    # Bottom frame for client buttons & logs
    bottom_frame = Frame(root)
    bottom_frame.pack(side=BOTTOM, fill=X, pady=10)

    button_frame = Frame(bottom_frame)
    button_frame.pack(side=LEFT, fill=X, expand=True)

    log_frame = Frame(bottom_frame)
    log_frame.pack(side=RIGHT, fill=BOTH, expand=True)

    # Label for Single View
    video_label = Label(video_frame)
    video_label.pack()

    # Status label (top left)
    status_label = Label(top_frame, text="Waiting for video streams...", font=("Arial", 14))
    status_label.pack(side=LEFT, padx=10)

    # Log UI
    log_label = Label(log_frame, text="Logs:", font=("Arial", 12))
    log_label.pack(anchor='nw')
    log_text = Text(log_frame, height=10, state='disabled', wrap='word')
    log_text.pack(fill=BOTH, expand=True)
    log_scroll = Scrollbar(log_frame, command=log_text.yview)
    log_scroll.pack(side=RIGHT, fill=Y)
    log_text.configure(yscrollcommand=log_scroll.set)

    # --- Data Structures ---
    clients = {}          # client_name -> latest frame (BGR, as from OpenCV)
    client_labels = {}    # client_name -> Label widget (for grid mode)
    current_client = None # The client displayed in single view
    view_mode = StringVar(value='Single')  # "Single" or "Grid"
    clients_lock = threading.Lock()
    log_queue = queue.Queue()

    # --- Helper Functions ---

    def log_message(msg):
        """Thread-safe way to add logs for display in the text widget."""
        log_queue.put(msg)

    def update_video(frame):
        """
        Display a single frame (BGR -> RGB) in `video_label` (Tk).
        """
        try:
            if frame is None or frame.shape[0] == 0 or frame.shape[1] == 0:
                return
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(frame_rgb)
            tk_img = ImageTk.PhotoImage(image=im)
            video_label.config(image=tk_img)
            video_label.image = tk_img  # Keep a reference!
        except Exception as e:
            log_message(f"Error updating video: {e}")

    def update_grid():
        """
        Show all connected clients in a 2-col grid,
        each frame resized to (320, 240).
        """
        try:
            # Clear existing layout
            for widget in video_frame.winfo_children():
                widget.pack_forget()
                widget.grid_forget()

            sorted_clients = sorted(clients.keys())  # sort by name
            columns = 2
            target_size = (320, 240)  # or adjust as needed

            for idx, client_name in enumerate(sorted_clients):
                frame = clients[client_name]
                if frame is None or frame.shape[0] == 0 or frame.shape[1] == 0:
                    continue

                try:
                    resized_frame = cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
                except Exception as re:
                    log_message(f"Error resizing {client_name}'s frame: {re}")
                    continue

                frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                im = Image.fromarray(frame_rgb)
                tk_img = ImageTk.PhotoImage(image=im)

                # Create or reuse a label for this client
                if client_name not in client_labels:
                    lbl = Label(video_frame)
                    client_labels[client_name] = lbl
                else:
                    lbl = client_labels[client_name]

                lbl.config(image=tk_img)
                lbl.image = tk_img  # keep reference

                row = idx // columns
                col = idx % columns
                lbl.grid(row=row, column=col, padx=5, pady=5)

        except Exception as e:
            log_message(f"Error updating grid: {e}")

    def switch_stream(client_name):
        """Switch Single View to show the chosen client."""
        nonlocal current_client
        current_client = client_name
        status_label.config(text=f"Displaying stream from {client_name}")
        log_message(f"Switched to client: {client_name}")

    def add_client_button(client_name):
        """Add a button to switch to client's single view."""
        try:
            btn = Button(button_frame, text=f"Stream {client_name}",
                         command=lambda: switch_stream(client_name))
            btn.pack(side=LEFT, padx=5)
            log_message(f"Added button for client: {client_name}")
        except Exception as e:
            log_message(f"Error adding client button: {e}")

    def toggle_view_mode():
        """Switch between Single and Grid views."""
        mode = view_mode.get()
        log_message(f"Toggling view mode to: {mode}")
        if mode == 'Single':
            # Hide all grid labels
            for lbl in client_labels.values():
                lbl.grid_forget()

            video_label.pack()
            if current_client:
                status_label.config(text=f"Displaying stream from {current_client}")
            else:
                status_label.config(text="Waiting for video streams...")
        else:
            video_label.pack_forget()
            status_label.config(text="Displaying all streams in a grid")
            update_grid()

    # --- Background Thread: Receive Images ---
    def receive_images():
        nonlocal current_client
        log_message("Image receiving thread started.")
        while True:
            try:
                # If no frames in 1s, zmq.error.Again is raised
                client_name, frame = image_hub.recv_image()
                log_message(f"Received frame from {client_name}")

                with clients_lock:
                    # If it's a new client, add a button
                    if client_name not in clients:
                        add_client_button(client_name)
                        # If no current client in single view, pick this one
                        if current_client is None and view_mode.get() == 'Single':
                            current_client = client_name
                            status_label.config(text=f"Displaying stream from {client_name}")
                            log_message(f"Auto-selected client: {client_name}")

                    # Store/update the latest frame
                    clients[client_name] = frame

                # Always send an acknowledgement
                image_hub.send_reply(b'OK')

            except zmq.error.Again:
                # No frames arrived in 1s, just keep looping
                pass
            except Exception as e:
                # Log any other error but don't break
                log_message(f"Error receiving image: {e}")
                time.sleep(1)

    # --- GUI Refresh Loop ---
    def refresh_gui():
        """Update the log text and either the Single or Grid view every 30ms."""
        # 1) Display log messages
        while not log_queue.empty():
            msg = log_queue.get_nowait()
            log_text.config(state='normal')
            log_text.insert(END, msg + '\n')
            log_text.see(END)
            log_text.config(state='disabled')

        # 2) Update single or grid
        with clients_lock:
            if view_mode.get() == 'Single':
                if current_client and current_client in clients:
                    update_video(clients[current_client])
            else:
                update_grid()

        root.after(30, refresh_gui)

    # --- Build UI controls for Single/Grid selection ---
    single_rb = Radiobutton(top_frame, text="Single View", variable=view_mode,
                            value='Single', command=toggle_view_mode)
    grid_rb = Radiobutton(top_frame, text="Grid View", variable=view_mode,
                          value='Grid', command=toggle_view_mode)
    single_rb.pack(side=LEFT, padx=5)
    grid_rb.pack(side=LEFT, padx=5)

    # --- Start the receive thread ---
    t = threading.Thread(target=receive_images, daemon=True)
    t.start()
    log_message("Image receiving thread started.")

    # --- Start the GUI loop ---
    root.after(30, refresh_gui)
    log_message("Starting Tkinter mainloop.")
    root.mainloop()

if __name__ == "__main__":
    main()
