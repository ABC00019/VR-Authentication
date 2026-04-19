from flask import Flask, jsonify, request
import os
import subprocess
import time
import shutil
import glob

# custom logic (Make sure these .py files are in the same folder)
from prep_recognition import move_latest_frames
from match_unity import check_auth, load_gallery

newapp = Flask(__name__)

# --- CONFIG ---
SDK_ENROLL_DIR = r"C:\Users\kevin\Documents\iCAM TD100 SDK\Enrollment"
SDK_REC_DIR    = r"C:\Users\kevin\Documents\iCAM TD100 SDK\Recognition"
GALLERY_DIR    = r"C:\Users\kevin\Downloads\openiris-base-SERVER\openiris-base-SERVER\dataset1\Enhance"
EXE_PATH       = r"C:\Users\kevin\Downloads\openiris-base-SERVER\openiris-base-SERVER\IcamBridge.exe"

print("[SERVER] Initializing Iris Gallery...")
cached_gallery = load_gallery()

# --- HELPER FUNCTIONS ---

def kill_bridge():
    subprocess.run(["taskkill", "/F", "/IM", "IcamBridge.exe", "/T"], capture_output=True)

def clear_folder(path):
    if os.path.exists(path):
        for f in glob.glob(os.path.join(path, "**", "*.png"), recursive=True):
            try: os.remove(f)
            except: pass

def move_enrollment_logic(name):
    all_pngs = glob.glob(os.path.join(SDK_ENROLL_DIR, "**", "*.png"), recursive=True)
    l_file = next((f for f in all_pngs if os.path.basename(f).upper().startswith("L_")), None)
    r_file = next((f for f in all_pngs if os.path.basename(f).upper().startswith("R_")), None)

    if l_file and r_file:
        kill_bridge()
        time.sleep(1)
        try:
            shutil.move(l_file, os.path.join(GALLERY_DIR, f"{name}_L.png"))
            shutil.move(r_file, os.path.join(GALLERY_DIR, f"{name}_R.png"))
            return True
        except Exception as e:
            print(f"[ENROLL ERROR] {e}")
    return False

# --- API ROUTES ---

@newapp.route('/api/enroll/<name>', methods=['POST', 'GET'])
def api_enroll(name):
    print(f"[API] Enrollment request for: {name}")
    clear_folder(SDK_ENROLL_DIR)
    subprocess.Popen([EXE_PATH, "enroll", name])
    
    timeout, start = 45, time.time()
    while time.time() - start < timeout:
        if move_enrollment_logic(name):
            global cached_gallery
            cached_gallery = load_gallery()
            return jsonify({"status": "success", "message": f"User {name} enrolled."}), 200
        time.sleep(1)
    
    kill_bridge()
    return jsonify({"status": "timeout", "message": "Enrollment timed out."}), 408

@newapp.route('/api/authenticate', methods=['POST', 'GET'])
def api_authenticate():
    print("[API] Authentication request received")
    clear_folder(SDK_REC_DIR)
    subprocess.Popen([EXE_PATH, "recognize"])
    
    timeout, start = 40, time.time()
    while time.time() - start < timeout:
        if move_latest_frames():
            kill_bridge()
            result = check_auth(cached_gallery)
            if result and result['match']:
                return jsonify({
                    "status": "success", 
                    "identity": result['identity'],
                    "score": result['score']
                }), 200
            else:
                return jsonify({"status": "denied", "message": "No match found."}), 401
        time.sleep(1)
    
    kill_bridge()
    return jsonify({"status": "timeout", "message": "Authentication timed out."}), 408

@newapp.route('/api/user_exists/<name>', methods=['GET'])
def api_user_exists(name):
    """Check if iris enrollment files exist for this user."""
    l_path = os.path.join(GALLERY_DIR, f"{name}_L.png")
    r_path = os.path.join(GALLERY_DIR, f"{name}_R.png")
    exists = os.path.exists(l_path) and os.path.exists(r_path)
    return jsonify({"exists": exists, "username": name}), 200


@newapp.route('/api/delete_user/<name>', methods=['POST', 'DELETE'])
def api_delete_user(name):
    """Remove iris enrollment files for this user."""
    l_path = os.path.join(GALLERY_DIR, f"{name}_L.png")
    r_path = os.path.join(GALLERY_DIR, f"{name}_R.png")
    deleted = []

    for path in [l_path, r_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted.append(os.path.basename(path))
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

    # Refresh the in-memory gallery
    global cached_gallery
    cached_gallery = load_gallery()

    return jsonify({"status": "success", "deleted": deleted}), 200

if __name__ == "__main__":
    print("Server starting on http://127.0.0.1:5000")
    newapp.run(host='127.0.0.1', port=5000, debug=True)
