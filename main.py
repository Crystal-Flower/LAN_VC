#!/usr/bin/env python3
"""
LAN Video Calling App for Two People
Requires: pip install opencv-python websockets aiortc pyaudio tkinter
"""

import asyncio
import json
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import websockets
from websockets.server import serve
import socket
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.contrib.signaling import BYE
import numpy as np
from PIL import Image, ImageTk
import pyaudio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
signaling_server = None
relay = MediaRelay()


class VideoCallGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAN Video Call")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')

        # Video call state
        self.pc = None
        self.websocket = None
        self.local_video = None
        self.remote_video = None
        self.is_calling = False
        self.is_muted = False
        self.is_video_off = False

        # OpenCV camera
        self.cap = None
        self.video_thread = None
        self.running = False

        self.setup_ui()

    def setup_ui(self):
        # Header frame
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="LAN Video Call",
                               font=('Arial', 20, 'bold'),
                               fg='white', bg='#34495e')
        title_label.pack(pady=20)

        # Connection frame
        self.connection_frame = tk.Frame(self.root, bg='#ecf0f1', relief=tk.RAISED, bd=2)
        self.connection_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(self.connection_frame, text="Server IP:",
                 font=('Arial', 12), bg='#ecf0f1').pack(side=tk.LEFT, padx=10)

        self.server_ip_entry = tk.Entry(self.connection_frame, font=('Arial', 12), width=15)
        self.server_ip_entry.pack(side=tk.LEFT, padx=5)
        self.server_ip_entry.insert(0, self.get_local_ip())

        self.start_server_btn = tk.Button(self.connection_frame, text="Start Server",
                                          command=self.start_server, bg='#3498db',
                                          fg='white', font=('Arial', 10, 'bold'))
        self.start_server_btn.pack(side=tk.LEFT, padx=10)

        self.connect_btn = tk.Button(self.connection_frame, text="Connect",
                                     command=self.connect_to_server, bg='#2ecc71',
                                     fg='white', font=('Arial', 10, 'bold'))
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(self.connection_frame, text="Disconnected",
                                     fg='red', font=('Arial', 12, 'bold'), bg='#ecf0f1')
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Video frames
        video_frame = tk.Frame(self.root, bg='#2c3e50')
        video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Local video frame
        local_frame = tk.LabelFrame(video_frame, text="You", fg='white',
                                    bg='#2c3e50', font=('Arial', 12, 'bold'))
        local_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.local_video_label = tk.Label(local_frame, bg='black', text="No Video",
                                          fg='white', font=('Arial', 16))
        self.local_video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Remote video frame
        remote_frame = tk.LabelFrame(video_frame, text="Remote", fg='white',
                                     bg='#2c3e50', font=('Arial', 12, 'bold'))
        remote_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.remote_video_label = tk.Label(remote_frame, bg='black', text="No Video",
                                           fg='white', font=('Arial', 16))
        self.remote_video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Controls frame
        controls_frame = tk.Frame(self.root, bg='#34495e', height=80)
        controls_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        controls_frame.pack_propagate(False)

        # Control buttons
        self.call_btn = tk.Button(controls_frame, text="📞 Start Call",
                                  command=self.toggle_call, bg='#2ecc71',
                                  fg='white', font=('Arial', 12, 'bold'), width=12)
        self.call_btn.pack(side=tk.LEFT, padx=10, pady=20)

        self.mute_btn = tk.Button(controls_frame, text="🎤 Mute",
                                  command=self.toggle_mute, bg='#f39c12',
                                  fg='white', font=('Arial', 12, 'bold'), width=10)
        self.mute_btn.pack(side=tk.LEFT, padx=5, pady=20)

        self.video_btn = tk.Button(controls_frame, text="📹 Video Off",
                                   command=self.toggle_video, bg='#f39c12',
                                   fg='white', font=('Arial', 12, 'bold'), width=12)
        self.video_btn.pack(side=tk.LEFT, padx=5, pady=20)

        # Info label
        self.info_label = tk.Label(controls_frame, text="Start server or connect to begin",
                                   fg='white', bg='#34495e', font=('Arial', 10))
        self.info_label.pack(side=tk.RIGHT, padx=10, pady=20)

    def get_local_ip(self):
        """Get local IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"

    def start_server(self):
        """Start the signaling server"""

        def run_server():
            asyncio.run(self.signaling_server())

        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

        self.start_server_btn.config(state='disabled', text='Server Running')
        self.info_label.config(text=f"Server started on {self.server_ip_entry.get()}:8765")

    async def signaling_server(self):
        """WebSocket signaling server"""
        clients = set()

        async def handle_client(websocket, path):
            clients.add(websocket)
            logger.info(f"Client connected. Total clients: {len(clients)}")

            try:
                async for message in websocket:
                    data = json.loads(message)
                    logger.info(f"Received: {data['type']}")

                    # Relay message to other client
                    for client in clients:
                        if client != websocket:
                            await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                clients.remove(websocket)
                logger.info(f"Client disconnected. Total clients: {len(clients)}")

        server = await serve(handle_client, "0.0.0.0", 8765)
        logger.info("Signaling server started on port 8765")
        await server.wait_closed()

    async def connect_to_server(self):
        """Connect to signaling server"""
        server_ip = self.server_ip_entry.get()
        uri = f"ws://{server_ip}:8765"

        try:
            self.websocket = await websockets.connect(uri)
            self.status_label.config(text="Connected", fg='green')
            self.connect_btn.config(state='disabled', text='Connected')
            self.info_label.config(text="Connected to server. Ready to call!")

            # Start listening for messages
            asyncio.create_task(self.handle_signaling_messages())

        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")

    def connect_to_server_sync(self):
        """Synchronous wrapper for connect_to_server"""
        asyncio.run(self.connect_to_server())

    async def handle_signaling_messages(self):
        """Handle incoming signaling messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.process_signaling_message(data)
        except websockets.exceptions.ConnectionClosed:
            self.status_label.config(text="Disconnected", fg='red')

    async def process_signaling_message(self, data):
        """Process signaling messages"""
        if data['type'] == 'offer':
            await self.handle_offer(data)
        elif data['type'] == 'answer':
            await self.handle_answer(data)
        elif data['type'] == 'ice-candidate':
            await self.handle_ice_candidate(data)
        elif data['type'] == 'hangup':
            self.end_call()

    def toggle_call(self):
        """Toggle call state"""
        if not self.is_calling:
            asyncio.run(self.start_call())
        else:
            self.end_call()

    async def start_call(self):
        """Start video call"""
        if not self.websocket:
            messagebox.showwarning("Not Connected", "Please connect to server first")
            return

        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Camera Error", "Could not open camera")
                return

            # Set camera properties for lower latency
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size

            # Create peer connection
            self.pc = RTCPeerConnection()

            # Add video track
            # Note: In a full implementation, you'd create a custom MediaStreamTrack
            # For simplicity, this example shows the UI structure

            self.is_calling = True
            self.call_btn.config(text="📞 End Call", bg='#e74c3c')
            self.info_label.config(text="Calling...")

            # Start video display thread
            self.running = True
            self.video_thread = threading.Thread(target=self.video_loop)
            self.video_thread.daemon = True
            self.video_thread.start()

            # Create offer
            await self.create_offer()

        except Exception as e:
            messagebox.showerror("Call Error", f"Failed to start call: {str(e)}")
            self.end_call()

    def video_loop(self):
        """Video display loop"""
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)

                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PIL Image
                pil_image = Image.fromarray(rgb_frame)

                # Resize to fit label
                pil_image = pil_image.resize((400, 300), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)

                # Update local video label
                self.local_video_label.config(image=photo, text="")
                self.local_video_label.image = photo

            # Limit frame rate
            asyncio.run(asyncio.sleep(0.033))  # ~30 FPS

    async def create_offer(self):
        """Create WebRTC offer"""
        if not self.pc:
            return

        try:
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)

            # Send offer via signaling
            await self.websocket.send(json.dumps({
                'type': 'offer',
                'sdp': self.pc.localDescription.sdp
            }))

        except Exception as e:
            logger.error(f"Error creating offer: {e}")

    async def handle_offer(self, data):
        """Handle incoming offer"""
        try:
            if not self.pc:
                self.pc = RTCPeerConnection()

            # Set remote description
            await self.pc.setRemoteDescription(
                RTCSessionDescription(sdp=data['sdp'], type='offer')
            )

            # Create answer
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)

            # Send answer
            await self.websocket.send(json.dumps({
                'type': 'answer',
                'sdp': self.pc.localDescription.sdp
            }))

            # Auto-accept incoming call
            if not self.is_calling:
                await self.start_call()

        except Exception as e:
            logger.error(f"Error handling offer: {e}")

    async def handle_answer(self, data):
        """Handle incoming answer"""
        try:
            await self.pc.setRemoteDescription(
                RTCSessionDescription(sdp=data['sdp'], type='answer')
            )
            self.info_label.config(text="Call connected!")

        except Exception as e:
            logger.error(f"Error handling answer: {e}")

    async def handle_ice_candidate(self, data):
        """Handle ICE candidate"""
        try:
            if self.pc:
                candidate = RTCIceCandidate(
                    component=data['candidate']['component'],
                    foundation=data['candidate']['foundation'],
                    ip=data['candidate']['ip'],
                    port=data['candidate']['port'],
                    priority=data['candidate']['priority'],
                    protocol=data['candidate']['protocol'],
                    type=data['candidate']['type']
                )
                await self.pc.addIceCandidate(candidate)

        except Exception as e:
            logger.error(f"Error handling ICE candidate: {e}")

    def end_call(self):
        """End the current call"""
        self.running = False
        self.is_calling = False

        if self.cap:
            self.cap.release()
            self.cap = None

        if self.pc:
            asyncio.run(self.pc.close())
            self.pc = None

        # Send hangup signal
        if self.websocket:
            asyncio.run(self.websocket.send(json.dumps({'type': 'hangup'})))

        # Reset UI
        self.call_btn.config(text="📞 Start Call", bg='#2ecc71')
        self.local_video_label.config(image='', text="No Video")
        self.remote_video_label.config(image='', text="No Video")
        self.info_label.config(text="Call ended")

        # Reset local video label image reference
        self.local_video_label.image = None

    def toggle_mute(self):
        """Toggle microphone mute"""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.mute_btn.config(text="🔇 Unmute", bg='#e74c3c')
        else:
            self.mute_btn.config(text="🎤 Mute", bg='#f39c12')

    def toggle_video(self):
        """Toggle video on/off"""
        self.is_video_off = not self.is_video_off
        if self.is_video_off:
            self.video_btn.config(text="📷 Video On", bg='#e74c3c')
            self.local_video_label.config(image='', text="Video Off")
        else:
            self.video_btn.config(text="📹 Video Off", bg='#f39c12')

    def run(self):
        """Start the GUI"""

        def on_closing():
            self.end_call()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)

        # Make connect button work with asyncio
        original_connect = self.connect_btn.config()['command'][4]
        self.connect_btn.config(command=lambda: threading.Thread(
            target=self.connect_to_server_sync).start())

        self.root.mainloop()


def main():
    """Main function"""
    print("LAN Video Calling App")
    print("====================")
    print("Instructions:")
    print("1. One person clicks 'Start Server'")
    print("2. Both people enter the server IP and click 'Connect'")
    print("3. Click 'Start Call' to begin video calling")
    print("4. Use controls to mute/unmute or turn video on/off")
    print()

    app = VideoCallGUI()
    app.run()


if __name__ == "__main__":
    main()