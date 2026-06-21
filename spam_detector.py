import re

# Spam keywords organized by category
SPAM_KEYWORDS = {
    "promotional": [
        "dm for promo", "dm for collab", "promo available",
        "paid promotion", "sponsored", "link in bio",
        "click link", "check bio", "buy now", "shop now",
        "discount code", "use code", "affiliate"
    ],
    "suspicious": [
        "100% legit", "100% real", "guaranteed", "no scam",
        "trust me", "legit seller", "verified seller",
        "fast delivery", "cheap followers", "buy followers",
        "get followers", "increase followers"
    ],
    "crypto_scam": [
        "bitcoin", "crypto", "investment", "profit",
        "trading signal", "forex", "binary", "wallet",
        "eth giveaway", "btc giveaway", "nft drop",
        "double your money", "get rich"
    ],
    "adult_spam": [
        "onlyfans", "18+", "adult content",
        "subscribe for more", "exclusive content"
    ],
    "bot_like": [
        "follow back", "follow for follow", "f4f",
        "l4l", "like for like", "follow everyone",
        "follow all", "gain followers fast"
    ]
}

def detect_spam_keywords(bio, username=""):
    """Scan bio and username for spam keywords"""
    if not bio and not username:
        return {
            "has_spam": False,
            "spam_score": 0,
            "found_keywords": [],
            "categories": [],
            "verdict": "✅ No spam keywords found"
        }

    text = (bio + " " + username).lower()
    found_keywords = []
    found_categories = []
    spam_score = 0

    for category, keywords in SPAM_KEYWORDS.items():
        category_found = []
        for keyword in keywords:
            if keyword.lower() in text:
                category_found.append(keyword)
                found_keywords.append(keyword)

        if category_found:
            found_categories.append(category)
            # Each category adds to spam score
            spam_score += len(category_found) * 15

    # Cap at 100
    spam_score = min(100, spam_score)

    # Check for excessive emojis (bot signal)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(bio or "")
    if len(emojis) > 8:
        spam_score += 15
        found_keywords.append("excessive emojis")
        found_categories.append("bot_like")

    # Check for excessive hashtags
    hashtags = re.findall(r'#\w+', bio or "")
    if len(hashtags) > 5:
        spam_score += 10
        found_keywords.append("excessive hashtags")
        found_categories.append("bot_like")

    # Check for excessive URLs
    urls = re.findall(r'http[s]?://\S+', bio or "")
    if len(urls) > 2:
        spam_score += 15
        found_keywords.append("multiple URLs")

    spam_score = min(100, spam_score)
    has_spam = spam_score > 0

    if spam_score >= 60:
        verdict = "🚨 High spam content detected"
    elif spam_score >= 30:
        verdict = "⚠️ Some spam keywords found"
    elif spam_score > 0:
        verdict = "🔍 Minor spam signals found"
    else:
        verdict = "✅ No spam keywords found"

    return {
        "has_spam": has_spam,
        "spam_score": spam_score,
        "found_keywords": found_keywords[:10],  # limit to 10
        "categories": list(set(found_categories)),
        "verdict": verdict
    }

# Tests
print("=== Spam Detector Tests ===\n")

test_bios = [
    ("nasa", "Making the seemingly impossible, possible ✨"),
    ("crypto_guy99", "DM for crypto signals 💰 Bitcoin investment guaranteed profit! 🚀"),
    ("promo_queen", "DM for promo 📩 Paid promotions available! Use code SAVE20 🛒"),
    ("follow4follow", "F4F ✅ Follow back guaranteed! Follow everyone! Gain followers fast"),
    ("normal_user", "Photography enthusiast 📷 Coffee lover ☕ Based in Mumbai"),
]

for username, bio in test_bios:
    result = detect_spam_keywords(bio, username)
    print(f"@{username}:")
    print(f"  Verdict: {result['verdict']}")
    print(f"  Spam Score: {result['spam_score']}/100")
    if result['found_keywords']:
        print(f"  Found: {result['found_keywords']}")
    print()