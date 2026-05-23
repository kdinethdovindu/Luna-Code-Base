import requests
import base64
import json
import subprocess
import time
from PIL import Image

# === CONFIGURATION ===
API_KEY = "AIzaSyDZ-qp3bV0WS5BywXjL84pYVqyH5TlbZiI"  # Your Google Vision API key
ORIGINAL_IMAGE_PATH = "captured.jpg"
COMPRESSED_IMAGE_PATH = "compressed.jpg"
VISION_API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

LIKELY_VALUES = ["LIKELY", "VERY_LIKELY"]

def detect_emotion():
    """Capture image, send to Google Vision API, return detected emotion or None."""

    try:
        # === STEP 1: CAPTURE IMAGE ===
        subprocess.run(["libcamera-jpeg", "-o", ORIGINAL_IMAGE_PATH, "-t", "1000", "--width", "640", "--height", "480"])
        time.sleep(1)

        # === STEP 2: COMPRESS ===
        with Image.open(ORIGINAL_IMAGE_PATH) as img:
            img = img.resize((640, 480))
            img.save(COMPRESSED_IMAGE_PATH, format="JPEG", optimize=True, quality=70)

        # === STEP 3: BASE64 ENCODE ===
        with open(COMPRESSED_IMAGE_PATH, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        # === STEP 4: SEND TO API ===
        payload = {
            "requests": [
                {
                    "image": {"content": base64_image},
                    "features": [{"type": "FACE_DETECTION"}]
                }
            ]
        }
        response = requests.post(VISION_API_URL, json=payload)
        result = response.json()

        emotions = result["responses"][0]["faceAnnotations"][0]
        emotion_data = {
            "joy": emotions["joyLikelihood"],
            "sorrow": emotions["sorrowLikelihood"],
            "anger": emotions["angerLikelihood"],
            "surprise": emotions["surpriseLikelihood"]
        }

        for emotion, likelihood in emotion_data.items():
            if likelihood in LIKELY_VALUES:
                return emotion

        return None

    except Exception as e:
        print(f"[EmotionDetector] Error: {e}")
        return None
