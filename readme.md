# 📹 LAN Video Calling App

A **LAN-based Video Calling Application** for two people using Python, WebRTC, and Tkinter.  
Supports **real-time video, mute/unmute, video on/off**, and works over a **local network** without needing external servers.

---

## 🚀 Features

- **Two-person LAN video calls** (no internet required)
- **Start/Join** a call easily with a few clicks
- **Real-time video streaming** using OpenCV
- **Mute/Unmute microphone**
- **Turn camera on/off**
- Simple and intuitive **Tkinter-based GUI**
- Uses **WebRTC** for peer-to-peer connection

---

## 📦 Requirements

Install the dependencies with:

```bash
pip install opencv-python websockets aiortc pyaudio pillow
````

> Python 3.8+ is recommended.

---

## 📂 Project Structure

```
📁 LAN-Video-Call
│── main.py   # Main application
│── README.md       # Documentation
```

---

## 🖥 How It Works

This app uses:

* **WebSockets** for signaling between peers
* **WebRTC (aiortc)** for direct audio/video streaming
* **OpenCV** to capture and display video
* **Tkinter** for the user interface
* **PyAudio** for microphone audio capture

---

## 📋 Usage

### 1️⃣ Start the Application

Run the script:

```bash
python main.py
```

### 2️⃣ Setup Connection

* **One person** clicks **"Start Server"** (acts as the signaling server)
* **Both persons** enter the same **Server IP** and click **"Connect"**

### 3️⃣ Start Video Call

* Once connected, click **"📞 Start Call"**
* Use **Mute** or **Video Off** buttons as needed

---

## 🖼 Screenshots

### Main UI

![UI Preview](https://via.placeholder.com/800x400?text=LAN+Video+Call+UI)

---

## ⚙️ Controls

| Button        | Action                        |
| ------------- | ----------------------------- |
| 📞 Start Call | Starts or ends the call       |
| 🎤 Mute       | Mutes microphone              |
| 📹 Video Off  | Turns off camera              |
| Start Server  | Starts local signaling server |
| Connect       | Connects to server            |

---

## 🔧 Technical Details

* **Signaling**: Implemented using `websockets` and `asyncio`
* **Media Streaming**: Powered by `aiortc`
* **Video Processing**: Handled with `OpenCV` and `Pillow`
* **Audio**: Captured using `PyAudio`
* **UI**: Built with `Tkinter`

---

## ⚠️ Limitations

* Works only on the **same local network (LAN)**
* Currently supports **only two participants**
* Audio streaming is not fully implemented in this version

---

## 📜 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## 📬 Contact

For issues or suggestions, open a [GitHub Issue](../../issues).

