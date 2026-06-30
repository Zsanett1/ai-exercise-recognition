import time

from .base import BaseExerciseRule, RuleResult


class SupermanRule(BaseExerciseRule):
    def __init__(
        self,
        required_consecutive_frames=3,
        raised_lift_threshold=0.035,
        lowered_lift_threshold=0.015,
        correct_upper_lift_min=0.035,
        correct_leg_lift_min=0.03,
        hold_duration_seconds=10,
        max_missing_frames=5,
    ):
        self.required_consecutive_frames = required_consecutive_frames
        self.raised_lift_threshold = raised_lift_threshold
        self.lowered_lift_threshold = lowered_lift_threshold
        self.correct_upper_lift_min = correct_upper_lift_min
        self.correct_leg_lift_min = correct_leg_lift_min
        self.hold_duration_seconds = hold_duration_seconds
        self.max_missing_frames = max_missing_frames

        self.superman_stage = "down"
        self.raised_frames = 0
        self.lowered_frames = 0
        self.missing_frames = 0
        self.max_upper_lift_during_rep = None
        self.max_leg_lift_during_rep = None
        self.raised_hold_started_at = None
        self.capture_highest_upper_body_frame = False
        self.capture_highest_leg_frame = False

    def validate_activation(self, landmarks):
        metrics = self._get_pose_metrics(landmarks)
        if metrics is None:
            return False

        return (
            metrics["upper_body_lift"] >= self.lowered_lift_threshold
            and metrics["leg_lift"] >= self.lowered_lift_threshold
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

        if self.capture_highest_upper_body_frame:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=True,
                feedback=None,
                feedback_code="superman_upper_body_not_lifted_enough",
                feedback_level=None,
                feedback_severity=self.max_upper_lift_during_rep,
                capture_feedback_frame=True,
            )

        if self.capture_highest_leg_frame:
            capture_result = RuleResult(
                rep_completed=False,
                keep_active=True,
                is_correct=True,
                feedback=None,
                feedback_code="superman_legs_not_lifted_enough",
                feedback_level=None,
                feedback_severity=self.max_leg_lift_during_rep,
                capture_feedback_frame=True,
            )

        if (
            metrics["upper_body_lift"] >= self.raised_lift_threshold
            and metrics["leg_lift"] >= self.raised_lift_threshold
        ):
            self.raised_frames += 1
            self.lowered_frames = 0
            if self.raised_hold_started_at is None:
                self.raised_hold_started_at = time.monotonic()
        elif (
            metrics["upper_body_lift"] <= self.lowered_lift_threshold
            and metrics["leg_lift"] <= self.lowered_lift_threshold
        ):
            self.lowered_frames += 1
            self.raised_frames = 0
            self.raised_hold_started_at = None
        else:
            self.raised_frames = 0
            self.lowered_frames = 0
            self.raised_hold_started_at = None

        if self.superman_stage == "down" and self.raised_frames >= self.required_consecutive_frames:
            self.superman_stage = "up"

        if (
            self.superman_stage == "up"
            and self.raised_hold_started_at is not None
            and time.monotonic() - self.raised_hold_started_at >= self.hold_duration_seconds
        ):
            return RuleResult(
                rep_completed=False,
                hold_completed=True,
                keep_active=True,
                is_correct=True,
                feedback="Good superman hold.",
                feedback_code="superman_correct_hold",
                feedback_level="success",
            )

        if self.superman_stage == "up" and self.lowered_frames >= self.required_consecutive_frames:
            result = self._build_superman_feedback()
            self.reset()
            return result
        
        if capture_result is not None:
            return capture_result

        return RuleResult()

    def reset(self):
        self.superman_stage = "down"
        self.raised_frames = 0
        self.lowered_frames = 0
        self.missing_frames = 0
        self.max_upper_lift_during_rep = None
        self.max_leg_lift_during_rep = None
        self.raised_hold_started_at = None
        self.capture_highest_upper_body_frame = False
        self.capture_highest_leg_frame = False

    def _update_rep_metrics(self, metrics):
        self.capture_highest_upper_body_frame = False
        self.capture_highest_leg_frame = False
        if self.max_upper_lift_during_rep is None or metrics["upper_body_lift"] > self.max_upper_lift_during_rep:
            self.max_upper_lift_during_rep = metrics["upper_body_lift"]
            self.capture_highest_upper_body_frame = True

        if self.max_leg_lift_during_rep is None or metrics["leg_lift"] > self.max_leg_lift_during_rep:
            self.max_leg_lift_during_rep = metrics["leg_lift"]
            self.capture_highest_leg_frame = True

    def _build_superman_feedback(self):
        if self.max_upper_lift_during_rep is None or self.max_leg_lift_during_rep is None:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Superman range of motion could not be measured clearly.",
                feedback_code="superman_range_not_measured",
                feedback_level="warning",
            )

        if self.max_upper_lift_during_rep < self.correct_upper_lift_min:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Lift your chest and arms a little higher with control.",
                feedback_code="superman_upper_body_not_lifted_enough",
                feedback_level="warning",
            )

        if self.max_leg_lift_during_rep < self.correct_leg_lift_min:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Lift your legs a little higher while keeping the movement controlled.",
                feedback_code="superman_legs_not_lifted_enough",
                feedback_level="warning",
            )

        return RuleResult(
            rep_completed=True,
            keep_active=False,
            is_correct=True,
            feedback="Good superman.",
            feedback_code="superman_correct",
            feedback_level="success",
        )

    def _get_pose_metrics(self, landmarks):
        if not landmarks:
            return None

        shoulder_center_y = (landmarks[11].y + landmarks[12].y) / 2
        hip_center_y = (landmarks[23].y + landmarks[24].y) / 2
        ankle_center_y = (landmarks[27].y + landmarks[28].y) / 2

        upper_body_lift = hip_center_y - shoulder_center_y
        leg_lift = hip_center_y - ankle_center_y

        return {
            "upper_body_lift": upper_body_lift,
            "leg_lift": leg_lift,
        }
