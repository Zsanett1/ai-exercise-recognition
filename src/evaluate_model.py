import json
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix


base_dir = Path(__file__).resolve().parent.parent
data_path = base_dir / "data" / "dataset.csv"
model_path = base_dir / "models" / "exercise_model.keras"
labels_path = base_dir / "models" / "class_names.json"

print("Model evaluation in process")

if not data_path.exists():
    raise FileNotFoundError(f"Dataset not found: {data_path}")

if not model_path.exists():
    raise FileNotFoundError(f"Model not found: {model_path}")

if not labels_path.exists():
    raise FileNotFoundError(f"Class names not found: {labels_path}")

df = pd.read_csv(data_path)

required_columns = {"label", "split"}
if not required_columns.issubset(df.columns):
    raise ValueError("Dataset must contain label and split columns")

with open(labels_path, "r", encoding="utf-8") as f:
    class_names = json.load(f)

label_to_id = {label: index for index, label in enumerate(class_names)}
unknown_labels = sorted(set(df["label"]) - set(label_to_id))
if unknown_labels:
    raise ValueError(f"Dataset contains labels not present in class_names.json: {unknown_labels}")

feature_columns = [
    col
    for col in df.columns
    if col not in {"label", "split", "source_file", "source_mtime"}
]

test_df = df[df["split"] == "test"].copy()
if test_df.empty:
    raise ValueError("Test split is empty")

X_test = test_df[feature_columns].values
y_test = test_df["label"].map(label_to_id).values

print(f"Classes: {class_names}")
print(f"Test samples: {len(X_test)}")
print(f"Input dimensions: {X_test.shape[1]}")

model = tf.keras.models.load_model(model_path)

test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"\nTest loss: {test_loss:.4f}")
print(f"Test accuracy: {test_accuracy:.4f}")

y_pred_probs = model.predict(X_test, verbose=0)
y_pred = np.argmax(y_pred_probs, axis=1)

print("\nClassification report:")
print(classification_report(y_test, y_pred, target_names=class_names))

print("\nConfusion matrix:")
print(confusion_matrix(y_test, y_pred))
