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
root.geometry("800x600")

# Label to display the current stream
video_label = Label(root)
video_label.pack()

# Label to show "Waiting for video streams..."
status_label = Label(root, text="Waiting for video streams...", font=("Arial", 14))
status_label.pack()

# Frame for buttons (to switch between streams)
button_frame = Frame(root)
button_frame.pack(pady=20)

# Dictionary to store the clients and their frames
clients = {}

# Currently displayed client
current_client = None

def update_video(frame):
    """Convert OpenCV frame to Tkinter image and display it."""
    # Convert the frame to RGB (Tkinter uses RGB while OpenCV uses BGR)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to a PIL image and then to ImageTk format for Tkinter
    im = Image.fromarray(frame_rgb)
    img = ImageTk.PhotoImage(image=im)

    # Update the Tkinter label with the new frame
    video_label.imgtk = img
    video_label.configure(image=img)

def switch_stream(client_name):
    """Switch to displaying the selected client stream."""
    global current_client
    current_client = client_name
    status_label.config(text=f"Displaying stream from {client_name}")

def add_client_button(client_name):
    """Add a button to the GUI for switching to a client's stream."""
    # Create a button for this client
    button = Button(button_frame, text=f"Stream {client_name}", command=lambda: switch_stream(client_name))
    button.pack(side=LEFT, padx=5)

def stream_video():
    """Receive and display video frames from the clients."""
    global current_client

    while True:
        # Receive frame from client
        client_name, frame = image_hub.recv_image()

        # If this is a new client, add a button for it
        if client_name not in clients:
            clients[client_name] = frame
            add_client_button(client_name)
            if current_client is None:
                switch_stream(client_name)

        # Update the video only for the currently selected client
        if current_client == client_name:
            update_video(frame)

        # Send acknowledgment back to the client
        image_hub.send_reply(b'OK')

        # Keep the Tkinter GUI responsive
        root.update()

# Run the video stream in the Tkinter window
root.after(0, stream_video)
root.mainloop()
