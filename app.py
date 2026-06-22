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
from face_detection import check_face_in_profile_pic
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

model = pickle.load(open("fake_detector_model.pkl", "rb"))

RAPIDAPI_KEY = "ADD RAPIDAPI KEY"
TWITTER_API_KEY = "ADD X API KEY"
SERPAPI_KEY = "ADD API KEY"  # get free key at serpapi.com
INSTAGRAM_HOST = "INSTAGRAM HOST URL"
TWITTER_HOST = "TWITTER HOST URL"

# Load face detector

# Load AI image detector
print("Loading AI detection model...")
ai_detector = pipeline(
    "image-classification",
    model="umm-maybe/AI-image-detector"
)
print("All models loaded!")





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
    headers = {"X-RapidAPI-Key": TWITTER_API_KEY, "X-RapidAPI-Host": TWITTER_HOST}
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
    elif "response" in profile and isinstance(profile["response"], list) and len(profile["response"]) > 0:
        user = profile["response"][0].get("user", {})
    elif "message" in profile:
        return None, f"API Error: {profile['message']}"
    else:
        return None, "Account not found, private, or API limit reached"

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
        if followers >= 1000000: real_score += 200
        elif followers >= 500000: real_score += 150
        elif followers >= 100000: real_score += 100
        elif followers >= 50000: real_score += 80
        elif followers >= 10000: real_score += 60
        elif followers >= 5000: real_score += 40
        elif followers >= 1000: real_score += 30
        elif followers >= 200: real_score += 20
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
        if followers >= 1000000: real_score += 200
        elif followers >= 500000: real_score += 150
        elif followers >= 100000: real_score += 100
        elif followers >= 50000: real_score += 80
        elif followers >= 10000: real_score += 60
        elif followers >= 5000: real_score += 40
        elif followers >= 1000: real_score += 30
        elif followers >= 500: real_score += 20
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

    


@app.route("/")
def home():
    return open("index.html").read()

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    username = data.get("username", "").strip().replace("@", "")
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

    # Relative Follower Adjustment for Comparison
    f1 = result1['data'].get('followers', 0)
    f2 = result2['data'].get('followers', 0)
    
    if f1 > 1000 or f2 > 1000:
        if f1 > f2 * 1.2: # At least 20% more followers
            result1['risk_score'] = max(0, result1['risk_score'] - 10)
            result2['risk_score'] = min(100, result2['risk_score'] + 5)
        elif f2 > f1 * 1.2:
            result2['risk_score'] = max(0, result2['risk_score'] - 10)
            result1['risk_score'] = min(100, result1['risk_score'] + 5)
            
        # Re-evaluate risk labels after adjustment
        for res in [result1, result2]:
            s = res['risk_score']
            if s >= 75:
                res['risk_level'], res['risk_color'] = "🔴 High Risk", "#cc0000"
            elif s >= 45:
                res['risk_level'], res['risk_color'] = "🟡 Medium Risk", "#ff9900"
            else:
                res['risk_level'], res['risk_color'] = "🟢 Low Risk", "#006600"

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
    app.run(debug=True, host='0.0.0.0', port=5004)
