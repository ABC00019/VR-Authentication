import os
import shutil
import socket

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
SOURCE_BASE = r"C:\Users\kevin\Documents\iCAM TD100 SDK\Enrollment"
DEST_DIR    = r"C:\Users\kevin\Downloads\openiris-base\openiris-base\dataset1\Enhance"
BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 5002  # The port your C++ or C# bridge listens on for "DONE"
# ─────────────────────────────────────────────

def stop_camera():
    """Sends a signal to the bridge to stop polling immediately."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((BRIDGE_HOST, BRIDGE_PORT))
            s.sendall(b"DONE\n")
            print("[*] Sent STOP signal to camera bridge.")
    except Exception as e:
        print(f"[!] Note: Could not send stop signal: {e}")

def enroll_dual(name):
    subject_path = os.path.join(SOURCE_BASE, name)
    if not os.path.exists(subject_path):
        print(f"[ERROR] Enrollment folder not found for: {name}")
        return

    # Filter for Left and Right images
    l_files = [os.path.join(subject_path, f) for f in os.listdir(subject_path) 
               if f.upper().startswith('L_') and f.endswith('.png')]
    r_files = [os.path.join(subject_path, f) for f in os.listdir(subject_path) 
               if f.upper().startswith('R_') and f.endswith('.png')]

    if l_files and r_files:
        # Select the most recent sharp frame for each eye
        best_l = max(l_files, key=os.path.getmtime)
        best_r = max(r_files, key=os.path.getmtime)

        # Copy and rename to your permanent database
        shutil.copy2(best_l, os.path.join(DEST_DIR, f"{name}_L.png"))
        shutil.copy2(best_r, os.path.join(DEST_DIR, f"{name}_R.png"))
        
        print(f"[SUCCESS] {name} enrolled with dual-eye templates.")
        
        # Signal the hardware to stop
        stop_camera()
        
        # Wipe the temporary SDK enrollment folder
        try:
            shutil.rmtree(subject_path)
            print(f"[*] Temporary enrollment data for {name} deleted.")
        except Exception as e:
            print(f"[!] Cleanup failed: {e}")
            
        print(f"\n[!] Done. Restart match_unity.py to recognize {name}.")
    else:
        print(f"[ERROR] Could not find both a Left and Right eye image in {subject_path}.")

if __name__ == "__main__":
    subject_name = input("Enter the name of the person you just enrolled: ").strip()
    if subject_name:
        enroll_dual(subject_name)
    else:
        print("Invalid name.")