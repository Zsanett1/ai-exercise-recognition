import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
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

feature_columns = [col for col in df.columns if col not in {"label", "source_file", "source_mtime"}]
X = df[feature_columns].values
y = df['label'].values

encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)

label_map = dict(zip(range(len(encoder.classes_)), encoder.classes_))
print(f"Recognized categories: {label_map}")

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

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

model.fit(X_train,y_train, epochs = 50, batch_size = 32, validation_data = (X_test, y_test))

if not os.path.exists(model_dir):
    os.makedirs(model_dir)

model.save(str(model_dir / model_name))
with open(model_dir / labels_file, "w", encoding="utf-8") as f:
    json.dump(encoder.classes_.tolist(), f, ensure_ascii=True, indent=2)
print("\nSuccess, model saved")
