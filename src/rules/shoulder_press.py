import numpy as np

from .base import BaseExerciseRule, RuleResult


class ShoulderPressRule(BaseExerciseRule):
    def __init__(
        self,
        required_consecutive_frames=3,
        pressed_elbow_angle_threshold=150,
        lowered_elbow_angle_threshold=110,
        overhead_wrist_offset_threshold=0.05,
        shoulder_level_wrist_offset_threshold=0.15,
        correct_press_min_angle=145,
        correct_lower_max_angle=115,
        arm_asymmetry_threshold=0.12,
        max_missing_frames=5,
    ):
        self.required_consecutive_frames = required_consecutive_frames
        self.pressed_elbow_angle_threshold = pressed_elbow_angle_threshold
        self.lowered_elbow_angle_threshold = lowered_elbow_angle_threshold
        self.overhead_wrist_offset_threshold = overhead_wrist_offset_threshold
        self.shoulder_level_wrist_offset_threshold = shoulder_level_wrist_offset_threshold
        self.correct_press_min_angle = correct_press_min_angle
        self.correct_lower_max_angle = correct_lower_max_angle
        self.arm_asymmetry_threshold = arm_asymmetry_threshold
        self.max_missing_frames = max_missing_frames

        self.press_stage = "down"
        self.pressed_frames = 0
        self.lowered_frames = 0
        self.missing_frames = 0
        self.max_elbow_angle_during_rep = None
        self.min_elbow_angle_during_rep = None
        self.max_wrist_asymmetry_during_rep = 0.0
        self.capture_highest_press_frame = False
        self.capture_lowest_press_frame = False
        self.capture_arm_asymmetry_frame = False

    def validate_activation(self, landmarks):
        metrics = self._get_pose_metrics(landmarks)
        if metrics is None:
            return False

        return (
            metrics["average_wrist_y"] <= metrics["average_shoulder_y"] + self.shoulder_level_wrist_offset_threshold
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
        self._update_rep_metrics(metrics)
        capture_result = None

        if self.capture_highest_press_frame:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=True,
                feedback=None,
                feedback_code="shoulder_press_not_pressed_high_enough",
                feedback_level=None,
                feedback_severity=self.max_elbow_angle_during_rep,
                capture_feedback_frame=True,
            )

        if self.capture_lowest_press_frame:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=True,
                feedback=None,
                feedback_code="shoulder_press_not_lowered_enough",
                feedback_level=None,
                feedback_severity=-self.min_elbow_angle_during_rep,
                capture_feedback_frame=True,
            )

        if self.capture_arm_asymmetry_frame and self.max_wrist_asymmetry_during_rep > self.arm_asymmetry_threshold:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=False,
                feedback="Press both arms more evenly during the shoulder press.",
                feedback_code="shoulder_press_arms_not_even",
                feedback_level="warning",
                feedback_severity=self.max_wrist_asymmetry_during_rep,
                capture_feedback_frame=True,
            )

        wrists_overhead = (
            metrics["average_wrist_y"]
            <= metrics["average_shoulder_y"] - self.overhead_wrist_offset_threshold
        )
        wrists_lowered = (
            metrics["average_wrist_y"]
            >= metrics["average_shoulder_y"] - self.shoulder_level_wrist_offset_threshold
        )

        if (
            metrics["average_elbow_angle"] >= self.pressed_elbow_angle_threshold
            and wrists_overhead
        ):
            self.pressed_frames += 1
            self.lowered_frames = 0
        elif (
            metrics["average_elbow_angle"] <= self.lowered_elbow_angle_threshold
            and wrists_lowered
        ):
            self.lowered_frames += 1
            self.pressed_frames = 0
        else:
            self.pressed_frames = 0
            self.lowered_frames = 0

        if self.press_stage == "down" and self.pressed_frames >= self.required_consecutive_frames:
            self.press_stage = "up"

        if self.press_stage == "up" and self.lowered_frames >= self.required_consecutive_frames:
            result = self._build_press_feedback()
            self.reset()
            return result
        
        if capture_result is not None:
            return capture_result

        return RuleResult()

    def reset(self):
        self.press_stage = "down"
        self.pressed_frames = 0
        self.lowered_frames = 0
        self.missing_frames = 0
        self.max_elbow_angle_during_rep = None
        self.min_elbow_angle_during_rep = None
        self.max_wrist_asymmetry_during_rep = 0.0
        self.capture_highest_press_frame = False
        self.capture_lowest_press_frame = False
        self.capture_arm_asymmetry_frame = False

    def _update_rep_metrics(self, metrics):
        elbow_angle = metrics["average_elbow_angle"]
        self.capture_highest_press_frame = False
        self.capture_lowest_press_frame = False
        self.capture_arm_asymmetry_frame = False

        if self.max_elbow_angle_during_rep is None or elbow_angle > self.max_elbow_angle_during_rep:
            self.max_elbow_angle_during_rep = elbow_angle
            self.capture_highest_press_frame = True
            
        if self.min_elbow_angle_during_rep is None or elbow_angle < self.min_elbow_angle_during_rep:
            self.min_elbow_angle_during_rep = elbow_angle
            self.capture_lowest_press_frame = True

        if metrics["wrist_height_asymmetry"] > self.max_wrist_asymmetry_during_rep:
            self.max_wrist_asymmetry_during_rep = metrics["wrist_height_asymmetry"]
            self.capture_arm_asymmetry_frame = True

    def _build_press_feedback(self):
        if self.max_elbow_angle_during_rep is None or self.min_elbow_angle_during_rep is None:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Shoulder press range of motion could not be measured clearly.",
                feedback_code="shoulder_press_range_not_measured",
                feedback_level="warning",
            )

        if self.max_wrist_asymmetry_during_rep > self.arm_asymmetry_threshold:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Press both arms more evenly during the shoulder press.",
                feedback_code="shoulder_press_arms_not_even",
                feedback_level="warning",
            )

        if self.max_elbow_angle_during_rep < self.correct_press_min_angle:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Press the weights higher overhead.",
                feedback_code="shoulder_press_not_pressed_high_enough",
                feedback_level="warning",
            )

        if self.min_elbow_angle_during_rep > self.correct_lower_max_angle:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Lower the weights closer to shoulder level before the next press.",
                feedback_code="shoulder_press_not_lowered_enough",
                feedback_level="warning",
            )

        return RuleResult(
            rep_completed=True,
            keep_active=False,
            is_correct=True,
            feedback="Good shoulder press.",
            feedback_code="shoulder_press_correct",
            feedback_level="success",
        )

    def _get_pose_metrics(self, landmarks):
        if not landmarks:
            return None

        left_shoulder = [landmarks[11].x, landmarks[11].y]
        left_elbow = [landmarks[13].x, landmarks[13].y]
        left_wrist = [landmarks[15].x, landmarks[15].y]

        right_shoulder = [landmarks[12].x, landmarks[12].y]
        right_elbow = [landmarks[14].x, landmarks[14].y]
        right_wrist = [landmarks[16].x, landmarks[16].y]

        left_elbow_angle = self._calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = self._calculate_angle(right_shoulder, right_elbow, right_wrist)
        average_elbow_angle = (left_elbow_angle + right_elbow_angle) / 2

        average_shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
        average_wrist_y = (left_wrist[1] + right_wrist[1]) / 2
        wrist_height_asymmetry = abs(left_wrist[1] - right_wrist[1])

        return {
            "average_elbow_angle": average_elbow_angle,
            "average_shoulder_y": average_shoulder_y,
            "average_wrist_y": average_wrist_y,
            "wrist_height_asymmetry": wrist_height_asymmetry,
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
