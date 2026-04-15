'''
REAL-TIME IRIS PROCESSING WITH SOCKET STREAMING FOR UNITY
- Receives camera frames FROM Unity (Vive Focus Vision via Wave SDK)
- Processes iris in real time
- Sends IrisTemplate to match_unity.py over a socket
 
Frame protocol (Unity → run_unity.py):
  [4 bytes] frame width  (big-endian uint32)
  [4 bytes] frame height (big-endian uint32)
  [4 bytes] data length  (big-endian uint32)
  [N bytes] raw RGBA pixel data (width * height * 4 bytes)
 
STARTUP ORDER:
  1. Run run_unity.py   (binds both ports immediately)
  2. Run match_unity.py (connects to port 5000)
  3. Press Play in Unity (connects to port 4999)
'''
 
import cv2
import iris
import numpy as np
import socket
import pickle
import struct
import threading
import time
 
# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
HOST             = '127.0.0.1'
UNITY_FRAME_PORT = 4999   # Unity connects here to send frames
MATCH_PORT       = 5000   # match_unity.py connects here to receive templates
EYE_SIDE         = "left" # "left" or "right"
# ─────────────────────────────────────────────
 
 
def preprocess(img_pixels):
    """Apply CLAHE enhancement before iris pipeline"""
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(img_pixels).astype(np.uint8)
 
 
def recv_exact(sock, n):
    """Receive exactly n bytes from socket, return None on disconnect"""
    data = b''
    while len(data) < n:
        try:
            chunk = sock.recv(n - len(data))
        except OSError:
            return None
        if not chunk:
            return None
        data += chunk
    return data
 
 
def receive_frame(conn):
    """
    Receive one frame sent by Unity.
    Protocol: width(4) + height(4) + data_len(4) + raw RGBA bytes
    Returns a grayscale numpy array, or None on failure.
    """
    header = recv_exact(conn, 12)
    if header is None:
        return None
 
    width, height, data_len = struct.unpack('>III', header)
 
    # Sanity-check dimensions to avoid giant mallocs on corrupt headers
    if width == 0 or height == 0 or data_len > 50_000_000:
        print(f"[run_unity] Bad header: {width}x{height}, data_len={data_len} — skipping frame")
        return None
 
    raw = recv_exact(conn, data_len)
    if raw is None:
        return None
 
    rgba = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 4))
    gray = cv2.cvtColor(rgba, cv2.COLOR_RGBA2GRAY)
    return gray
 
 
def capture_and_process():
    iris_pipeline = iris.IRISPipeline()
 
    # ── Bind BOTH server sockets up front so clients can connect in any order ──
    match_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    match_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    match_server.bind((HOST, MATCH_PORT))
    match_server.listen(1)
 
    frame_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    frame_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    frame_server.bind((HOST, UNITY_FRAME_PORT))
    frame_server.listen(1)
 
    print(f"[run_unity] Listening for match_unity.py on {HOST}:{MATCH_PORT}")
    print(f"[run_unity] Listening for Unity frames  on {HOST}:{UNITY_FRAME_PORT}")
    print(f"[run_unity] Start match_unity.py and press Play in Unity (order doesn't matter now).")
 
    # ── Accept both connections concurrently using threads ──
    match_conn_holder = [None]
    frame_conn_holder = [None]
 
    def accept_match():
        conn, addr = match_server.accept()
        match_conn_holder[0] = conn
        print(f"[run_unity] match_unity.py connected from {addr}")
 
    def accept_frame():
        conn, addr = frame_server.accept()
        frame_conn_holder[0] = conn
        print(f"[run_unity] Unity connected from {addr}")
 
    t1 = threading.Thread(target=accept_match, daemon=True)
    t2 = threading.Thread(target=accept_frame, daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
 
    match_conn = match_conn_holder[0]
    frame_conn = frame_conn_holder[0]
 
    print("[run_unity] Both clients connected. Processing incoming frames...")
 
    while True:
        gray = receive_frame(frame_conn)
        if gray is None:
            print("[run_unity] Unity disconnected or frame error.")
            break
 
        enhanced = preprocess(gray)
 
        try:
            output   = iris_pipeline(img_data=enhanced, eye_side=EYE_SIDE)
            template = output['iris_template']
 
            data    = pickle.dumps(template)
            msg_len = struct.pack('>I', len(data))
            match_conn.sendall(msg_len + data)
            print(f"[run_unity] Sent iris template ({len(data)} bytes)")
 
        except Exception as e:
            print(f"[run_unity] Iris processing failed: {e}")
 
    frame_conn.close()
    frame_server.close()
    match_conn.close()
    match_server.close()
 
 
if __name__ == "__main__":
    capture_and_process()