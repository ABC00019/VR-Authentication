import socket
import struct
import numpy as np
import cv2
import iris
import pickle
import time
from custom_pipeline import new_pipeline_conf

# Ports
SDK_IN_PORT = 5005    # From C# App
UNITY_OUT_PORT = 5000 # To match_unity.py
HOST = '127.0.0.1'

def start_bridge():
    # 1. Initialize Iris Pipeline
    print("[Bridge] Initializing OpenIris Pipeline...")
    iris_pipeline = iris.IRISPipeline(config=new_pipeline_conf)
    
    # 2. Setup Server for C# App
    sdk_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sdk_sock.bind((HOST, SDK_IN_PORT))
    sdk_sock.listen(1)
    
    # 3. Setup Server for match_unity.py
    unity_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    unity_sock.bind((HOST, UNITY_OUT_PORT))
    unity_sock.listen(1)

    print(f"[Bridge] Waiting for C# App on {SDK_IN_PORT}...")
    sdk_conn, _ = sdk_sock.accept()
    print("[Bridge] C# SDK Connected.")

    print(f"[Bridge] Waiting for match_unity.py on {UNITY_OUT_PORT}...")
    unity_conn, _ = unity_sock.accept()
    print("[Bridge] match_unity.py Connected.")

    try:
        while True:
            # Receive image size (4 bytes)
            header = sdk_conn.recv(4)
            if not header: break
            size = struct.unpack('<i', header)[0]

            # Receive image bytes
            img_bytes = b''
            while len(img_bytes) < size:
                chunk = sdk_conn.recv(size - len(img_bytes))
                if not chunk: break
                img_bytes += chunk

            # Convert to image (The iCAM TD100 usually outputs 640x480 grayscale)
            # If the image looks scrambled, try changing shape to (480, 640)
            try:
                frame = np.frombuffer(img_bytes, dtype=np.uint8)
                # iCAM images can sometimes vary; if this crashes, check device specs
                frame = frame.reshape((480, 640)) 
                
                # Process with OpenIris
                output = iris_pipeline(img_data=frame, eye_side="left")
                template = output['iris_template']

                # Send template to match_unity.py
                data = pickle.dumps(template)
                msg_len = struct.pack('>I', len(data))
                unity_conn.sendall(msg_len + data)
                print(f"[Bridge] Template sent to Unity ({len(data)} bytes)")

                # Visual feedback
                cv2.imshow("Bridge Feed (From SDK)", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): break

            except Exception as e:
                print(f"[Bridge] Frame processing error: {e}")

    finally:
        sdk_conn.close()
        unity_conn.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    start_bridge()