import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report
import os
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
data_path = base_dir / "data" / "dataset.csv"
model_dir = base_dir / "models"
model_name = "exercise_model.keras"
labels_file = "class_names.json"

print("Model training in process")

if not os.path.exists(data_path):
    print(f"Error, no data found")
    exit()

df = pd.read_csv(data_path)

required_columns = {"label", "split"}
if not required_columns.issubset(df.columns):
    print("Error, dataset must contain label and split columns")
    exit()

feature_columns = [col for col in df.columns if col not in {"label", "split", "source_file", "source_mtime", "feature_version"}]
y = df['label'].values

encoder = LabelEncoder()
df["label_encoded"] = encoder.fit_transform(y)

label_map = dict(zip(range(len(encoder.classes_)), encoder.classes_))
print(f"Recognized categories: {label_map}")

train_df = df[df["split"] == "train"]
val_df = df[df["split"] == "validation"]
test_df = df[df["split"] == "test"]

if train_df.empty or val_df.empty or test_df.empty:
    print("Error, train, validation and test splits must all contain data")
    exit()

X_train = train_df[feature_columns].values
y_train = train_df["label_encoded"].values
X_val = val_df[feature_columns].values
y_val = val_df["label_encoded"].values
X_test = test_df[feature_columns].values
y_test = test_df["label_encoded"].values

print(f"Train samples: {len(X_train)}")
print(f"Validation samples: {len(X_val)}")
print(f"Test samples: {len(X_test)}")

model = models.Sequential([
    layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    layers.Dropout(0.2),
    layers.Dense(32, activation='relu'),
    layers.Dense(len(encoder.classes_), activation='softmax')
])

model.compile(optimizer = 'adam',
              loss = 'sparse_categorical_crossentropy',
              metrics = ['accuracy'])

print("\nLearning begins")

model.fit(X_train,y_train, epochs = 50, batch_size = 32, validation_data = (X_val, y_val))

test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"\nTest accuracy: {test_accuracy:.4f}")

y_pred_probs = model.predict(X_test)
y_pred = np.argmax(y_pred_probs, axis = 1)

print("\nClassification report:")
print(classification_report(y_test, y_pred, target_names=encoder.classes_))

print("\nConfusion matrix:")
print(confusion_matrix(y_test, y_pred))

if not os.path.exists(model_dir):
    os.makedirs(model_dir)

model.save(str(model_dir / model_name))
with open(model_dir / labels_file, "w", encoding="utf-8") as f:
    json.dump(encoder.classes_.tolist(), f, ensure_ascii=True, indent=2)
print("\nSuccess, model saved")
