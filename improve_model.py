import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report
import pickle

# ── STEP 1: Load CSV dataset ────────────────────────────────
print("Loading dataset...")
df = pd.read_csv("user_fake_authentic_2class.csv")
print(f"Total accounts: {len(df)}")
print("Fake vs Real:")
print(df.iloc[:, -1].value_counts())

# ── STEP 2: Prepare features ────────────────────────────────
X = df.iloc[:, :-1]
y = df.iloc[:, -1]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── STEP 3: Tune the model ──────────────────────────────────
print("\nTuning model... (this takes 2-3 minutes)")

param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [10, 20, None],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
    "class_weight": ["balanced"]
}

rf = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(
    rf, param_grid,
    cv=5,
    scoring="f1_weighted",
    n_jobs=-1,
    verbose=1
)
grid_search.fit(X_train, y_train)

# ── STEP 4: Evaluate ────────────────────────────────────────
best_model = grid_search.best_estimator_
print("\nBest parameters found:")
print(grid_search.best_params_)

predictions = best_model.predict(X_test)
print("\nImproved Model Results:")
print(classification_report(y_test, predictions))

# Compare with original accuracy
original = RandomForestClassifier(n_estimators=100, random_state=42)
original.fit(X_train, y_train)
orig_preds = original.predict(X_test)
print("\nOriginal Model Results:")
print(classification_report(y_test, orig_preds))

# ── STEP 5: Save improved model ─────────────────────────────
pickle.dump(best_model, open("fake_detector_model.pkl", "wb"))
print("\n✅ Improved model saved!")