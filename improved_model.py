import pandas as pd
import json
import os
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report
import pickle

# ── STEP 1: Load existing CSV dataset ──────────────────────
print("Loading CSV dataset...")
df = pd.read_csv("user_fake_authentic_2class.csv")
print(f"CSV dataset: {len(df)} accounts")

# ── STEP 2: Load your 600+ JSON fake accounts ──────────────
print("\nLoading JSON fake accounts...")

json_accounts = []
json_folder = "json_accounts"  # folder where your JSON files are

for filename in os.listdir(json_folder):
    if filename.endswith(".json"):
        try:
            with open(os.path.join(json_folder, filename), "r") as f:
                data = json.load(f)

            # Handle nested structure
            if "graphql" in data:
                user = data["graphql"]["user"]
            else:
                user = data

            username = user.get("username", "")
            followers = user.get("edge_followed_by", {}).get("count", 0)
            following = user.get("edge_follow", {}).get("count", 0)
            posts = user.get("edge_owner_to_timeline_media", {}).get("count", 0)
            bio = user.get("biography", "") or ""
            has_pic = 1 if user.get("profile_pic_url") else 0
            is_private = 1 if user.get("is_private") else 0
            bio_length = len(bio)
            ff_ratio = followers / max(following, 1)
            num_ratio = len(re.findall(r'\d', username)) / max(len(username), 1)

            json_accounts.append({
                "pos": posts,
                "flw": followers,
                "flg": following,
                "bl": bio_length,
                "pic": has_pic,
                "lin": 0,
                "cl": 0,
                "cz": 0,
                "ni": num_ratio,
                "erl": 0,
                "erc": 0,
                "lt": 0,
                "hc": 0,
                "pr": is_private,
                "fo": ff_ratio,
                "cs": 0,
                "pi": 0,
                "class": "f"  # all JSON accounts are fake
            })
        except Exception as e:
            print(f"Skipping {filename}: {e}")

print(f"Loaded {len(json_accounts)} JSON fake accounts")

# ── STEP 3: Combine datasets ────────────────────────────────
json_df = pd.DataFrame(json_accounts)
combined_df = pd.concat([df, json_df], ignore_index=True)
print(f"\nCombined dataset: {len(combined_df)} accounts")
print("Fake vs Real:")
print(combined_df["class"].value_counts())

# ── STEP 4: Prepare features ────────────────────────────────
X = combined_df.iloc[:, :-1]
y = combined_df.iloc[:, -1]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── STEP 5: Tune the model with GridSearchCV ────────────────
print("\nTuning model... (this may take 2-3 minutes)")

param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [10, 20, None],
    "min_samples_split": [2, 5, 10],
    "class_weight": ["balanced"]
}

rf = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(
    rf, param_grid,
    cv=3,
    scoring="f1_weighted",
    n_jobs=-1,
    verbose=1
)
grid_search.fit(X_train, y_train)

# ── STEP 6: Evaluate best model ─────────────────────────────
best_model = grid_search.best_estimator_
print("\nBest parameters:", grid_search.best_params_)

predictions = best_model.predict(X_test)
print("\nImproved Model Results:")
print(classification_report(y_test, predictions))

# ── STEP 7: Save improved model ─────────────────────────────
pickle.dump(best_model, open("fake_detector_model.pkl", "wb"))
print("\n✅ Improved model saved as fake_detector_model.pkl!")