import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import torch
from transformers import pipeline

# Load AI image detector model
print("Loading AI detection model... (first time takes 1-2 minutes)")
ai_detector = pipeline(
    "image-classification",
    model="umm-maybe/AI-image-detector"
)
print("Model loaded!")

def download_image(image_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(image_url, headers=headers, timeout=10)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    return img

def pixel_analysis(img):
    """Check for AI artifacts using pixel-level analysis"""
    img_array = np.array(img)
    
    # Check 1: Noise pattern analysis
    # AI images tend to have very uniform noise
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    noise = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Check 2: Color smoothness
    # AI faces tend to have unnaturally smooth skin
    blur = cv2.GaussianBlur(img_array, (5, 5), 0)
    smoothness = np.mean(np.abs(img_array.astype(float) - blur.astype(float)))
    
    # Check 3: Edge analysis
    # AI images have very clean edges
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges > 0) / edges.size
    
    print(f"Noise variance: {noise:.2f}")
    print(f"Smoothness score: {smoothness:.2f}")
    print(f"Edge density: {edge_density:.4f}")
    
    # Score based on thresholds
    ai_signals = 0
    
    if noise < 100:      # very low noise = AI
        ai_signals += 1
    if smoothness < 8:   # very smooth = AI
        ai_signals += 1
    if edge_density < 0.05:  # very clean edges = AI
        ai_signals += 1
    
    return {
        "ai_signals": ai_signals,
        "noise": round(noise, 2),
        "smoothness": round(smoothness, 2),
        "edge_density": round(edge_density, 4)
    }

def detect_ai_image(image_url):
    try:
        # Download image
        img = download_image(image_url)
        
        # Method 1: Pixel analysis
        pixel_result = pixel_analysis(img)
        
        # Method 2: AI model prediction
        model_result = ai_detector(img)
        print(f"Model result: {model_result}")
        
        # Extract AI probability from model
        ai_prob = 0
        for item in model_result:
            if "artificial" in item["label"].lower() or "fake" in item["label"].lower() or "ai" in item["label"].lower():
                ai_prob = item["score"]
                break
        
        print(f"AI probability from model: {ai_prob:.2%}")
        print(f"Pixel AI signals: {pixel_result['ai_signals']}/3")
        
        # Combined decision
        if ai_prob > 0.75 and pixel_result["ai_signals"] >= 2:
            verdict = "🤖 Very likely AI Generated"
            is_ai = True
            confidence = round(ai_prob * 100, 1)
        elif ai_prob > 0.60 or pixel_result["ai_signals"] >= 2:
            verdict = "🔍 Possibly AI Generated"
            is_ai = True
            confidence = round(ai_prob * 100, 1)
        else:
            verdict = "✅ Looks like a real photo"
            is_ai = False
            confidence = round((1 - ai_prob) * 100, 1)
        
        return {
            "is_ai": is_ai,
            "verdict": verdict,
            "confidence": confidence,
            "ai_probability": round(ai_prob * 100, 1),
            "pixel_signals": pixel_result["ai_signals"]
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            "is_ai": None,
            "verdict": f"Could not analyze image",
            "confidence": 0
        }

# Replace the test section at the bottom with these tests:

print("\nTest 1 - AI Generated face (thispersondoesnotexist):")
result1 = detect_ai_image("https://thispersondoesnotexist.com/")
print(result1)

print("\nTest 2 - Real photo:")
result2 = detect_ai_image("https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400")
print(result2)

print("\nTest 3 - Another real photo:")
result3 = detect_ai_image("https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400")
print(result3)