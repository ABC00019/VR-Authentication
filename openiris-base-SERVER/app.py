from flask import Flask, render_template_string
import os
import subprocess
import time
import shutil
import glob

# Import your custom logic
from prep_recognition import move_latest_frames
from match_unity import check_auth, load_gallery

app = Flask(__name__)

# --- CONFIG ---
SDK_ENROLL_DIR = r"C:\Users\kevin\Documents\iCAM TD100 SDK\Enrollment"
SDK_REC_DIR    = r"C:\Users\kevin\Documents\iCAM TD100 SDK\Recognition"
GALLERY_DIR    = r"C:\Users\kevin\Downloads\openiris-base-SERVER\openiris-base-SERVER\dataset1\Enhance"
EXE_PATH       = r"C:\Users\kevin\Downloads\openiris-base-SERVER\openiris-base-SERVER\IcamBridge.exe"

print("[SERVER] Initializing Iris Gallery...")
cached_gallery = load_gallery()

# --- UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Iris System</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #121212; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e1e1e; padding: 2.5rem; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.6); text-align: center; width: 380px; border: 1px solid #333; }
        .pulse { width: 80px; height: 80px; background: {{ color }}; border-radius: 50%; margin: 0 auto 1.5rem; display: flex; align-items: center; justify-content: center; font-size: 2rem; {% if loading %} animation: p 2s infinite; {% endif %} }
        @keyframes p { 0% { transform: scale(0.9); box-shadow: 0 0 0 0 {{ color }}77; } 70% { transform: scale(1); box-shadow: 0 0 0 20px {{ color }}00; } 100% { transform: scale(0.9); } }
        h1 { margin: 0; font-size: 1.5rem; color: {{ color }}; }
        p { color: #888; margin: 10px 0 20px; }
        .data { background: #252525; padding: 10px; border-radius: 8px; font-family: monospace; color: #4ade80; margin-bottom: 15px; font-size: 0.9rem; }
        .btn { display: inline-block; padding: 12px 24px; background: #0078d4; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }
    </style>
    {% if loading %}<meta http-equiv="refresh" content="0; url={{ next_url }}">{% endif %}
</head>
<body>
    <div class="card">
        <div class="pulse">{{ icon }}</div>
        <h1>{{ title }}</h1>
        <p>{{ subtitle }}</p>
        {% if data %}<div class="data">{{ data }}</div>{% endif %}
        {% if not loading %} <a href="/authenticate" class="btn">{{ btn_label }}</a> {% endif %}
    </div>
</body>
</html>
"""

def kill_bridge():
    subprocess.run(["taskkill", "/F", "/IM", "IcamBridge.exe", "/T"], capture_output=True)

def clear_folder(path):
    if os.path.exists(path):
        for f in glob.glob(os.path.join(path, "**", "*.png"), recursive=True):
            try: os.remove(f)
            except: pass

def move_enrollment_logic(name):
    """Recursive search for Enrollment sub-folders."""
    all_pngs = glob.glob(os.path.join(SDK_ENROLL_DIR, "**", "*.png"), recursive=True)

    # FIX: Use startswith to avoid ambiguity.
    # The old check ('L' in filename) was unreliable — both L_Master.png and R_Master.png
    # contain both letters, so l_file and r_file could resolve to the same file.
    l_file = next((f for f in all_pngs if os.path.basename(f).upper().startswith("L_")), None)
    r_file = next((f for f in all_pngs if os.path.basename(f).upper().startswith("R_")), None)

    print(f"[ENROLL] Found L: {l_file}")
    print(f"[ENROLL] Found R: {r_file}")

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

# --- ROUTES ---

@app.route('/authenticate')
def start_auth():
    kill_bridge()
    return render_template_string(HTML_TEMPLATE, loading=True, next_url="/do_auth", title="Verifying Iris", subtitle="Look into the camera", icon="👁️", color="#0078d4")

@app.route('/do_auth')
def do_auth():
    clear_folder(SDK_REC_DIR)
    subprocess.Popen([EXE_PATH, "recognize"])
    timeout, start = 40, time.time()

    while time.time() - start < timeout:
        if move_latest_frames():
            kill_bridge()
            result = check_auth(cached_gallery)
            if result and result['match']:
                return render_template_string(HTML_TEMPLATE, loading=False, title="Access Granted", subtitle="Welcome", data=f"User: {result['identity']}", icon="✅", color="#4ade80", btn_label="Start New Scan")
            else:
                score = result['score'] if result else "N/A"
                return render_template_string(HTML_TEMPLATE, loading=False, title="Access Denied", subtitle="No Match", data=f"Score: {score}", icon="❌", color="#f87171", btn_label="Try Again")
        time.sleep(1)

    kill_bridge()
    return render_template_string(HTML_TEMPLATE, loading=False, title="Timed Out", subtitle="Deactivated", icon="⚠️", color="#fbbf24", btn_label="Try Again")

@app.route('/enroll/<name>')
def start_enroll(name):
    kill_bridge()
    return render_template_string(HTML_TEMPLATE, loading=True, next_url=f"/do_enroll/{name}", title="Enrolling", subtitle=f"Capturing: {name}", icon="👤", color="#0078d4")

@app.route('/do_enroll/<name>')
def do_enroll(name):
    clear_folder(SDK_ENROLL_DIR)
    subprocess.Popen([EXE_PATH, "enroll", name])
    timeout, start = 45, time.time()

    while time.time() - start < timeout:
        if move_enrollment_logic(name):
            global cached_gallery
            cached_gallery = load_gallery()
            return render_template_string(HTML_TEMPLATE, loading=False, title="Success", subtitle="User Enrolled", icon="✅", color="#4ade80", btn_label="Start New Scan")
        time.sleep(1)

    kill_bridge()
    return render_template_string(HTML_TEMPLATE, loading=False, title="Failed", subtitle="No images found", icon="❌", color="#f87171", btn_label="Try Again")

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)