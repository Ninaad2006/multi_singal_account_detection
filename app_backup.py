from flask import Flask, request, jsonify, render_template_string
import pickle
import pandas as pd
import requests
import re
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from transformers import pipeline
from datetime import datetime
from clone_detection import full_clone_check
from spam_detector import detect_spam_keywords
from database import save_analysis, get_history, get_stats, delete_history, add_monitored_account, remove_monitored_account, get_monitored_accounts, get_alerts
from monitor import start_monitoring
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

model = pickle.load(open("fake_detector_model.pkl", "rb"))

RAPIDAPI_KEY = "241acbfa2amsh04e4cb5dec6276bp13e117jsn494bed62103b"
SERPAPI_KEY = "YpQN1QAENdqQ4Wk8ZWaDkbdW"  # get free key at serpapi.com
INSTAGRAM_HOST = "instagram120.p.rapidapi.com"
TWITTER_HOST = "twitter-api47.p.rapidapi.com"

# Load face detector
print("Loading face detector...")
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# Load AI image detector
print("Loading AI detection model...")
ai_detector = pipeline(
    "image-classification",
    model="umm-maybe/AI-image-detector"
)
print("All models loaded!")



def check_face_in_profile_pic(image_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(image_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"has_face": None, "verdict": "Could not download image"}
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))
        face_count = len(faces)
        return {
            "has_face": face_count > 0,
            "verdict": "✅ Real human face detected" if face_count > 0 else "⚠️ No human face detected"
        }
    except Exception as e:
        return {"has_face": None, "verdict": f"Could not analyze"}

def check_ai_generated(image_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(image_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"is_ai": None, "verdict": "⚪ Could not analyze image"}
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        noise = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur = cv2.GaussianBlur(img_array, (5, 5), 0)
        smoothness = np.mean(np.abs(img_array.astype(float) - blur.astype(float)))
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        pixel_ai_signals = sum([noise < 80, smoothness < 5, edge_density < 0.03])
        model_result = ai_detector(img)
        ai_prob = next((item["score"] for item in model_result if "artificial" in item["label"].lower()), 0)
        if ai_prob > 0.75 and pixel_ai_signals >= 2:
            verdict = "🤖 Likely AI Generated (experimental)"
            is_ai = True
        elif ai_prob > 0.60 or pixel_ai_signals >= 3:
            verdict = "🔍 Possibly AI Generated (experimental)"
            is_ai = True
        else:
            verdict = "✅ Looks like a real photo (experimental)"
            is_ai = False
        return {"is_ai": is_ai, "verdict": verdict, "ai_probability": round(ai_prob * 100, 1)}
    except Exception as e:
        return {"is_ai": None, "verdict": "⚪ Could not analyze image"}

def get_instagram_data(username):
    url = f"https://{INSTAGRAM_HOST}/api/instagram/userInfo"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": INSTAGRAM_HOST,
        "Content-Type": "application/json"
    }
    body = {"username": username}
    response = requests.post(url, headers=headers, json=body)
    data = response.json()
    print("RAW RESPONSE KEYS:", data.keys() if isinstance(data, dict) else type(data))
    return data

