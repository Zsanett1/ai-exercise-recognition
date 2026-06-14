import csv
import json
import os
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf

from rules import build_rule_manager

base_dir = Path(__file__).resolve().parent.parent
model_path = base_dir / "models" / "exercise_model.keras"
labels_path = base_dir / "models" / "class_names.json"
data_path = base_dir / "data" / "dataset.csv"
videos_path = base_dir / "videos"

hidden_classes = {"idle"}
min_confidence_to_display = 0.70
min_confidence_to_consider = 0.40
required_consecutive_frames = 3
required_non_exercise_frames = 3
top_prediction_count = 5


def load_class_names():
    if os.path.exists(labels_path):
        with open(labels_path, "r", encoding="utf-8") as f:
            return json.load(f)

    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return sorted({row["label"] for row in reader if row.get("label")})

    if os.path.exists(videos_path):
        return sorted(
            folder for folder in os.listdir(videos_path)
            if os.path.isdir(os.path.join(videos_path, folder))
        )

    print("Error: no labels source found")
    exit()


class_names = load_class_names()
model = tf.keras.models.load_model(str(model_path))
rule_manager = build_rule_manager(
    class_names=class_names,
    hidden_classes=hidden_classes,
    min_confidence_to_display=min_confidence_to_display,
    required_consecutive_frames=required_consecutive_frames,
    required_non_exercise_frames=required_non_exercise_frames,
    min_confidence_to_consider=min_confidence_to_consider,
)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("hiba, megprobalom 1-el")
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("kritikus hiba")
    exit()

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        candidates = []

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        try:
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                row = []
                for lm in landmarks:
                    row.extend([lm.x, lm.y, lm.z, lm.visibility])

                X = np.array([row])
                prediction = model.predict(X, verbose=0)
                candidate_indexes = np.argsort(prediction[0])[-top_prediction_count:][::-1]
                candidates = [
                    (class_names[int(index)], float(prediction[0][int(index)]))
                    for index in candidate_indexes
                ]
                frame_decision = rule_manager.process_candidates(candidates, landmarks)
            else:
                frame_decision = rule_manager.process_frame(None, 0.0, None)

            if frame_decision.display_label:
                cv2.rectangle(image, (0, 0), (250, 60), (245, 117, 16), -1)
                cv2.putText(
                    image,
                    f"Action: {frame_decision.display_label.upper()}",
                    (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    image,
                    f"Confidence: {frame_decision.display_confidence:.2f}",
                    (15, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

            cv2.rectangle(image, (0, 70), (250, 120), (16, 117, 245), -1)
            cv2.putText(
                image,
                f"Reps: {frame_decision.total_reps}",
                (15, 103),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            if candidates:
                cv2.rectangle(image, (0, 130), (330, 285), (30, 30, 30), -1)
                cv2.putText(
                    image,
                    "Top predictions",
                    (15, 155),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
                for index, (candidate_label, candidate_confidence) in enumerate(candidates, start=1):
                    cv2.putText(
                        image,
                        f"{index}. {candidate_label}: {candidate_confidence:.2f}",
                        (15, 155 + index * 24),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (230, 230, 230),
                        1,
                        cv2.LINE_AA,
                    )

        except Exception as e:
            print(f"Error : {e}")

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.imshow("AI Exercise recignition", image)

        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
