import numpy as np

from .base import BaseExerciseRule, RuleResult


class PushUpRule(BaseExerciseRule):
    def __init__(
        self,
        required_consecutive_frames=3,
        activation_body_angle_threshold=140,
        activation_elbow_angle_threshold=155,
        activation_lowering_elbow_angle_threshold=130,
        activation_wrist_below_shoulder_offset=0.05,
        activation_wrist_shoulder_x_threshold=0.18,
        down_elbow_angle_threshold=100,
        up_elbow_angle_threshold=160,
        correct_depth_min_angle=55,
        correct_depth_max_angle=110,
        body_straight_angle_threshold=160,
        max_missing_frames=5,
    ):
        self.required_consecutive_frames = required_consecutive_frames
        self.activation_body_angle_threshold = activation_body_angle_threshold
        self.activation_elbow_angle_threshold = activation_elbow_angle_threshold
        self.activation_lowering_elbow_angle_threshold = activation_lowering_elbow_angle_threshold
        self.activation_wrist_below_shoulder_offset = activation_wrist_below_shoulder_offset
        self.activation_wrist_shoulder_x_threshold = activation_wrist_shoulder_x_threshold
        self.down_elbow_angle_threshold = down_elbow_angle_threshold
        self.up_elbow_angle_threshold = up_elbow_angle_threshold
        self.correct_depth_min_angle = correct_depth_min_angle
        self.correct_depth_max_angle = correct_depth_max_angle
        self.body_straight_angle_threshold = body_straight_angle_threshold
        self.max_missing_frames = max_missing_frames

        self.push_up_stage = "up"
        self.push_up_down_frames = 0
        self.push_up_up_frames = 0
        self.missing_frames = 0
        self.min_elbow_angle_during_rep = None
        self.min_body_angle_during_rep = None
        self.capture_lowest_frame = False
        self.capture_body_alignment_frame = False

    def validate_activation(self, landmarks):
        metrics = self._get_pose_metrics(landmarks)
        if metrics is None:
            return False

        wrists_under_shoulders = (
            metrics["average_wrist_y"]
            >= metrics["average_shoulder_y"] + self.activation_wrist_below_shoulder_offset
        )
        hips_below_shoulders = metrics["average_hip_y"] >= metrics["average_shoulder_y"]
        wrists_near_shoulders_x = (
            metrics["average_wrist_shoulder_x_distance"]
            <= self.activation_wrist_shoulder_x_threshold
        )

        elbow_in_push_up_range = (
            metrics["average_elbow_angle"] >= self.activation_elbow_angle_threshold
            or metrics["average_elbow_angle"] <= self.activation_lowering_elbow_angle_threshold
        )

        return (
            metrics["average_body_angle"] >= self.activation_body_angle_threshold
            and elbow_in_push_up_range
            and wrists_under_shoulders
            and hips_below_shoulders
            and wrists_near_shoulders_x
        )

    def is_static_top_position(self, landmarks):
        metrics = self._get_pose_metrics(landmarks)
        if metrics is None:
            return False

        return (
            metrics["average_body_angle"] >= self.activation_body_angle_threshold
            and metrics["average_elbow_angle"] >= self.activation_elbow_angle_threshold
        )

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
        self._update_min_body_angle(metrics["average_body_angle"])
        capture_result = None

        if self.capture_body_alignment_frame and metrics["average_body_angle"] < self.body_straight_angle_threshold:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=False,
                feedback="Keep your body in a straighter line during the push-up.",
                feedback_code="push_up_body_not_straight",
                feedback_level="warning",
                feedback_severity=self.body_straight_angle_threshold - metrics["average_body_angle"],
                capture_feedback_frame=True,
            )

        if metrics["average_elbow_angle"] <= self.down_elbow_angle_threshold:
            self.push_up_down_frames += 1
            self.push_up_up_frames = 0
            self._update_min_elbow_angle(metrics["average_elbow_angle"])
            if self.capture_lowest_frame:
                capture_result = RuleResult(
                    rep_completed=False,
                    keep_active=True,
                    is_correct=True,
                    feedback=None,
                    feedback_code="push_up_not_low_enough",
                    feedback_level=None,
                    feedback_severity=-metrics["average_elbow_angle"],
                    capture_feedback_frame=True,
                )

            if self.min_elbow_angle_during_rep is not None and self.min_elbow_angle_during_rep < self.correct_depth_min_angle:
                capture_result = RuleResult(
                    rep_completed=False,
                    keep_active=True,
                    is_correct=False,
                    feedback="You went too low during the push-up.",
                    feedback_code="push_up_too_low",
                    feedback_level="warning",
                    feedback_severity=self.correct_depth_min_angle - self.min_elbow_angle_during_rep,
                    capture_feedback_frame=self.capture_lowest_frame,
                )
        elif metrics["average_elbow_angle"] >= self.up_elbow_angle_threshold:
            self.push_up_up_frames += 1
            self.push_up_down_frames = 0
        else:
            self.push_up_down_frames = 0
            self.push_up_up_frames = 0

        if self.push_up_stage == "up" and self.push_up_down_frames >= self.required_consecutive_frames:
            self.push_up_stage = "down"

        if self.push_up_stage == "down" and self.push_up_up_frames >= self.required_consecutive_frames:
            result = self._build_push_up_feedback()
            self.reset()
            return result
        
        if capture_result is not None:
            return capture_result

        return RuleResult()

    def reset(self):
        self.push_up_stage = "up"
        self.push_up_down_frames = 0
        self.push_up_up_frames = 0
        self.missing_frames = 0
        self.min_elbow_angle_during_rep = None
        self.min_body_angle_during_rep = None
        self.capture_lowest_frame = False
        self.capture_body_alignment_frame = False

    def _update_min_elbow_angle(self, elbow_angle):
        if self.min_elbow_angle_during_rep is None or elbow_angle < self.min_elbow_angle_during_rep:
            self.min_elbow_angle_during_rep = elbow_angle
            self.capture_lowest_frame = True
        else:
            self.capture_lowest_frame = False

    def _update_min_body_angle(self, body_angle):
        if self.min_body_angle_during_rep is None or body_angle < self.min_body_angle_during_rep:
            self.min_body_angle_during_rep = body_angle
            self.capture_body_alignment_frame = True
        else:
            self.capture_body_alignment_frame = False

    def _build_push_up_feedback(self):
        if self.min_elbow_angle_during_rep is None:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Push-up depth could not be measured clearly.",
                feedback_code="push_up_depth_not_measured",
                feedback_level="warning",
            )

        if (
            self.min_body_angle_during_rep is not None
            and self.min_body_angle_during_rep < self.body_straight_angle_threshold
        ):
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Keep your body in a straighter line during the push-up.",
                feedback_code="push_up_body_not_straight",
                feedback_level="warning",
            )

        if self.min_elbow_angle_during_rep > self.correct_depth_max_angle:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Lower your chest more during the push-up.",
                feedback_code="push_up_not_low_enough",
                feedback_level="warning",
            )

        if self.min_elbow_angle_during_rep < self.correct_depth_min_angle:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="You went too low during the push-up.",
                feedback_code="push_up_too_low",
                feedback_level="warning",
            )

        return RuleResult(
            rep_completed=True,
            keep_active=False,
            is_correct=True,
            feedback="Good push-up.",
            feedback_code="push_up_correct",
            feedback_level="success",
        )

    def _get_pose_metrics(self, landmarks):
        if not landmarks:
            return None

        left_shoulder = [landmarks[11].x, landmarks[11].y]
        left_elbow = [landmarks[13].x, landmarks[13].y]
        left_wrist = [landmarks[15].x, landmarks[15].y]
        left_hip = [landmarks[23].x, landmarks[23].y]
        left_ankle = [landmarks[27].x, landmarks[27].y]

        right_shoulder = [landmarks[12].x, landmarks[12].y]
        right_elbow = [landmarks[14].x, landmarks[14].y]
        right_wrist = [landmarks[16].x, landmarks[16].y]
        right_hip = [landmarks[24].x, landmarks[24].y]
        right_ankle = [landmarks[28].x, landmarks[28].y]

        left_elbow_angle = self._calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = self._calculate_angle(right_shoulder, right_elbow, right_wrist)
        average_elbow_angle = (left_elbow_angle + right_elbow_angle) / 2

        left_body_angle = self._calculate_angle(left_shoulder, left_hip, left_ankle)
        right_body_angle = self._calculate_angle(right_shoulder, right_hip, right_ankle)
        average_body_angle = (left_body_angle + right_body_angle) / 2
        average_shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
        average_wrist_y = (left_wrist[1] + right_wrist[1]) / 2
        average_hip_y = (left_hip[1] + right_hip[1]) / 2
        average_wrist_shoulder_x_distance = (
            abs(left_wrist[0] - left_shoulder[0])
            + abs(right_wrist[0] - right_shoulder[0])
        ) / 2

        return {
            "average_elbow_angle": average_elbow_angle,
            "average_body_angle": average_body_angle,
            "average_shoulder_y": average_shoulder_y,
            "average_wrist_y": average_wrist_y,
            "average_hip_y": average_hip_y,
            "average_wrist_shoulder_x_distance": average_wrist_shoulder_x_distance,
        }

    def _calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = abs(np.degrees(radians))

        if angle > 180:
            angle = 360 - angle

        return angle