def get_x_data(username):
    url = f"https://{TWITTER_HOST}/v3/user/by-username"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": TWITTER_HOST}
    params = {"username": username}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def analyze_instagram(username):
    profile = get_instagram_data(username)
    if not profile or "error" in profile:
        return None, "Account not found or is private"
    user = profile.get("data", profile)
    # New API returns data under result[0]['user']
    if "result" in profile and len(profile["result"]) > 0:
        user = profile["result"][0].get("user", {})
    else:
        return None, "Account not found or is private"

    # Extract features using correct field names
    followers = user.get("follower_count", 0)
    following = user.get("following_count", 0)
    posts = user.get("media_count", 0)
    bio = user.get("biography", "") or ""
    has_pic = 0 if user.get("has_anonymous_profile_picture", True) else 1
    is_verified = 1 if user.get("is_verified", False) else 0
    is_private = 1 if user.get("is_private", False) else 0
    bio_length = len(bio)
    ff_ratio = followers / max(following, 1)
    username_str = user.get("username", username)
    num_ratio = len(re.findall(r'\d', username_str)) / max(len(username_str), 1)
    profile_pic_url = user.get("profile_pic_url", "")

    # Account age - not available in this API so skip
    account_age_days = 0
    account_age_str = "Unknown"

    # Engagement rate
    avg_likes = user.get("avg_likes", 0) or 0
    engagement_rate = round((avg_likes / followers) * 100, 2) if followers > 0 and posts > 0 else 0
    if engagement_rate == 0:
        engagement_verdict = "⚪ No data available"
    elif engagement_rate >= 6:
        engagement_verdict = "✅ Excellent engagement"
    elif engagement_rate >= 3:
        engagement_verdict = "✅ Good engagement"
    elif engagement_rate >= 1:
        engagement_verdict = "⚠️ Low engagement"
    else:
        engagement_verdict = "🚨 Very low engagement (possible fake)"

    face_result = check_face_in_profile_pic(profile_pic_url) if profile_pic_url else {"has_face": None, "verdict": "No profile picture"}
    ai_result = check_ai_generated(profile_pic_url) if profile_pic_url else {"is_ai": None, "verdict": "⚪ No profile picture"}

    # Clone detection
    clone_result = full_clone_check(
        username=username_str,
        bio=bio,
        profile_pic_url=profile_pic_url,
        serpapi_key=SERPAPI_KEY
    )
    # Spam detection
    spam_result = detect_spam_keywords(bio, username_str)

    spam_verdict = spam_result["verdict"]
    

    # Smart scoring
    if is_verified:
        final_prediction = "real"
        confidence = 99.9
    else:
        fake_score = 0
        real_score = 0
        if has_pic: real_score += 10
        else: fake_score += 20
        if posts >= 12: real_score += 20
        elif posts >= 3: real_score += 10
        elif posts == 0: fake_score += 25
        else: real_score += 3
        if bio_length >= 20: real_score += 15
        elif bio_length > 0: real_score += 7
        else: fake_score += 10
        if face_result.get("has_face"): real_score += 20
        elif face_result.get("has_face") is False: fake_score += 10
        if followers >= 200: real_score += 20
        elif followers >= 50: real_score += 12
        elif followers >= 10: real_score += 5
        else: fake_score += 15
        if ff_ratio >= 0.3: real_score += 15
        elif ff_ratio < 0.05: fake_score += 30
        elif ff_ratio < 0.1: fake_score += 15
        if following > 2000 and followers < 50: fake_score += 40
        if num_ratio > 0.5: fake_score += 20
        elif num_ratio > 0.3: fake_score += 10
        elif num_ratio == 0: real_score += 5
        if is_private and posts > 0 and followers > 10: real_score += 10
        # Account age signals
        if account_age_days > 0:
            if account_age_days < 30:
                fake_score += 30  # very new account
            elif account_age_days < 90:
                fake_score += 15  # fairly new
            elif account_age_days > 365:
                real_score += 20  # established account
        # Engagement signals
        if engagement_rate > 0:
            if engagement_rate < 0.5:
                fake_score += 20  # suspiciously low
            elif engagement_rate >= 3:
                real_score += 15  # healthy engagement
        # Spam signals
        if spam_result["spam_score"] >= 60:
            fake_score += 30
        elif spam_result["spam_score"] >= 30:
            fake_score += 15
        total = max(real_score + fake_score, 1)
        real_pct = real_score / total
        if real_pct >= 0.60:
            final_prediction = "real"
            confidence = round(50 + real_pct * 50, 1)
        elif real_pct <= 0.40:
            final_prediction = "fake"
            confidence = round(50 + (1 - real_pct) * 50, 1)
        else:
            final_prediction = "fake" if not has_pic and posts == 0 else "real"
            confidence = 60.0

    # Calculate risk score 0-100
    if final_prediction == "fake":
        risk_score = min(100, round((1 - real_pct) * 100)) if not is_verified else 5
    else:
        risk_score = max(0, round((1 - real_pct) * 100)) if not is_verified else 5

    # Risk level label
    if risk_score >= 75:
        risk_level = "🔴 High Risk"
        risk_color = "#cc0000"
    elif risk_score >= 45:
        risk_level = "🟡 Medium Risk"
        risk_color = "#ff9900"
    else:
        risk_level = "🟢 Low Risk"
        risk_color = "#006600"

    return {
        "platform": "instagram",
        "prediction": final_prediction,
        "confidence": confidence,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "face": face_result,
        "clone": clone_result,
        "ai_image": ai_result,
        "spam": spam_result,
        "account_age_days": account_age_days,
        "account_age_str": account_age_str,
        "engagement_rate": engagement_rate,
        "engagement_verdict": engagement_verdict,   
        "data": {
            "username": username_str,
            "followers": followers,
            "following": following,
            "posts": posts,
            "bio_length": bio_length,
            "has_pic": bool(has_pic),
            "is_verified": bool(is_verified),
            "is_private": bool(is_private),
            "profile_pic_url": profile_pic_url,
            "account_age_str": account_age_str,
            "account_age_days": account_age_days,
            "engagement_rate": engagement_rate,
            "engagement_verdict": engagement_verdict
        }
    }, None

