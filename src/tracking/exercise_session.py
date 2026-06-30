import csv
import json
import os
from pathlib import Path
import numpy as np
import tensorflow as tf
from src.rules import build_rule_manager
from src.tracking.landmark_features import normalize_landmarks

base_dir = Path(__file__).resolve().parent.parent.parent
model_path = base_dir / "models" / "exercise_model.keras"
labels_path = base_dir / "models" / "class_names.json"
data_path = base_dir / "data" / "dataset.csv"
videos_path = base_dir / "videos"

TARGET_LABEL_ALIASES = {
    "calf_raises": "calf_raise",
}

class ExerciseTrackingSession:
    def __init__(self, target_label = None):
        self.requested_target_label = target_label
        self.hidden_classes = {"idle"}
        self.min_confidence_to_display = 0.70
        self.min_confidence_to_consider = 0.40
        self.required_consecutive_frames = 3
        self.required_non_exercise_frames = 3
        self.top_prediction_count = 5
        self.feedback_history = []
        self.last_feedback_rep_count = 0
        self.last_total_reps = 0
        self.last_correct_reps = 0
        self.rep_feedback_history = []
        self.error_screenshots = []

        self.class_names = self.load_class_names()
        self.target_label = self.resolve_target_label(target_label)
        self.model = tf.keras.models.load_model(str(model_path))
        self.rule_manager = build_rule_manager(
            class_names = self.class_names,
            hidden_classes = self.hidden_classes,
            min_confidence_to_display = self.min_confidence_to_display,
            required_consecutive_frames = self.required_consecutive_frames,
            required_non_exercise_frames = self.required_non_exercise_frames,
            min_confidence_to_consider = self.min_confidence_to_consider
        )
        self.latest_label = None
        self.latest_confidence = 0.0
        self.total_reps = 0
        self.correct_reps = 0
        self.feedback = ""

    def load_class_names(self):
        if os.path.exists(labels_path):
            with open(labels_path, "r", encoding = "utf-8") as f:
                return json.load(f)
        if os.path.exists(data_path):
            with open(data_path, "r", encoding = "utf-8", newline = "") as f:
                reader = csv.DictReader(f)
                return sorted({row["label"] for row in reader if row.get("label")})
        if os.path.exists(videos_path):
            return sorted(
                folder for folder in os.listdir(videos_path)
                if os.path.isdir(os.path.join(videos_path, folder))
            )
        raise FileNotFoundError("No labels source found.")

    def resolve_target_label(self, target_label):
        if not target_label:
            return None
        normalized_label = TARGET_LABEL_ALIASES.get(target_label, target_label)
        if normalized_label in self.class_names:
            return normalized_label
        return None

    def build_prediction_candidates(self, prediction):
        candidate_indexes = np.argsort(prediction[0])[-self.top_prediction_count:][::-1]
        top_candidates = [
            (self.class_names[int(index)], float(prediction[0][int(index)]))
            for index in candidate_indexes
        ]

        if self.requested_target_label:
            if not self.target_label:
                return []
            return [
                (label, confidence)
                for label, confidence in top_candidates
                if label == self.target_label
            ]

        return top_candidates
    
    def process_landmarks(self, landmarks):
        if not landmarks:
            frame_decision = self.rule_manager.process_frame(None, 0.0, None)
            self.update_from_decision(frame_decision)
            return frame_decision
        
        row = normalize_landmarks(landmarks)
        
        prediction = self.model.predict(np.array([row]), verbose = 0)
        candidates = self.build_prediction_candidates(prediction)
        frame_decision = self.rule_manager.process_candidates(candidates, landmarks)
        self.update_from_decision(frame_decision)
        return frame_decision
    
    def update_from_decision(self, frame_decision):
        self.latest_label = frame_decision.display_label
        self.latest_confidence = frame_decision.display_confidence
        self.total_reps = frame_decision.total_reps
        self.correct_reps = frame_decision.correct_reps
        if frame_decision.feedback:
            self.feedback = frame_decision.feedback
            if frame_decision.total_reps > self.last_feedback_rep_count:
                self.feedback_history.append(frame_decision.feedback)
                self.last_feedback_rep_count = frame_decision.total_reps
        if frame_decision.total_reps > self.last_total_reps:
            rep_number = frame_decision.total_reps
            is_correct = frame_decision.correct_reps > self.last_correct_reps
            self.rep_feedback_history.append({
                "rep": rep_number,
                "is_correct": is_correct,
                "feedback": frame_decision.feedback or "No feedback recorded.",
            })
            self.last_total_reps = frame_decision.total_reps
            self.last_correct_reps = frame_decision.correct_reps

    def add_error_screenshot(self, rep_number, feedback_code, feedback, image_path):
        self.error_screenshots.append({
            "rep": rep_number, "feedback_code": feedback_code,
            "feedback": feedback, "image_path": image_path,
        })

    def get_summary(self):
        return {
            "label": self.latest_label,
            "confidence": self.latest_confidence,
            "total_reps": self.total_reps,
            "correct_reps": self.correct_reps,
            "feedback": self.feedback,
            "feedback_history": self.feedback_history,
            "rep_feedback_history": self.rep_feedback_history,
            "error_screenshots": self.error_screenshots,
        }
