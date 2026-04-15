'''
icam.py - reads iris frames from IcamBridge.exe and streams to run_unity.py
Sends both left and right eye frames when available.
No popup windows.
'''

import numpy as np
import socket
import struct
import os
import time

HOST        = '127.0.0.1'
PORT        = 4999
RIGHT_FILE  = r"C:\icam_frames\right.bin"
LEFT_FILE   = r"C:\icam_frames\left.bin"
READY_FILE  = r"C:\icam_frames\ready.flag"
WIDTH       = 640
HEIGHT      = 480
FRAME_BYTES = WIDTH * HEIGHT

def send_frame(sock, raw_gray):
    # Convert grayscale to RGBA
    gray = np.frombuffer(raw_gray, dtype=np.uint8).reshape((HEIGHT, WIDTH))
    rgba = np.stack([gray, gray, gray, np.full_like(gray, 255)], axis=-1)
    data = rgba.tobytes()
    header = struct.pack('>III', WIDTH, HEIGHT, len(data))
    sock.sendall(header + data)

def main():
    print("[icam] Waiting for IcamBridge.exe to write first frame...")
    print(f"[icam] Watching: {READY_FILE}")

    while not os.path.exists(READY_FILE):
        time.sleep(0.1)

    print("[icam] Frame file found. Connecting to run_unity.py...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    print(f"[icam] Connected to run_unity.py on port {PORT}")

    last_flag = None
    frames_sent = 0

    while True:
        try:
            if not os.path.exists(READY_FILE):
                time.sleep(0.05)
                continue

            flag = open(READY_FILE).read().strip()
            if flag == last_flag:
                time.sleep(0.02)
                continue

            # Parse which eyes are available: e.g. "RL|1712345678900"
            parts = flag.split('|')
            eyes = parts[0]  # "R", "L", or "RL"
            last_flag = flag

            # Send right eye if available
            if 'R' in eyes and os.path.exists(RIGHT_FILE):
                raw = open(RIGHT_FILE, 'rb').read()
                if len(raw) == FRAME_BYTES:
                    send_frame(sock, raw)
                    frames_sent += 1
                    print(f"[icam] Sent RIGHT frame #{frames_sent}")

            # Send left eye if available
            if 'L' in eyes and os.path.exists(LEFT_FILE):
                raw = open(LEFT_FILE, 'rb').read()
                if len(raw) == FRAME_BYTES:
                    send_frame(sock, raw)
                    frames_sent += 1
                    print(f"[icam] Sent LEFT frame #{frames_sent}")

        except BrokenPipeError:
            print("[icam] run_unity.py disconnected.")
            break
        except FileNotFoundError:
            time.sleep(0.05)
        except Exception as e:
            print(f"[icam] Error: {e}")
            time.sleep(0.1)

    sock.close()

if __name__ == "__main__":
    main()