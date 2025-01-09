# pythonCam

**A Python-Based Server and Client Security Camera Software Solution**

## Overview

**pythonCam** is a robust and flexible security camera software solution developed in Python. Designed to facilitate seamless video streaming between multiple client devices and a centralized server, pythonCam offers an intuitive graphical interface for monitoring and managing live video feeds in real-time.

## Features

- **Multi-Client Support**: Connect and manage multiple client devices simultaneously.
- **Dynamic Display Modes**:
  - **Single View**: Focus on a specific client's video feed.
  - **Grid View**: View all connected clients' streams in a customizable grid layout.
- **Real-Time Logging**: Monitor client connections and stream statuses directly within the GUI.
- **User-Friendly Interface**: Built with Tkinter for an intuitive and responsive user experience.
- **Threaded Processing**: Ensures smooth and lag-free video streaming by handling processes concurrently.
- **Cross-Platform Compatibility**: Compatible with both Windows and Linux operating systems.

## Technologies Used

- **Python 3**: Core programming language.
- **imagezmq**: Facilitates efficient image transmission over ZeroMQ.
- **OpenCV**: Handles video capture, processing, and conversion.
- **Tkinter**: Provides the graphical user interface.
- **Pillow (PIL)**: Assists in image manipulation and conversion.

## Project Structure

- **server.py**: Main server application for receiving and displaying video streams.
- **client.py**: Sample client application for capturing and streaming video from a device's camera.
- **README.md**: Project documentation.
- **LICENSE**: Apache License 2.0 governing usage and contributions.

## License

This project is licensed under the [Apache License 2.0](LICENSE.txt). You are free to use, modify, and distribute this software, provided you comply with the terms of the license.

## Authors

- **Anastasios Psaltakis**  
  *Lead Developer*  
  [GitHub Profile](https://github.com/tassopsaltakis)

## Acknowledgments

- Inspired by the need for a scalable and efficient security camera solution.
- Thanks to the developers of `imagezmq`, `OpenCV`, and `Tkinter` for providing essential tools that make this project possible.