def analyze_x(username):
    profile = get_x_data(username)
    if not profile or "data" not in profile:
        return None, "Account not found"
    user = profile["data"]
    followers = user.get("followerCount", 0)
    following = user.get("followingCount", 0)
    tweets = user.get("tweetCount", 0)
    bio = user.get("bio", "") or ""
    is_verified = 1 if user.get("isBlueVerified") or user.get("verified") else 0
    is_protected = 1 if user.get("isProtected") else 0
    has_pic = 0 if user.get("defaultProfileImage") else 1
    bio_length = len(bio)
    ff_ratio = followers / max(following, 1)
    username_str = user.get("username", username)
    num_ratio = len(re.findall(r'\d', username_str)) / max(len(username_str), 1)
    profile_pic_url = user.get("avatar", "")
    face_result = check_face_in_profile_pic(profile_pic_url) if profile_pic_url else {"has_face": None, "verdict": "No profile picture"}
    ai_result = check_ai_generated(profile_pic_url) if profile_pic_url else {"is_ai": None, "verdict": "⚪ No profile picture"}

    # Account age
    created_at = user.get("createdAt", "")
    account_age_days = 0
    if created_at:
        try:
            created = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            account_age_days = (datetime.now() - created).days
        except:
            pass
    tweet_frequency = tweets / max(account_age_days, 1) * 30  # tweets per month
    # Clone detection
    clone_result = full_clone_check(
        username=username_str,
        bio=bio,
        profile_pic_url=profile_pic_url,
        serpapi_key=SERPAPI_KEY
    )
    # Spam detection
    spam_result = detect_spam_keywords(bio, username_str)

    # Smart scoring for X
    if is_verified:
        final_prediction = "real"
        confidence = 99.9
    else:
        fake_score = 0
        real_score = 0
        if has_pic: real_score += 10
        else: fake_score += 20
        if tweets >= 100: real_score += 20
        elif tweets >= 20: real_score += 10
        elif tweets == 0: fake_score += 25
        else: real_score += 3
        if bio_length >= 20: real_score += 15
        elif bio_length > 0: real_score += 7
        else: fake_score += 10
        if face_result.get("has_face"): real_score += 20
        elif face_result.get("has_face") is False: fake_score += 10
        if followers >= 500: real_score += 20
        elif followers >= 100: real_score += 12
        elif followers >= 20: real_score += 5
        else: fake_score += 15
        if ff_ratio >= 0.3: real_score += 15
        elif ff_ratio < 0.05: fake_score += 30
        elif ff_ratio < 0.1: fake_score += 15
        if account_age_days > 365: real_score += 20
        elif account_age_days > 90: real_score += 10
        else: fake_score += 15
        if tweet_frequency > 1000: fake_score += 20  # bot-like posting
        if num_ratio > 0.5: fake_score += 20
        elif num_ratio == 0: real_score += 5
        # Spam signals
        if spam_result["spam_score"] >= 60: fake_score += 30
        elif spam_result["spam_score"] >= 30: fake_score += 15
        total = max(real_score + fake_score, 1)
        real_pct = real_score / total
        if real_pct >= 0.60:
            final_prediction = "real"
            confidence = round(50 + real_pct * 50, 1)
        elif real_pct <= 0.40:
            final_prediction = "fake"
            confidence = round(50 + (1 - real_pct) * 50, 1)
        else:
            final_prediction = "fake" if not has_pic and tweets == 0 else "real"
            confidence = 60.0
    # Calculate risk score
    if final_prediction == "fake":
        risk_score = min(100, round((1 - real_pct) * 100)) if not is_verified else 5
    else:
        risk_score = max(0, round((1 - real_pct) * 100)) if not is_verified else 5

    if risk_score >= 75:
        risk_level = "🔴 High Risk"
        risk_color = "#cc0000"
    elif risk_score >= 45:
        risk_level = "🟡 Medium Risk"
        risk_color = "#ff9900"
    else:
        risk_level = "🟢 Low Risk"
        risk_color = "#006600"
   
    return {
        "platform": "x",
        "prediction": final_prediction,
        "confidence": confidence,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "face": face_result,
        "clone": clone_result,
        "ai_image": ai_result,
        "spam": spam_result,
        "data": {
            "username": username_str,
            "followers": followers,
            "following": following,
            "tweets": tweets,
            "bio_length": bio_length,
            "has_pic": bool(has_pic),
            "is_verified": bool(is_verified),
            "is_protected": bool(is_protected),
            "account_age_days": account_age_days,
            "tweet_frequency": round(tweet_frequency, 1),
            "profile_pic_url": profile_pic_url 
        }
    }, None
