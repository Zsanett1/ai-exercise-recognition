import numpy as np
from .base import BaseExerciseRule, RuleResult


class SquatRule(BaseExerciseRule):
    def __init__(
        self,
        required_consecutive_frames=3,
        view_width_threshold=0.16,
        activation_angle_threshold=125,
        activation_drop_threshold=0.04,
        down_angle_threshold=110,
        up_angle_threshold=160,
        correct_depth_min_angle=70,
        correct_depth_max_angle=105,
        down_drop_threshold=0.05,
        up_drop_threshold=0.02,
        max_missing_frames=5,
    ):
        self.required_consecutive_frames = required_consecutive_frames
        self.view_width_threshold = view_width_threshold
        self.activation_angle_threshold = activation_angle_threshold
        self.activation_drop_threshold = activation_drop_threshold
        self.down_angle_threshold = down_angle_threshold
        self.up_angle_threshold = up_angle_threshold
        self.correct_depth_min_angle = correct_depth_min_angle
        self.correct_depth_max_angle = correct_depth_max_angle
        self.down_drop_threshold = down_drop_threshold
        self.up_drop_threshold = up_drop_threshold
        self.max_missing_frames = max_missing_frames

        self.squat_stage = "up"
        self.squat_down_frames = 0
        self.squat_up_frames = 0
        self.missing_frames = 0
        self.current_view = "side"
        self.standing_hip_y = None
        self.min_knee_angle_during_rep = None

    def validate_activation(self, landmarks):
        metrics = self._get_pose_metrics(landmarks)
        if metrics is None:
            return False

        self.current_view = metrics["view"]

        if self.current_view == "side":
            return metrics["average_knee_angle"] <= self.activation_angle_threshold

        hip_drop = self._get_hip_drop(metrics["hip_center_y"])
        if hip_drop <= self.up_drop_threshold:
            self._update_standing_baseline(metrics["hip_center_y"])
            hip_drop = self._get_hip_drop(metrics["hip_center_y"])
        return hip_drop >= self.activation_drop_threshold

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
        self.current_view = metrics["view"]

        if self.current_view == "side":
            if metrics["average_knee_angle"] <= self.down_angle_threshold:
                self.squat_down_frames += 1
                self.squat_up_frames = 0
                self._update_min_knee_angle(metrics["average_knee_angle"])
            elif metrics["average_knee_angle"] >= self.up_angle_threshold:
                self.squat_up_frames += 1
                self.squat_down_frames = 0
            else:
                self.squat_down_frames = 0
                self.squat_up_frames = 0
        else:
            hip_drop = self._get_hip_drop(metrics["hip_center_y"])

            if self.squat_stage == "up" and hip_drop <= self.up_drop_threshold:
                self._update_standing_baseline(metrics["hip_center_y"])
                hip_drop = self._get_hip_drop(metrics["hip_center_y"])

            if hip_drop >= self.down_drop_threshold:
                self.squat_down_frames += 1
                self.squat_up_frames = 0
                self._update_min_knee_angle(metrics["average_knee_angle"])
            elif hip_drop <= self.up_drop_threshold:
                self.squat_up_frames += 1
                self.squat_down_frames = 0
            else:
                self.squat_down_frames = 0
                self.squat_up_frames = 0

        if self.squat_stage == "up" and self.squat_down_frames >= self.required_consecutive_frames:
            self.squat_stage = "down"

        if self.squat_stage == "down" and self.squat_up_frames >= self.required_consecutive_frames:
            result = self._build_depth_feedback()
            self.reset()
            return result

        return RuleResult()

    def reset(self):
        self.squat_stage = "up"
        self.squat_down_frames = 0
        self.squat_up_frames = 0
        self.missing_frames = 0
        self.current_view = "side"
        self.min_knee_angle_during_rep = None

    def _update_min_knee_angle(self, knee_angle):
        if self.min_knee_angle_during_rep is None:
            self.min_knee_angle_during_rep = knee_angle
        else:
            self.min_knee_angle_during_rep = min(
                self.min_knee_angle_during_rep,
                knee_angle,
        )

    def _build_depth_feedback(self):
        if self.min_knee_angle_during_rep is None:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Squat depth could not be measured clearly.",
                feedback_code="depth_not_measured",
                feedback_level="warning",
            )

        if self.min_knee_angle_during_rep > self.correct_depth_max_angle:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="You did not squat deep enough.",
                feedback_code="not_deep_enough",
                feedback_level="warning",
            )

        if self.min_knee_angle_during_rep < self.correct_depth_min_angle:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="You went too deep during the squat.",
                feedback_code="too_deep",
                feedback_level="warning",
            )

        return RuleResult(
            rep_completed=True,
            keep_active=False,
            is_correct=True,
            feedback="Good squat depth.",
            feedback_code="correct_squat",
            feedback_level="success",
        )

    def _get_pose_metrics(self, landmarks):
        if not landmarks:
            return None

        left_hip = [landmarks[23].x, landmarks[23].y]
        left_knee = [landmarks[25].x, landmarks[25].y]
        left_ankle = [landmarks[27].x, landmarks[27].y]
        right_hip = [landmarks[24].x, landmarks[24].y]
        right_knee = [landmarks[26].x, landmarks[26].y]
        right_ankle = [landmarks[28].x, landmarks[28].y]

        left_knee_angle = self._calculate_angle(left_hip, left_knee, left_ankle)
        right_knee_angle = self._calculate_angle(right_hip, right_knee, right_ankle)
        average_knee_angle = (left_knee_angle + right_knee_angle) / 2

        shoulder_width = abs(landmarks[11].x - landmarks[12].x)
        hip_width = abs(landmarks[23].x - landmarks[24].x)
        average_body_width = (shoulder_width + hip_width) / 2
        hip_center_y = (landmarks[23].y + landmarks[24].y) / 2
        view = "front" if average_body_width >= self.view_width_threshold else "side"

        return {
            "average_knee_angle": average_knee_angle,
            "hip_center_y": hip_center_y,
            "view": view,
        }

    def _update_standing_baseline(self, hip_center_y):
        if self.standing_hip_y is None:
            self.standing_hip_y = hip_center_y
        else:
            self.standing_hip_y = (0.9 * self.standing_hip_y) + (0.1 * hip_center_y)

    def _get_hip_drop(self, hip_center_y):
        if self.standing_hip_y is None:
            return 0.0
        return hip_center_y - self.standing_hip_y

    def _calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = abs(np.degrees(radians))

        if angle > 180:
            angle = 360 - angle

        return angle
