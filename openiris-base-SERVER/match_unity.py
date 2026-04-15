import cv2
import iris
import os
import json
from custom_pipeline import new_pipeline_conf

# --- CONFIG ---
# Paths updated for your SERVER directory structure
GALLERY_DIR     = r"C:\Users\kevin\Downloads\openiris-base-SERVER\openiris-base-SERVER\dataset1"
PROBE_DIR       = r"C:\Users\kevin\Downloads\openiris-base-SERVER\openiris-base-SERVER\dataset2"
ENHANCE_FOLDER  = "Enhance"
MATCH_THRESHOLD = 0.35

# --- PERSISTENT OBJECTS ---
# We initialize these once so the server keeps them in RAM
matcher = iris.HammingDistanceMatcher()
iris_pipeline = iris.IRISPipeline(config=new_pipeline_conf)

def load_gallery():
    """
    Loads all enrolled iris templates into a dictionary.
    Called once when the server starts.
    """
    gallery = {}
    enhance_path = os.path.join(GALLERY_DIR, ENHANCE_FOLDER)
    
    if not os.path.exists(enhance_path):
        print(f"[MATCHER] Error: {enhance_path} missing!")
        return {}

    print("[MATCHER] Loading gallery templates into RAM...")
    for img_name in os.listdir(enhance_path):
        if img_name.lower().endswith(".png"):
            label = os.path.splitext(img_name)[0]
            img_path = os.path.join(enhance_path, img_name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None: continue
            
            output = iris_pipeline(img_data=img, eye_side="left")
            gallery[label] = output['iris_template']
            
    print(f"[MATCHER] Successfully loaded {len(gallery)} templates.")
    return gallery

def check_auth(gallery_templates):
    """
    Compares the newly captured probe images against the loaded gallery.
    Returns a dictionary result for the server to send to Unity.
    """
    probe_path = os.path.join(PROBE_DIR, ENHANCE_FOLDER)
    files = [f for f in os.listdir(probe_path) if f.endswith(".png")]
    
    if not files:
        return None

    best_score, best_label = 1.0, "unknown"

    for f in files:
        img_path = os.path.join(probe_path, f)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None: continue
        
        probe_output = iris_pipeline(img_data=img, eye_side="left")
        probe_code = probe_output['iris_template']

        for label, gal_code in gallery_templates.items():
            score = matcher.run(gal_code, probe_code)
            if score < best_score:
                best_score, best_label = score, label

    # Convert to standard Python types for JSON compatibility
    is_match = bool(best_score < MATCH_THRESHOLD)
    identity = str(best_label.split('_')[0]) if is_match else "unknown"
    
    result = {
        "score": round(float(best_score), 4),
        "match": is_match,
        "identity": identity
    }
    
    # Cleanup: Remove probes so they don't get re-matched next time
    for f in files:
        try: os.remove(os.path.join(probe_path, f))
        except: pass
            
    return result