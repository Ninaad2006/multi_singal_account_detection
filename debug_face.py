import requests
from face_detection import check_face_in_profile_pic

RAPIDAPI_KEY = "dummy" # The app.py has a real one defined in it

# Let's import the rapidapi key from app.py
from app import RAPIDAPI_KEY

url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
querystring = {"username_or_id_or_url": "zuck"}
headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "instagram-scraper-api2.p.rapidapi.com"
}

print("Fetching Zuck's profile info...")
response = requests.get(url, headers=headers, params=querystring)
if response.status_code == 200:
    data = response.json()
    profile_pic_url = data.get("data", {}).get("profile_pic_url_hd") or data.get("data", {}).get("profile_pic_url")
    print(f"Profile pic URL: {profile_pic_url}")
    if profile_pic_url:
        result = check_face_in_profile_pic(profile_pic_url)
        print("Face detection result:", result)
else:
    print("Failed to fetch:", response.status_code)
