# server.py
import cv2
import imagezmq
from tkinter import *
from PIL import Image, ImageTk

# Initialize the server
image_hub = imagezmq.ImageHub()

# Create a Tkinter window
root = Tk()
root.title("Video Stream Server")

# Set the window size
root.geometry("1000x800")

# Frame that will hold the top controls
top_frame = Frame(root)
top_frame.pack(side=TOP, fill=X, pady=5)

# Frame that will hold the video(s)
video_frame = Frame(root)
video_frame.pack(side=TOP, fill=BOTH, expand=True)

# Bottom frame for buttons to switch between streams
button_frame = Frame(root)
button_frame.pack(side=BOTTOM, fill=X, pady=10)

# Label to display the current stream (Single view)
video_label = Label(video_frame)
video_label.pack()

# Label to show status
status_label = Label(top_frame, text="Waiting for video streams...", font=("Arial", 14))
status_label.pack(side=LEFT, padx=10)

# Dictionary to store the clients and their latest frames
clients = {}

# Dictionary for client labels in grid mode (client_name -> Label)
client_labels = {}

# Currently displayed client
current_client = None

# View mode - can be 'Single' or 'Grid'
view_mode = StringVar(value='Single')


def update_video(frame):
    """Convert OpenCV frame to Tkinter image and display it in the single-video label."""
    # Convert the frame to RGB (Tkinter uses RGB while OpenCV uses BGR)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to a PIL image and then to ImageTk format for Tkinter
    im = Image.fromarray(frame_rgb)
    img = ImageTk.PhotoImage(image=im)

    # Update the Tkinter label with the new frame
    video_label.imgtk = img
    video_label.configure(image=img)


def update_grid():
    """
    In Grid view, update each client's Label with the latest frame.
    We use a simple 2-column layout as an example.
    You can adjust the layout logic to suit your needs (e.g., 3 columns, 4 columns, etc.).
    """
    # Clear out any existing Label widgets if the client went away
    # or if we have new clients that don't have labels yet, create them.
    # We'll re-pack everything each time.
    for widget in video_frame.winfo_children():
        widget.pack_forget()
        widget.grid_forget()

    # Sort clients by name or in insertion order if you prefer
    sorted_clients = list(clients.keys())

    columns = 2  # Number of columns in the grid
    for idx, client_name in enumerate(sorted_clients):
        frame = clients[client_name]

        # If we don't have a label for this client yet, create one
        if client_name not in client_labels:
            label = Label(video_frame)
            client_labels[client_name] = label
        else:
            label = client_labels[client_name]

        # Convert frame to a Tkinter-friendly image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(frame_rgb)
        img = ImageTk.PhotoImage(image=im)
        label.imgtk = img
        label.configure(image=img)

        # Grid placement
        row = idx // columns
        col = idx % columns
        label.grid(row=row, column=col, padx=5, pady=5)


def switch_stream(client_name):
    """Switch to displaying the selected client's stream (in Single view)."""
    global current_client
    current_client = client_name
    status_label.config(text=f"Displaying stream from {client_name}")


def add_client_button(client_name):
    """Add a button to the GUI for switching to a client's stream."""
    # Create a button for this client (for Single view)
    button = Button(button_frame, text=f"Stream {client_name}",
                    command=lambda: switch_stream(client_name))
    button.pack(side=LEFT, padx=5)


def toggle_view_mode():
    """Switch between Single and Grid view."""
    global view_mode
    mode = view_mode.get()

    if mode == 'Single':
        # Hide all client labels in case they're visible from Grid mode
        for lbl in client_labels.values():
            lbl.grid_forget()
        video_label.pack()  # Make sure the single view label is visible
        if current_client:
            status_label.config(text=f"Displaying stream from {current_client}")
        else:
            status_label.config(text="Waiting for video streams...")
    else:
        # Grid view
        video_label.pack_forget()  # Hide the single view label
        status_label.config(text="Displaying all streams in a grid")


def stream_video():
    """Receive and display video frames from the clients."""
    global current_client

    while True:
        # Receive frame from client
        client_name, frame = image_hub.recv_image()

        # If this is a new client, add a button for it
        if client_name not in clients:
            add_client_button(client_name)
            # If no current client is selected (Single mode), pick the first client automatically
            if current_client is None:
                current_client = client_name
                status_label.config(text=f"Displaying stream from {client_name}")

        # Store/update the latest frame for this client
        clients[client_name] = frame

        # In Single view, update only the currently selected client's video
        # In Grid view, update all
        mode = view_mode.get()
        if mode == 'Single':
            if current_client == client_name:
                update_video(frame)
        else:
            update_grid()

        # Send acknowledgment back to the client
        image_hub.send_reply(b'OK')

        # Keep the Tkinter GUI responsive
        root.update()


# Create Radio Buttons to toggle between 'Single' and 'Grid' view
single_rb = Radiobutton(top_frame, text="Single View", variable=view_mode, value='Single',
                        command=toggle_view_mode)
grid_rb = Radiobutton(top_frame, text="Grid View", variable=view_mode, value='Grid',
                      command=toggle_view_mode)
single_rb.pack(side=LEFT, padx=5)
grid_rb.pack(side=LEFT, padx=5)

# Run the video stream in the Tkinter window
root.after(0, stream_video)
root.mainloop()
