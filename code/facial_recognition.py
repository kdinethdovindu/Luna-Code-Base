import requests
import base64
import subprocess
import time
from PIL import Image

class EmotionDetector:
    def __init__(self, api_key, image_path="captured.jpg", compressed_path="compressed.jpg"):
        self.api_key = api_key
        self.original_image_path = image_path
        self.compressed_image_path = compressed_path
        self.api_url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
        self.likelihood_score = {
            "UNKNOWN": 0,
            "VERY_UNLIKELY": 0,
            "UNLIKELY": 1,
            "POSSIBLE": 2,
            "LIKELY": 3,
            "VERY_LIKELY": 4
        }
        self.conflicting_pairs = [("Joy", "Sorrow"), ("Anger", "Surprise")]

    def capture_image(self):
        subprocess.run([
            "libcamera-jpeg", "-o", self.original_image_path,
            "-t", "1000", "--width", "640", "--height", "480", "--quality", "95"
        ])
        time.sleep(1)

    def compress_image(self):
        with Image.open(self.original_image_path) as img:
            img = img.resize((640, 480))
            img.save(self.compressed_image_path, format="JPEG", optimize=True, quality=70)

    def image_to_base64(self):
        with open(self.compressed_image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def get_emotion(self):
        self.capture_image()
        self.compress_image()
        base64_image = self.image_to_base64()

        payload = {
            "requests": [{
                "image": {"content": base64_image},
                "features": [{"type": "FACE_DETECTION"}]
            }]
        }

        try:
            response = requests.post(self.api_url, json=payload)
            result = response.json()

            faces = result["responses"][0].get("faceAnnotations")
            if not faces:
                return "NoFace"

            annotation = faces[0]
            emotion_data = {
                "Joy": annotation.get("joyLikelihood", "UNKNOWN"),
                "Sorrow": annotation.get("sorrowLikelihood", "UNKNOWN"),
                "Anger": annotation.get("angerLikelihood", "UNKNOWN"),
                "Surprise": annotation.get("surpriseLikelihood", "UNKNOWN")
            }

            scored = {
                emotion: self.likelihood_score[likelihood]
                for emotion, likelihood in emotion_data.items()
                if self.likelihood_score[likelihood] >= 2  # Only POSSIBLE or higher
            }

            for e1, e2 in self.conflicting_pairs:
                if e1 in scored and e2 in scored:
                    if scored[e1] > scored[e2]:
                        del scored[e2]
                    else:
                        del scored[e1]

            if scored:
                return max(scored.items(), key=lambda x: x[1])[0]
            else:
                return "Neutral"

        except (KeyError, IndexError, requests.exceptions.RequestException):
            return "NoFace"


if __name__ == "__main__":
    # Put your Google Vision API key here
    API_KEY = "AIzaSyDZ-qp3bV0WS5BywXjL84pYVqyH5TlbZiI"

    detector = EmotionDetector(API_KEY)
    emotion = detector.get_emotion()
    print("Detected emotion:", emotion)
