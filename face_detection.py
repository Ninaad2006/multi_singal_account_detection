import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
def check_face_in_profile_pic(image_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(image_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"has_face": None, "verdict": "Could not download image"}

        img = Image.open(BytesIO(response.content)).convert("RGB")
        
        # Resize to larger size for better detection
        img = img.resize((300, 300), Image.LANCZOS)
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Improve contrast
        gray = cv2.equalizeHist(gray)

        # Try multiple cascades
        cascades = [
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml',
            cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml',
            cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml',
            cv2.data.haarcascades + 'haarcascade_profileface.xml',
        ]

        for cascade_path in cascades:
            cascade = cv2.CascadeClassifier(cascade_path)
            
            # Try with relaxed settings
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,   # more thorough scan
                minNeighbors=3,     # less strict
                minSize=(20, 20),   # smaller minimum face size
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(faces) > 0:
                return {
                    "has_face": True,
                    "verdict": "✅ Real human face detected"
                }

        # If no face found try with even more relaxed settings
        main_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = main_cascade.detectMultiScale(
            gray,
            scaleFactor=1.03,
            minNeighbors=2,
            minSize=(15, 15)
        )

        if len(faces) > 0:
            return {
                "has_face": True,
                "verdict": "✅ Real human face detected"
            }

        return {
            "has_face": False,
            "verdict": "⚠️ No human face detected"
        }

    except Exception as e:
        return {"has_face": None, "verdict": "Could not analyze"}
