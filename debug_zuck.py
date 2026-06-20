from app import get_instagram_data
from face_detection import check_face_in_profile_pic

data = get_instagram_data("zuck")
print("Data keys:", data.keys())
if "result" in data and len(data["result"]) > 0:
    user = data["result"][0].get("user", {})
    pic_url = user.get("profile_pic_url", "")
    print("Pic URL:", pic_url)
    if pic_url:
        print(check_face_in_profile_pic(pic_url))
else:
    print("No user data")