# Start background monitoring
monitoring_thread = start_monitoring(analyze_instagram, analyze_x, interval_minutes=30)
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Fake Account Detector</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial; max-width: 650px; margin: 50px auto; padding: 20px; background: #fafafa; }
        h1 { text-align: center; margin-bottom: 5px; color: #333; }
        p.sub { text-align:center; color:#888; margin-bottom: 25px; }
        .platform-selector { display: flex; gap: 10px; margin-bottom: 15px; }
        .platform-btn { flex: 1; padding: 10px; border: 2px solid #ddd; background: white; cursor: pointer; border-radius: 8px; font-size: 15px; font-weight: bold; }
        .platform-btn.active-instagram { border-color: #E1306C; background: #fff0f5; color: #E1306C; }
        .platform-btn.active-x { border-color: #000; background: #f0f0f0; color: #000; }
        .input-group { display: flex; gap: 10px; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 15px; }
        button#analyzeBtn { padding: 12px 20px; border: none; cursor: pointer; border-radius: 5px; font-size: 15px; color: white; }
        .instagram-theme { background: #E1306C; }
        .x-theme { background: #000; }
        .loading { text-align: center; margin-top: 20px; color: #888; display: none; }
        .result { margin-top: 20px; padding: 20px; border-radius: 8px; font-size: 22px; text-align: center; font-weight: bold; }
        .fake { background: #ffcccc; color: #cc0000; }
        .real { background: #ccffcc; color: #006600; }
        .warning { background: #fff3cd; color: #856404; font-size: 16px; }
        .details { margin-top: 15px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; }
        .details p { margin: 8px 0; font-size: 14px; }
        .confidence { font-size: 14px; font-weight: normal; margin-top: 5px; opacity: 0.8; }
        .section-title { font-weight: bold; color: #555; margin: 12px 0 5px 0; font-size: 13px; text-transform: uppercase; }
        .experimental { font-size: 11px; color: #888; margin-top: 3px; }
        .platform-badge { display: inline-block; padding: 3px 8px; border-radius: 10px; font-size: 12px; margin-bottom: 5px; }
        .badge-instagram { background: #E1306C; color: white; }
        .badge-x { background: #000; color: white; }
    </style>
</head>
<body>
    <h1>🔍 Fake Account Detector</h1>
    <p class="sub">Analyze Instagram and X accounts instantly</p>

    <div class="platform-selector">
        <button class="platform-btn active-instagram" id="btn-instagram" onclick="selectPlatform('instagram')">
            📸 Instagram
        </button>
        <button class="platform-btn" id="btn-x" onclick="selectPlatform('x')">
            𝕏 X (Twitter)
        </button>
    </div>

    <div class="input-group">
        <input type="text" id="username" placeholder="Enter username">
        <button id="analyzeBtn" class="instagram-theme" onclick="predict()">Analyze</button>
    </div>

    <div id="loading" class="loading">⏳ Analyzing account...</div>
    <div id="result"></div>

    <div style="margin-top:20px;text-align:center;display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
        <button onclick="showHistory()" style="background:#6c757d;color:white;padding:8px 16px;border:none;border-radius:5px;cursor:pointer;font-size:13px;">
            📋 View History
        </button>
        <button onclick="clearHistory()" style="background:#dc3545;color:white;padding:8px 16px;border:none;border-radius:5px;cursor:pointer;font-size:13px;">
            🗑️ Clear History
        </button>
        <button onclick="toggleCompare()" style="background:#6f42c1;color:white;padding:8px 16px;border:none;border-radius:5px;cursor:pointer;font-size:13px;">
            ⚖️ Compare Accounts
        </button>
    </div>

    <div id="history-panel" style="display:none;margin-top:20px;"></div>

    <div id="compare-panel" style="display:none;margin-top:20px;background:white;padding:15px;border-radius:8px;border:1px solid #ddd;">
        <p style="font-weight:bold;margin-bottom:10px;">⚖️ Compare Two Accounts</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
            <input type="text" id="compare-user1" placeholder="First username" style="padding:10px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
            <input type="text" id="compare-user2" placeholder="Second username" style="padding:10px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
        </div>
        <button onclick="runComparison()" style="background:#6f42c1;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;width:100%;font-size:15px;">
            ⚖️ Compare
        </button>
        <div id="compare-results" style="margin-top:15px;"></div>
    </div>
<div style="margin-top:10px;text-align:center;">
        <button onclick="toggleMonitoring()" style="background:#28a745;color:white;padding:8px 16px;border:none;border-radius:5px;cursor:pointer;font-size:13px;">
            👁️ Monitor Accounts
        </button>
    </div>

    <div id="monitor-panel" style="display:none;margin-top:20px;background:white;padding:15px;border-radius:8px;border:1px solid #ddd;">
        <p style="font-weight:bold;margin-bottom:10px;">👁️ Real-Time Monitoring</p>
        <p style="font-size:12px;color:#888;margin-bottom:10px;">Add accounts to monitor. App checks every 30 minutes and alerts you of suspicious changes.</p>
        <div style="display:flex;gap:10px;margin-bottom:10px;">
            <input type="text" id="monitor-username" placeholder="Username to monitor" style="flex:1;padding:10px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
            <button onclick="addToMonitoring()" style="background:#28a745;color:white;padding:10px 15px;border:none;border-radius:5px;cursor:pointer;">
                + Add
            </button>
        </div>
        <button onclick="loadMonitoringStatus()" style="background:#6c757d;color:white;padding:8px 16px;border:none;border-radius:5px;cursor:pointer;font-size:13px;margin-bottom:15px;">
            🔄 Refresh Status
        </button>
        <div id="monitor-status"></div>
    </div>
<script>
let currentPlatform = 'instagram';

function selectPlatform(platform) {
    currentPlatform = platform;
    document.getElementById('btn-instagram').className = 'platform-btn' + (platform === 'instagram' ? ' active-instagram' : '');
    document.getElementById('btn-x').className = 'platform-btn' + (platform === 'x' ? ' active-x' : '');
    document.getElementById('analyzeBtn').className = platform === 'instagram' ? 'instagram-theme' : 'x-theme';
    document.getElementById('username').placeholder = platform === 'instagram' ? 'Enter Instagram username' : 'Enter X username';
}

async function predict() {
    const username = document.getElementById('username').value.trim();
    if (!username) { alert('Please enter a username!'); return; }
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').innerHTML = '';

    const response = await fetch('/predict', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: username, platform: currentPlatform})
    });
    const result = await response.json();
    document.getElementById('loading').style.display = 'none';

    if (result.error) {
        document.getElementById('result').innerHTML =
            '<div class="result warning">⚠️ ' + result.error + '</div>';
        return;
    }

    const emoji = result.prediction === 'fake' ? '🚨' : '✅';
    const label = result.prediction === 'fake' ? 'Fake Account' : 'Real Account';
    const badgeClass = result.platform === 'instagram' ? 'badge-instagram' : 'badge-x';
    const badgeLabel = result.platform === 'instagram' ? '📸 Instagram' : '𝕏 X';

    let platformDetails = '';
    if (result.platform === 'instagram') {
        platformDetails =
            '<p>📸 <b>Posts:</b> ' + result.data.posts + '</p>' +
            '<p>🔒 <b>Private:</b> ' + (result.data.is_private ? 'Yes' : 'No') + '</p>' +
            '<p>📅 <b>Account Age:</b> ' + (result.data.account_age_str || 'Unknown') + '</p>' +
            '<p>💬 <b>Engagement Rate:</b> ' + (result.data.engagement_rate || 0) + '% — ' + (result.data.engagement_verdict || 'No data') + '</p>';
    } else {
        platformDetails =
            '<p>🐦 <b>Tweets:</b> ' + result.data.tweets.toLocaleString() + '</p>' +
            '<p>📅 <b>Account Age:</b> ' + Math.floor(result.data.account_age_days / 365) + ' years, ' + Math.floor((result.data.account_age_days % 365) / 30) + ' months</p>' +
            '<p>📊 <b>Tweet Frequency:</b> ' + result.data.tweet_frequency + ' tweets/month</p>' +
            '<p>🔒 <b>Protected:</b> ' + (result.data.is_protected ? 'Yes' : 'No') + '</p>';
    }

    let profilePic = result.data.profile_pic_url ?
        '<div style="text-align:center;margin-bottom:15px;"><img src="/proxy-image?url=' + encodeURIComponent(result.data.profile_pic_url) + '" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid #ddd;" alt="Profile"></div>'
        : '';

    let cloneVerdict = result.clone ? result.clone.verdict : 'Not checked';
    let cloneSignals = (result.clone && result.clone.signals && result.clone.signals.length > 0) ?
        '<p style="color:#cc0000;font-size:13px">⚠️ Signals: ' + result.clone.signals.join(", ") + '</p>' : '';

    let spamVerdict = result.spam ? result.spam.verdict : 'Not checked';
    let spamKeywords = (result.spam && result.spam.found_keywords && result.spam.found_keywords.length > 0) ?
        '<p style="color:#cc0000;font-size:13px">🔑 Keywords: ' + result.spam.found_keywords.join(", ") + '</p>' : '';

    let spamScore = result.spam ? result.spam.spam_score : 0;
    let spamColor = spamScore >= 60 ? '#cc0000' : spamScore >= 30 ? '#ff9900' : '#4CAF50';
    let spamMeter =
        '<div style="margin-bottom:15px;">' +
            '<div style="display:flex;justify-content:space-between;margin-bottom:3px;">' +
                '<span style="font-size:13px;font-weight:bold;">Spam Score</span>' +
                '<span style="font-size:13px;color:' + spamColor + '">' + spamScore + '/100</span>' +
            '</div>' +
            '<div style="background:#eee;border-radius:10px;height:12px;overflow:hidden;">' +
                '<div style="width:' + spamScore + '%;background:' + spamColor + ';height:100%;border-radius:10px;"></div>' +
            '</div>' +
        '</div>';

    let riskColor = result.risk_color || '#888';
    let riskScore = result.risk_score || 0;
    let riskMeter =
        '<div style="margin-bottom:20px;">' +
            '<div style="display:flex;justify-content:space-between;margin-bottom:5px;">' +
                '<span style="font-weight:bold;font-size:14px;">Risk Score</span>' +
                '<span style="font-weight:bold;color:' + riskColor + '">' + (result.risk_level || '') + '</span>' +
            '</div>' +
            '<div style="background:#eee;border-radius:10px;height:20px;overflow:hidden;">' +
                '<div style="width:' + riskScore + '%;background:' + riskColor + ';height:100%;border-radius:10px;transition:width 1s ease;"></div>' +
            '</div>' +
            '<div style="display:flex;justify-content:space-between;font-size:11px;color:#888;margin-top:3px;">' +
                '<span>0 - Safe</span>' +
                '<span>' + riskScore + '/100</span>' +
                '<span>100 - Dangerous</span>' +
            '</div>' +
        '</div>';

    document.getElementById('result').innerHTML =
        '<div class="result ' + result.prediction + '">' +
            '<span class="platform-badge ' + badgeClass + '">' + badgeLabel + '</span><br>' +
            emoji + ' ' + label +
            '<div class="confidence">Confidence: ' + result.confidence + '%</div>' +
        '</div>' +
        '<div class="details">' +
            profilePic +
            riskMeter +
            '<p class="section-title">Profile Info</p>' +
            '<p>👤 <b>Username:</b> ' + result.data.username + '</p>' +
            '<p>👥 <b>Followers:</b> ' + result.data.followers.toLocaleString() + '</p>' +
            '<p>➡️ <b>Following:</b> ' + result.data.following.toLocaleString() + '</p>' +
            '<p>📝 <b>Bio Length:</b> ' + result.data.bio_length + ' characters</p>' +
            '<p>🖼️ <b>Profile Picture:</b> ' + (result.data.has_pic ? 'Yes ✅' : 'No ❌') + '</p>' +
            '<p>✔️ <b>Verified:</b> ' + (result.data.is_verified ? 'Yes ✅' : 'No ❌') + '</p>' +
            platformDetails +
            '<p class="section-title">Image Analysis</p>' +
            '<p>😊 <b>Face Detection:</b> ' + result.face.verdict + '</p>' +
            '<p>🤖 <b>AI Image Check:</b> ' + result.ai_image.verdict + '</p>' +
            '<p class="experimental">⚠️ AI image detection is experimental and may not always be accurate</p>' +
            '<p class="section-title">Clone Detection</p>' +
            '<p>👥 <b>Clone Check:</b> ' + cloneVerdict + '</p>' +
            cloneSignals +
            '<p class="section-title">Spam Analysis</p>' +
            '<p>🔍 <b>Spam Check:</b> ' + spamVerdict + '</p>' +
            spamMeter +
            spamKeywords +
        '</div>';
}

async function showHistory() {
    const response = await fetch('/history');
    const data = await response.json();
    const stats = data.stats;
    const records = data.history;

    let statsHtml =
        '<div style="background:white;padding:15px;border-radius:8px;border:1px solid #ddd;margin-bottom:15px;">' +
            '<p style="font-weight:bold;font-size:14px;margin-bottom:10px;">📊 Overall Statistics</p>' +
            '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;text-align:center;">' +
                '<div style="background:#f8f9fa;padding:10px;border-radius:5px;">' +
                    '<div style="font-size:22px;font-weight:bold;">' + stats.total + '</div>' +
                    '<div style="font-size:12px;color:#888;">Total Analyzed</div>' +
                '</div>' +
                '<div style="background:#ffcccc;padding:10px;border-radius:5px;">' +
                    '<div style="font-size:22px;font-weight:bold;color:#cc0000;">' + stats.fake_count + '</div>' +
                    '<div style="font-size:12px;color:#888;">Fake Found</div>' +
                '</div>' +
                '<div style="background:#ccffcc;padding:10px;border-radius:5px;">' +
                    '<div style="font-size:22px;font-weight:bold;color:#006600;">' + stats.real_count + '</div>' +
                    '<div style="font-size:12px;color:#888;">Real Accounts</div>' +
                '</div>' +
            '</div>' +
            '<p style="font-size:12px;color:#888;margin-top:10px;">Average Risk Score: ' + stats.avg_risk + '/100 | Clones Found: ' + stats.clones_found + '</p>' +
        '</div>';

    let historyHtml = '<p style="font-weight:bold;font-size:14px;margin-bottom:10px;">🕐 Recent Analyses</p>';
    if (records.length === 0) {
        historyHtml += '<p style="color:#888;">No history yet</p>';
    } else {
        records.forEach(r => {
            const emoji = r.prediction === 'fake' ? '🚨' : '✅';
            const color = r.prediction === 'fake' ? '#ffcccc' : '#ccffcc';
            historyHtml +=
                '<div style="background:' + color + ';padding:8px 12px;border-radius:5px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">' +
                    '<span>' + emoji + ' <b>@' + r.username + '</b> (' + r.platform + ')</span>' +
                    '<span style="font-size:12px;color:#555;">Risk: ' + r.risk_score + '/100 | ' + r.analyzed_at + '</span>' +
                '</div>';
        });
    }

    const panel = document.getElementById('history-panel');
    panel.style.display = 'block';
    panel.innerHTML =
        '<div style="background:white;padding:15px;border-radius:8px;border:1px solid #ddd;">' +
            statsHtml + historyHtml +
        '</div>';
}

async function clearHistory() {
    if (!confirm('Clear all history?')) return;
    await fetch('/clear-history', {method: 'POST'});
    document.getElementById('history-panel').style.display = 'none';
    alert('History cleared!');
}

function toggleCompare() {
    const panel = document.getElementById('compare-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

async function runComparison() {
    const user1 = document.getElementById('compare-user1').value.trim();
    const user2 = document.getElementById('compare-user2').value.trim();
    if (!user1 || !user2) { alert('Please enter both usernames!'); return; }

    document.getElementById('compare-results').innerHTML =
        '<p style="text-align:center;color:#888;">⏳ Analyzing both accounts...</p>';

    const response = await fetch('/compare', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username1: user1, username2: user2, platform: currentPlatform})
    });
    const data = await response.json();

    if (data.error) {
        document.getElementById('compare-results').innerHTML =
            '<div style="background:#fff3cd;padding:10px;border-radius:5px;">⚠️ ' + data.error + '</div>';
        return;
    }

    const a1 = data.account1;
    const a2 = data.account2;

    function accountCard(a) {
        const emoji = a.prediction === 'fake' ? '🚨' : '✅';
        const color = a.prediction === 'fake' ? '#ffcccc' : '#ccffcc';
        const textColor = a.prediction === 'fake' ? '#cc0000' : '#006600';
        const pic = a.data.profile_pic_url ?
            '<img src="/proxy-image?url=' + encodeURIComponent(a.data.profile_pic_url) + '" style="width:60px;height:60px;border-radius:50%;object-fit:cover;border:2px solid #ddd;display:block;margin:0 auto 10px auto;">'
            : '';
        return '<div style="background:' + color + ';padding:12px;border-radius:8px;">' +
            pic +
            '<p style="text-align:center;font-weight:bold;font-size:16px;">' + emoji + ' @' + a.data.username + '</p>' +
            '<p style="text-align:center;color:' + textColor + ';font-size:13px;margin-bottom:10px;">' + a.risk_level + ' (' + a.risk_score + '/100)</p>' +
            '<div style="background:rgba(0,0,0,0.1);border-radius:5px;height:8px;margin-bottom:10px;">' +
                '<div style="width:' + a.risk_score + '%;background:' + a.risk_color + ';height:100%;border-radius:5px;"></div>' +
            '</div>' +
            '<table style="width:100%;font-size:12px;border-collapse:collapse;">' +
                '<tr><td>👥 Followers</td><td style="text-align:right;font-weight:bold;">' + a.data.followers.toLocaleString() + '</td></tr>' +
                '<tr><td>➡️ Following</td><td style="text-align:right;font-weight:bold;">' + a.data.following.toLocaleString() + '</td></tr>' +
                '<tr><td>📝 Bio Length</td><td style="text-align:right;font-weight:bold;">' + a.data.bio_length + ' chars</td></tr>' +
                '<tr><td>🖼️ Profile Pic</td><td style="text-align:right;font-weight:bold;">' + (a.data.has_pic ? 'Yes ✅' : 'No ❌') + '</td></tr>' +
                '<tr><td>✔️ Verified</td><td style="text-align:right;font-weight:bold;">' + (a.data.is_verified ? 'Yes ✅' : 'No ❌') + '</td></tr>' +
                '<tr><td>😊 Face</td><td style="text-align:right;font-weight:bold;">' + (a.face.has_face ? 'Yes ✅' : 'No ❌') + '</td></tr>' +
                '<tr><td>🔍 Spam Score</td><td style="text-align:right;font-weight:bold;">' + a.spam.spam_score + '/100</td></tr>' +
                '<tr><td>👥 Clone Check</td><td style="text-align:right;font-weight:bold;">' + (a.clone.is_clone ? '⚠️ Possible' : '✅ Clean') + '</td></tr>' +
            '</table>' +
        '</div>';
    }

    let verdict = '';
    if (a1.prediction === 'fake' && a2.prediction === 'real') {
        verdict = '⚖️ Verdict: <b>@' + a2.data.username + '</b> appears more legitimate';
    } else if (a2.prediction === 'fake' && a1.prediction === 'real') {
        verdict = '⚖️ Verdict: <b>@' + a1.data.username + '</b> appears more legitimate';
    } else if (a1.risk_score < a2.risk_score) {
        verdict = '⚖️ Verdict: <b>@' + a1.data.username + '</b> has lower risk score';
    } else if (a2.risk_score < a1.risk_score) {
        verdict = '⚖️ Verdict: <b>@' + a2.data.username + '</b> has lower risk score';
    } else {
        verdict = '⚖️ Both accounts have similar risk profiles';
    }

    document.getElementById('compare-results').innerHTML =
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">' +
            accountCard(a1) + accountCard(a2) +
        '</div>' +
        '<div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;font-size:14px;">' +
            verdict +
        '</div>';
}
function toggleMonitoring() {
    const panel = document.getElementById('monitor-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    if (panel.style.display === 'block') loadMonitoringStatus();
}

async function addToMonitoring() {
    const username = document.getElementById('monitor-username').value.trim();
    if (!username) { alert('Please enter a username!'); return; }

    const response = await fetch('/monitoring/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: username, platform: currentPlatform})
    });
    const data = await response.json();
    alert(data.message || data.error);
    document.getElementById('monitor-username').value = '';
    loadMonitoringStatus();
}

async function removeFromMonitoring(username) {
    if (!confirm('Remove @' + username + ' from monitoring?')) return;
    await fetch('/monitoring/remove', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: username})
    });
    loadMonitoringStatus();
}

async function loadMonitoringStatus() {
    const response = await fetch('/monitoring/status');
    const data = await response.json();
    const accounts = data.accounts;
    const alerts = data.alerts;

    let accountsHtml = '<p style="font-weight:bold;font-size:13px;margin-bottom:8px;">📋 Monitored Accounts (' + accounts.length + ')</p>';
    if (accounts.length === 0) {
        accountsHtml += '<p style="color:#888;font-size:13px;">No accounts being monitored yet</p>';
    } else {
        accounts.forEach(a => {
            const scoreColor = a.last_risk_score >= 75 ? '#cc0000' : a.last_risk_score >= 45 ? '#ff9900' : '#006600';
            accountsHtml +=
                '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px;background:#f8f9fa;border-radius:5px;margin-bottom:5px;">' +
                    '<div>' +
                        '<b>@' + a.username + '</b> ' +
                        '<span style="font-size:11px;background:#ddd;padding:2px 6px;border-radius:10px;">' + a.platform + '</span>' +
                        (a.alert_count > 0 ? ' <span style="color:#cc0000;font-size:11px;">⚠️ ' + a.alert_count + ' alerts</span>' : '') +
                    '</div>' +
                    '<div style="display:flex;align-items:center;gap:10px;">' +
                        '<span style="color:' + scoreColor + ';font-size:13px;font-weight:bold;">Risk: ' + (a.last_risk_score || '?') + '/100</span>' +
                        '<span style="font-size:11px;color:#888;">' + (a.last_checked || 'Never') + '</span>' +
                        '<button onclick="removeFromMonitoring(\\'' + a.username + '\\')" style="background:#dc3545;color:white;border:none;padding:4px 8px;border-radius:3px;cursor:pointer;font-size:11px;">Remove</button>' +
                    '</div>' +
                '</div>';
        });
    }

    let alertsHtml = '<p style="font-weight:bold;font-size:13px;margin:15px 0 8px 0;">🚨 Recent Alerts (' + alerts.length + ')</p>';
    if (alerts.length === 0) {
        alertsHtml += '<p style="color:#888;font-size:13px;">No alerts yet — accounts look clean!</p>';
    } else {
        alerts.forEach(a => {
            const alertColor = a.alert_type === 'high_risk' ? '#ffcccc' :
                              a.alert_type === 'clone_detected' ? '#fff3cd' : '#fff3cd';
            alertsHtml +=
                '<div style="background:' + alertColor + ';padding:8px 12px;border-radius:5px;margin-bottom:6px;">' +
                    '<div style="display:flex;justify-content:space-between;">' +
                        '<span>🚨 <b>@' + a.username + '</b>: ' + a.message + '</span>' +
                        '<span style="font-size:11px;color:#555;">' + a.created_at + '</span>' +
                    '</div>' +
                '</div>';
        });
    }

    document.getElementById('monitor-status').innerHTML = accountsHtml + alertsHtml;
}

document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') predict();
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    username = data.get("username", "").strip()
    platform = data.get("platform", "instagram")

    if not username:
        return jsonify({"error": "Please enter a username"})

    if platform == "instagram":
        result, error = analyze_instagram(username)
    else:
        result, error = analyze_x(username)

    if error:
        return jsonify({"error": error})

    # Save to history
    save_analysis(result)

    return jsonify(result)

@app.route("/history")
def history():
    records = get_history(50)
    stats = get_stats()
    return jsonify({"history": records, "stats": stats})

@app.route("/clear-history", methods=["POST"])
def clear_history():
    delete_history()
    return jsonify({"message": "History cleared!"})
@app.route("/bulk-analyze", methods=["POST"])

    

@app.route("/proxy-image")
def proxy_image():
    image_url = request.args.get("url")
    if not image_url:
        return "", 404
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(image_url, headers=headers, timeout=10)
        from flask import Response
        return Response(
            response.content,
            content_type=response.headers.get("content-type", "image/jpeg")
        )
    except:
        return "", 404
@app.route("/compare", methods=["POST"])
def compare():
    data = request.json
    username1 = data.get("username1", "").strip().replace("@", "")
    username2 = data.get("username2", "").strip().replace("@", "")
    platform = data.get("platform", "instagram")

    if not username1 or not username2:
        return jsonify({"error": "Please enter both usernames"})

    if platform == "instagram":
        result1, error1 = analyze_instagram(username1)
        result2, error2 = analyze_instagram(username2)
    else:
        result1, error1 = analyze_x(username1)
        result2, error2 = analyze_x(username2)

    if error1:
        return jsonify({"error": f"Account 1: {error1}"})
    if error2:
        return jsonify({"error": f"Account 2: {error2}"})

    save_analysis(result1)
    save_analysis(result2)

    return jsonify({
        "account1": result1,
        "account2": result2
    })

@app.route("/monitoring/add", methods=["POST"])
def add_monitoring():
    data = request.json
    username = data.get("username", "").strip().replace("@", "")
    platform = data.get("platform", "instagram")
    
    if not username:
        return jsonify({"error": "Please enter a username"})
        
    success = add_monitored_account(username, platform)
    if success:
        return jsonify({"message": f"Successfully added @{username} to monitoring"})
    else:
        return jsonify({"error": f"Failed to add @{username}. Already being monitored?"})

@app.route("/monitoring/remove", methods=["POST"])
def remove_monitoring():
    data = request.json
    username = data.get("username", "").strip().replace("@", "")
    
    if not username:
        return jsonify({"error": "Please enter a username"})
        
    remove_monitored_account(username)
    return jsonify({"message": f"Successfully removed @{username} from monitoring"})

@app.route("/monitoring/status")
def monitoring_status():
    accounts = get_monitored_accounts()
    alerts = get_alerts()
    return jsonify({"accounts": accounts, "alerts": alerts})
if __name__ == "__main__":
    app.run(debug=True, port=5002)