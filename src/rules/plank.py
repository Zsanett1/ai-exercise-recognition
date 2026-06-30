import numpy as np
import time

from .base import BaseExerciseRule, RuleResult


class PlankRule(BaseExerciseRule):
    def __init__(
        self,
        activation_body_angle_threshold=130,
        body_straight_angle_threshold=160,
        hip_offset_threshold=0.06,
        hold_duration_seconds=10,
        max_missing_frames=5,
    ):
        self.activation_body_angle_threshold = activation_body_angle_threshold
        self.body_straight_angle_threshold = body_straight_angle_threshold
        self.hip_offset_threshold = hip_offset_threshold
        self.hold_duration_seconds = hold_duration_seconds
        self.max_missing_frames = max_missing_frames

        self.missing_frames = 0
        self.correct_hold_started_at = None

    def validate_activation(self, landmarks):
        metrics = self._get_pose_metrics(landmarks)
        if metrics is None:
            return False

        return metrics["average_body_angle"] >= self.activation_body_angle_threshold

    def on_activate(self):
        self.missing_frames = 0

    def process_active_frame(self, landmarks):
        metrics = self._get_pose_metrics(landmarks)

        if metrics is None:
            self.missing_frames += 1
            return RuleResult(
                rep_completed=False,
                keep_active=self.missing_frames < self.max_missing_frames,
            )

        self.missing_frames = 0
        return self._build_plank_feedback(metrics)

    def reset(self):
        self.missing_frames = 0
        self.correct_hold_started_at = None

    def _build_plank_feedback(self, metrics):
        if metrics["average_body_angle"] < self.body_straight_angle_threshold:
            self.correct_hold_started_at = None
            return RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=False,
                feedback="Keep your body in a straighter line during the plank.",
                feedback_code="plank_body_not_straight",
                feedback_level="warning",
                feedback_severity=self.body_straight_angle_threshold - metrics["average_body_angle"],
                capture_feedback_frame=True,
            )

        if metrics["average_hip_line_offset"] > self.hip_offset_threshold:
            self.correct_hold_started_at = None
            return RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=False,
                feedback="Lift your hips slightly to avoid sagging.",
                feedback_code="plank_hips_sagging",
                feedback_level="warning",
                feedback_severity=metrics["average_hip_line_offset"] - self.hip_offset_threshold,
                capture_feedback_frame=True,
            )

        if metrics["average_hip_line_offset"] < -self.hip_offset_threshold:
            self.correct_hold_started_at = None
            return RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=False,
                feedback="Lower your hips slightly to keep a straight plank.",
                feedback_code="plank_hips_too_high",
                feedback_level="warning",
                feedback_severity=abs(metrics["average_hip_line_offset"]) - self.hip_offset_threshold,
                capture_feedback_frame=True,
            )

        if self.correct_hold_started_at is None:
            self.correct_hold_started_at = time.monotonic()

        hold_completed = (
            time.monotonic() - self.correct_hold_started_at
            >= self.hold_duration_seconds
        )

        return RuleResult(
            rep_completed=False,
            hold_completed=hold_completed,
            keep_active=True,
            is_correct=True,
            feedback="Good plank position.",
            feedback_code="plank_correct",
            feedback_level="success",
        )

    def _get_pose_metrics(self, landmarks):
        if not landmarks:
            return None

        left_shoulder = [landmarks[11].x, landmarks[11].y]
        left_hip = [landmarks[23].x, landmarks[23].y]
        left_ankle = [landmarks[27].x, landmarks[27].y]

        right_shoulder = [landmarks[12].x, landmarks[12].y]
        right_hip = [landmarks[24].x, landmarks[24].y]
        right_ankle = [landmarks[28].x, landmarks[28].y]

        left_body_angle = self._calculate_angle(left_shoulder, left_hip, left_ankle)
        right_body_angle = self._calculate_angle(right_shoulder, right_hip, right_ankle)
        average_body_angle = (left_body_angle + right_body_angle) / 2

        left_hip_line_offset = self._calculate_hip_line_offset(
            left_shoulder,
            left_hip,
            left_ankle,
        )
        right_hip_line_offset = self._calculate_hip_line_offset(
            right_shoulder,
            right_hip,
            right_ankle,
        )
        average_hip_line_offset = (left_hip_line_offset + right_hip_line_offset) / 2

        return {
            "average_body_angle": average_body_angle,
            "average_hip_line_offset": average_hip_line_offset,
        }

    def _calculate_hip_line_offset(self, shoulder, hip, ankle):
        shoulder = np.array(shoulder)
        hip = np.array(hip)
        ankle = np.array(ankle)

        shoulder_to_ankle = ankle - shoulder
        shoulder_to_hip = hip - shoulder
        line_length_squared = np.dot(shoulder_to_ankle, shoulder_to_ankle)

        if line_length_squared == 0:
            return 0.0

        projection_ratio = np.dot(shoulder_to_hip, shoulder_to_ankle) / line_length_squared
        projected_hip = shoulder + projection_ratio * shoulder_to_ankle
        return hip[1] - projected_hip[1]

    def _calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = abs(np.degrees(radians))

        if angle > 180:
            angle = 360 - angle

        return angle
