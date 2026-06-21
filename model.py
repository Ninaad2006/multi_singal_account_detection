import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle

# Load dataset
df = pd.read_csv("user_fake_authentic_2class.csv")

print("Columns:", df.columns.tolist())
print("Shape:", df.shape)
print("\nFirst 5 rows:")
print(df.head())

# Separate features and label
X = df.iloc[:, :-1]  # everything except last column
y = df.iloc[:, -1]   # last column is fake/real label

# Split into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train the model
print("\nTraining model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Test the model
predictions = model.predict(X_test)
print("\nModel Results:")
print(classification_report(y_test, predictions))

# Save the model
pickle.dump(model, open("fake_detector_model.pkl", "wb"))
print("\nModel saved as fake_detector_model.pkl!")