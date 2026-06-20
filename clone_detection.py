from rapidfuzz import fuzz
import re
import requests

# ── FUNCTION 1: Username pattern check ─────────────────────
def check_username_clone(username):
    clean = username.lower()
    clone_patterns = [
        r'.*_+official.*',
        r'.*\.+official.*',
        r'real_+.*',
        r'.*_+real.*',
        r'.*_+backup.*',
        r'.*_+support.*',
        r'.*_+help.*',
        r'.*_+account.*',
        r'.*_+page.*',
        r'.*0+$',
        r'.*_+[0-9]+$',
    ]
    signals = []
    for pattern in clone_patterns:
        if re.match(pattern, clean):
            signals.append(f"Username matches clone pattern")
    return signals

# ── FUNCTION 2: Username similarity ────────────────────────
def compare_usernames(username1, username2):
    return fuzz.ratio(username1.lower(), username2.lower())

# ── FUNCTION 3: Bio similarity ──────────────────────────────
def check_bio_clone(bio1, bio2):
    if not bio1 or not bio2:
        return 0
    return fuzz.ratio(bio1.lower(), bio2.lower())

# ── FUNCTION 4: Reverse image search ───────────────────────
def reverse_image_search(image_url, api_key):
    try:
        search_url = "https://serpapi.com/search"
        params = {
            "engine": "google_reverse_image",
            "image_url": image_url,
            "api_key": api_key
        }
        response = requests.get(search_url, params=params)
        data = response.json()
        results = []
        if "inline_images" in data:
            for img in data["inline_images"][:5]:
                results.append(img.get("source", ""))
        if "image_results" in data:
            for result in data["image_results"][:3]:
                results.append(result.get("link", ""))
        return {
            "found_elsewhere": len(results) > 0,
            "locations": results,
            "count": len(results)
        }
    except Exception as e:
        return {"found_elsewhere": None, "locations": [], "count": 0}

# ── FUNCTION 5: Full clone check ────────────────────────────
def full_clone_check(username, bio, profile_pic_url,
                     original_username=None, original_bio=None,
                     serpapi_key=None):
    clone_signals = []
    clone_score = 0

    # Check 1: Username patterns
    pattern_signals = check_username_clone(username)
    if pattern_signals:
        clone_signals.extend(pattern_signals)
        clone_score += 30

    # Check 2: Username similarity
    if original_username:
        similarity = compare_usernames(username, original_username)
        if similarity > 85:
            clone_signals.append(
                f"Username {similarity:.0f}% similar to @{original_username}"
            )
            clone_score += 40
        elif similarity > 70:
            clone_signals.append(
                f"Username somewhat similar to @{original_username}"
            )
            clone_score += 20

    # Check 3: Bio similarity
    if original_bio and bio:
        bio_similarity = check_bio_clone(bio, original_bio)
        if bio_similarity > 80:
            clone_signals.append(
                f"Bio {bio_similarity:.0f}% identical to original"
            )
            clone_score += 40
        elif bio_similarity > 60:
            clone_signals.append(
                f"Bio suspiciously similar to original"
            )
            clone_score += 20

    # Check 4: Reverse image search
    if profile_pic_url and serpapi_key:
        image_results = reverse_image_search(profile_pic_url, serpapi_key)
        if image_results["found_elsewhere"] and image_results["count"] > 2:
            clone_signals.append(
                f"Profile picture found on {image_results['count']} other sites"
            )
            clone_score += 30

    # Final verdict
    if clone_score >= 60:
        verdict = "🚨 Likely Clone Profile"
        is_clone = True
    elif clone_score >= 30:
        verdict = "⚠️ Possibly Clone Profile"
        is_clone = True
    else:
        verdict = "✅ No Clone Signals Detected"
        is_clone = False

    return {
        "is_clone": is_clone,
        "verdict": verdict,
        "clone_score": clone_score,
        "signals": clone_signals
    }

# ── TESTS ───────────────────────────────────────────────────
print("=== Username Clone Pattern Tests ===")
test_usernames = [
    "nasa_official", "real_nasa", "nasa.official",
    "nasa_backup", "nasa_123", "nasa",
    "elonmusk0", "cristiano_real"
]
for username in test_usernames:
    signals = check_username_clone(username)
    if signals:
        print(f"⚠️  {username}: Clone pattern detected")
    else:
        print(f"✅ {username}: Clean")

print("\n=== Full Clone Detection Test ===")
result = full_clone_check(
    username="nasa_official",
    bio="Making the seemingly impossible possible ✨",
    profile_pic_url="",
    original_username="nasa",
    original_bio="Making the seemingly impossible, possible. ✨"
)
print(f"Verdict: {result['verdict']}")
print(f"Score: {result['clone_score']}")
print(f"Signals: {result['signals']}")

print("\n=== Clean Account Test ===")
result2 = full_clone_check(
    username="john_photography",
    bio="I love taking photos of nature",
    profile_pic_url=""
)
print(f"Verdict: {result2['verdict']}")
print(f"Score: {result2['clone_score']}")