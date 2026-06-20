import requests
import json

INSTAGRAM_HOST = "instagram120.p.rapidapi.com"
RAPIDAPI_KEY = "241acbfa2amsh04e4cb5dec6276bp13e117jsn494bed62103b"

def test_ig(username):
    url = f"https://{INSTAGRAM_HOST}/api/instagram/userInfo"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": INSTAGRAM_HOST,
        "Content-Type": "application/json"
    }
    body = {"username": username}
    response = requests.post(url, headers=headers, json=body)
    data = response.json()
    print(f"\n--- Testing @{username} ---")
    print("Keys:", data.keys() if isinstance(data, dict) else type(data))
    if "message" in data:
        print("Message:", data["message"])
    if "success" in data:
        print("Success:", data["success"])

if __name__ == "__main__":
    test_ig("zuck")
    test_ig("non_existent_account_123456789_")
    test_ig("")
