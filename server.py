# server.py
import cv2
import imagezmq
from tkinter import *
from PIL import Image, ImageTk
import threading
import queue

def main():
    print("Starting Video Stream Server...")

    # Initialize the ImageHub (listen on port 5555)
    try:
        image_hub = imagezmq.ImageHub(open_port='tcp://192.168.7.176:5555')
        print("ImageHub initialized, listening on port 5555.")
    except Exception as e:
        print(f"Failed to initialize ImageHub: {e}")
        return

    # Create a Tkinter window
    root = Tk()
    root.title("Video Stream Server")

    # Set the window size
    root.geometry("1200x800")
    print("Tkinter window created.")

    # Frame that will hold the top controls
    top_frame = Frame(root)
    top_frame.pack(side=TOP, fill=X, pady=5)

    # Frame that will hold the video(s)
    video_frame = Frame(root)
    video_frame.pack(side=TOP, fill=BOTH, expand=True)

    # Bottom frame for buttons to switch between streams and logs
    bottom_frame = Frame(root)
    bottom_frame.pack(side=BOTTOM, fill=X, pady=10)

    # Frame for stream buttons
    button_frame = Frame(bottom_frame)
    button_frame.pack(side=LEFT, fill=X, expand=True)

    # Frame for logs
    log_frame = Frame(bottom_frame)
    log_frame.pack(side=RIGHT, fill=BOTH, expand=True)

    # Label to display the current stream (Single view)
    video_label = Label(video_frame)
    video_label.pack()

    # Label to show status
    status_label = Label(top_frame, text="Waiting for video streams...", font=("Arial", 14))
    status_label.pack(side=LEFT, padx=10)

    # Text widget for logs
    log_label = Label(log_frame, text="Logs:", font=("Arial", 12))
    log_label.pack(anchor='nw')

    log_text = Text(log_frame, height=10, state='disabled', wrap='word')
    log_text.pack(fill=BOTH, expand=True)

    # Scrollbar for log_text
    log_scroll = Scrollbar(log_frame, command=log_text.yview)
    log_scroll.pack(side=RIGHT, fill=Y)
    log_text.configure(yscrollcommand=log_scroll.set)

    # Dictionary to store the clients and their latest frames
    clients = {}

    # Dictionary for client labels in grid mode (client_name -> Label)
    client_labels = {}

    # Currently displayed client
    current_client = None

    # View mode - can be 'Single' or 'Grid'
    view_mode = StringVar(value='Single')

    # Lock for accessing clients dictionary
    clients_lock = threading.Lock()

    # Queue for log messages
    log_queue = queue.Queue()

    def log_message(message):
        """Add a log message to the log queue."""
        log_queue.put(message)

    def update_video(frame):
        """
        Convert an OpenCV frame (BGR) to a Tkinter image (RGB) and display it
        in the single-video label.
        """
        try:
            # Convert BGR -> RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(frame_rgb)
            img = ImageTk.PhotoImage(image=im)

            # Update the Tkinter label with the new frame
            video_label.imgtk = img
            video_label.configure(image=img)
        except Exception as e:
            log_message(f"Error updating video: {e}")

    def update_grid():
        """
        In Grid view, update each client's Label with the latest frame.
        We'll use a simple 2-column layout as an example.
        Adjust as needed (e.g., 3 columns, 4 columns).
        """
        try:
            # Remove any old grids or pack layout
            for widget in video_frame.winfo_children():
                widget.pack_forget()
                widget.grid_forget()

            sorted_clients = list(clients.keys())
            columns = 2  # Number of columns in the grid

            for idx, client_name in enumerate(sorted_clients):
                frame = clients[client_name]

                # Create a Label if it doesn't exist yet
                if client_name not in client_labels:
                    label = Label(video_frame)
                    client_labels[client_name] = label
                else:
                    label = client_labels[client_name]

                # Convert frame to Tkinter-friendly image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                im = Image.fromarray(frame_rgb)
                img = ImageTk.PhotoImage(image=im)
                label.imgtk = img
                label.configure(image=img)

                # Grid placement
                row = idx // columns
                col = idx % columns
                label.grid(row=row, column=col, padx=5, pady=5)
        except Exception as e:
            log_message(f"Error updating grid: {e}")

    def switch_stream(client_name):
        """
        Switch to displaying the selected client's stream (in Single view).
        """
        nonlocal current_client
        current_client = client_name
        status_label.config(text=f"Displaying stream from {client_name}")
        log_message(f"Switched to client: {client_name}")

    def add_client_button(client_name):
        """
        Add a button to the GUI for switching to a client's stream in Single view.
        """
        try:
            button = Button(
                button_frame,
                text=f"Stream {client_name}",
                command=lambda: switch_stream(client_name)
            )
            button.pack(side=LEFT, padx=5)
            log_message(f"Added button for client: {client_name}")
        except Exception as e:
            log_message(f"Error adding client button: {e}")

    def toggle_view_mode():
        """
        Switch between Single and Grid view based on the selected radio button.
        """
        try:
            mode = view_mode.get()
            log_message(f"Switching view mode to: {mode}")
            if mode == 'Single':
                # Hide all grid labels
                for lbl in client_labels.values():
                    lbl.grid_forget()
                # Show the single view label
                video_label.pack()
                if current_client:
                    status_label.config(text=f"Displaying stream from {current_client}")
                else:
                    status_label.config(text="Waiting for video streams...")
            else:
                # Hide single view label
                video_label.pack_forget()
                status_label.config(text="Displaying all streams in a grid")
                # Update the grid view
                update_grid()
        except Exception as e:
            log_message(f"Error toggling view mode: {e}")

    def receive_images():
        """
        Continuously receive frames from clients and update the clients dict.
        Runs in a separate thread.
        """
        nonlocal current_client
        log_message("Image receiving thread started.")
        while True:
            try:
                # Receive frame from client
                client_name, frame = image_hub.recv_image()
                log_message(f"Received frame from {client_name}")

                with clients_lock:
                    # If this is a new client, add a button for them
                    if client_name not in clients:
                        add_client_button(client_name)
                        # If no current client is selected in Single mode, pick the first client
                        if current_client is None and view_mode.get() == 'Single':
                            current_client = client_name
                            status_label.config(text=f"Displaying stream from {client_name}")
                            log_message(f"Automatically switched to first client: {client_name}")

                    # Store/update the latest frame for this client
                    clients[client_name] = frame

                # Send acknowledgment back to the client
                image_hub.send_reply(b'OK')
            except Exception as e:
                log_message(f"Error receiving image: {e}")
                break

    def refresh_gui():
        """
        Periodically update the GUI based on the current view mode and client frames.
        Also process any log messages in the log_queue.
        """
        try:
            # Process log messages
            while not log_queue.empty():
                message = log_queue.get_nowait()
                log_text.config(state='normal')
                log_text.insert(END, message + '\n')
                log_text.see(END)
                log_text.config(state='disabled')

            # Update video or grid
            with clients_lock:
                if view_mode.get() == 'Single':
                    if current_client and current_client in clients:
                        update_video(clients[current_client])
                else:
                    update_grid()
        except Exception as e:
            log_message(f"Error in refresh_gui: {e}")
        # Schedule the next refresh
        root.after(30, refresh_gui)  # Adjust the delay as needed (milliseconds)

    # Create Radio Buttons to toggle between 'Single' and 'Grid' view
    single_rb = Radiobutton(top_frame, text="Single View", variable=view_mode, value='Single',
                            command=toggle_view_mode)
    grid_rb = Radiobutton(top_frame, text="Grid View", variable=view_mode, value='Grid',
                          command=toggle_view_mode)
    single_rb.pack(side=LEFT, padx=5)
    grid_rb.pack(side=LEFT, padx=5)

    # Start the image receiving thread
    receive_thread = threading.Thread(target=receive_images, daemon=True)
    receive_thread.start()
    log_message("Image receiving thread started.")

    # Start the GUI refresh loop
    root.after(30, refresh_gui)  # Start the refresh loop

    # Start Tkinter event loop
    log_message("Starting Tkinter mainloop.")
    root.mainloop()

if __name__ == "__main__":
    main()
