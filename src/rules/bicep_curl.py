import numpy as np

from .base import BaseExerciseRule, RuleResult


class BicepCurlRule(BaseExerciseRule):
    def __init__(
        self,
        required_consecutive_frames=3,
        curled_angle_threshold=65,
        extended_angle_threshold=150,
        correct_curl_max_angle=75,
        correct_extension_min_angle=145,
        elbow_drift_threshold=0.08,
        max_missing_frames=5,
    ):
        self.required_consecutive_frames = required_consecutive_frames
        self.curled_angle_threshold = curled_angle_threshold
        self.extended_angle_threshold = extended_angle_threshold
        self.correct_curl_max_angle = correct_curl_max_angle
        self.correct_extension_min_angle = correct_extension_min_angle
        self.elbow_drift_threshold = elbow_drift_threshold
        self.max_missing_frames = max_missing_frames

        self.curl_stage = "down"
        self.curled_frames = 0
        self.extended_frames = 0
        self.missing_frames = 0
        self.min_elbow_angle_during_rep = None
        self.max_elbow_angle_during_rep = None
        self.max_elbow_drift_during_rep = 0.0
        self.start_elbow_center = None
        self.capture_highest_curl_frame = False
        self.capture_lowest_curl_frame = False
        self.capture_elbow_drift_frame = False

    def validate_activation(self, landmarks):
        metrics = self._get_pose_metrics(landmarks)
        return metrics is not None

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

        if self.capture_highest_curl_frame:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=True,
                feedback=None,
                feedback_code="bicep_curl_not_curled_high_enough",
                feedback_level=None,
                feedback_severity=-self.min_elbow_angle_during_rep,
                capture_feedback_frame=True,
            )

        if self.capture_lowest_curl_frame:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=True,
                feedback=None,
                feedback_code="bicep_curl_not_lowered_enough",
                feedback_level=None,
                feedback_severity=self.max_elbow_angle_during_rep,
                capture_feedback_frame=True,
            )

        if self.capture_elbow_drift_frame and self.max_elbow_drift_during_rep > self.elbow_drift_threshold:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=False,
                feedback="Keep your elbows more stable during the curl.",
                feedback_code="bicep_curl_elbows_moving",
                feedback_level="warning",
                feedback_severity=self.max_elbow_drift_during_rep,
                capture_feedback_frame=True,
            )

        if metrics["average_elbow_angle"] <= self.curled_angle_threshold:
            self.curled_frames += 1
            self.extended_frames = 0
        elif metrics["average_elbow_angle"] >= self.extended_angle_threshold:
            self.extended_frames += 1
            self.curled_frames = 0
        else:
            self.curled_frames = 0
            self.extended_frames = 0

        if self.curl_stage == "down" and self.curled_frames >= self.required_consecutive_frames:
            self.curl_stage = "up"

        if self.curl_stage == "up" and self.extended_frames >= self.required_consecutive_frames:
            result = self._build_curl_feedback()
            self.reset()
            return result
        
        if capture_result is not None:
            return capture_result

        return RuleResult()

    def reset(self):
        self.curl_stage = "down"
        self.curled_frames = 0
        self.extended_frames = 0
        self.missing_frames = 0
        self.min_elbow_angle_during_rep = None
        self.max_elbow_angle_during_rep = None
        self.max_elbow_drift_during_rep = 0.0
        self.start_elbow_center = None
        self.capture_highest_curl_frame = False
        self.capture_lowest_curl_frame = False
        self.capture_elbow_drift_frame = False

    def _update_rep_metrics(self, metrics):
        elbow_angle = metrics["average_elbow_angle"]
        self.capture_highest_curl_frame = False
        self.capture_lowest_curl_frame = False
        self.capture_elbow_drift_frame = False

        if self.min_elbow_angle_during_rep is None or elbow_angle < self.min_elbow_angle_during_rep:
            self.min_elbow_angle_during_rep = elbow_angle
            self.capture_highest_curl_frame = True

        if self.max_elbow_angle_during_rep is None or elbow_angle > self.max_elbow_angle_during_rep:
            self.max_elbow_angle_during_rep = elbow_angle
            self.capture_lowest_curl_frame = True

        elbow_center = metrics["elbow_center"]
        if self.start_elbow_center is None:
            self.start_elbow_center = elbow_center
            return

        elbow_drift = self._calculate_distance(self.start_elbow_center, elbow_center)
        if elbow_drift > self.max_elbow_drift_during_rep:
            self.max_elbow_drift_during_rep = elbow_drift
            self.capture_elbow_drift_frame = True

    def _build_curl_feedback(self):
        if self.min_elbow_angle_during_rep is None or self.max_elbow_angle_during_rep is None:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Bicep curl range of motion could not be measured clearly.",
                feedback_code="bicep_curl_range_not_measured",
                feedback_level="warning",
            )

        if self.max_elbow_drift_during_rep > self.elbow_drift_threshold:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Keep your elbows more stable during the curl.",
                feedback_code="bicep_curl_elbows_moving",
                feedback_level="warning",
            )

        if self.min_elbow_angle_during_rep > self.correct_curl_max_angle:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Curl the weight higher to complete the movement.",
                feedback_code="bicep_curl_not_curled_high_enough",
                feedback_level="warning",
            )

        if self.max_elbow_angle_during_rep < self.correct_extension_min_angle:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Lower your arm more before starting the next curl.",
                feedback_code="bicep_curl_not_lowered_enough",
                feedback_level="warning",
            )

        return RuleResult(
            rep_completed=True,
            keep_active=False,
            is_correct=True,
            feedback="Good bicep curl.",
            feedback_code="bicep_curl_correct",
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
        elbow_center = [
            (left_elbow[0] + right_elbow[0]) / 2,
            (left_elbow[1] + right_elbow[1]) / 2,
        ]

        return {
            "average_elbow_angle": average_elbow_angle,
            "elbow_center": elbow_center,
        }

    def _calculate_distance(self, a, b):
        a = np.array(a)
        b = np.array(b)
        return float(np.linalg.norm(a - b))

    def _calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = abs(np.degrees(radians))

        if angle > 180:
            angle = 360 - angle

        return angle
