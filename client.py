# client.py
import cv2
import base64
import asyncio
import websockets

async def send_video():
    # Connect to the server WebSocket
    uri = "ws://localhost:5000/socket.io/"
    async with websockets.connect(uri) as websocket:
        video_capture = cv2.VideoCapture(0)  # Use the webcam
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            # Encode the frame in JPEG format
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = base64.b64encode(buffer).decode('utf-8')

            # Send the frame data to the server
            await websocket.send(frame_data)

            # Wait for a short period to simulate a video frame rate (e.g., 30 FPS)
            await asyncio.sleep(0.03)

asyncio.get_event_loop().run_until_complete(send_video())
