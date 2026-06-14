from .base import BaseExerciseRule, RuleResult


class CalfRaisesRule(BaseExerciseRule):
    def __init__(
        self,
        required_consecutive_frames=3,
        raised_heel_threshold=0.035,
        lowered_heel_threshold=0.015,
        correct_raise_min_height=0.04,
        correct_lower_max_height=0.02,
        max_missing_frames=5,
    ):
        self.required_consecutive_frames = required_consecutive_frames
        self.raised_heel_threshold = raised_heel_threshold
        self.lowered_heel_threshold = lowered_heel_threshold
        self.correct_raise_min_height = correct_raise_min_height
        self.correct_lower_max_height = correct_lower_max_height
        self.max_missing_frames = max_missing_frames

        self.calf_raise_stage = "down"
        self.raised_frames = 0
        self.lowered_frames = 0
        self.missing_frames = 0
        self.max_heel_lift_during_rep = None
        self.min_heel_lift_during_rep = None

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

        if metrics["average_heel_lift"] >= self.raised_heel_threshold:
            self.raised_frames += 1
            self.lowered_frames = 0
        elif metrics["average_heel_lift"] <= self.lowered_heel_threshold:
            self.lowered_frames += 1
            self.raised_frames = 0
        else:
            self.raised_frames = 0
            self.lowered_frames = 0

        if self.calf_raise_stage == "down" and self.raised_frames >= self.required_consecutive_frames:
            self.calf_raise_stage = "up"

        if self.calf_raise_stage == "up" and self.lowered_frames >= self.required_consecutive_frames:
            result = self._build_calf_raise_feedback()
            self.reset()
            return result

        return RuleResult()

    def reset(self):
        self.calf_raise_stage = "down"
        self.raised_frames = 0
        self.lowered_frames = 0
        self.missing_frames = 0
        self.max_heel_lift_during_rep = None
        self.min_heel_lift_during_rep = None

    def _update_rep_metrics(self, metrics):
        heel_lift = metrics["average_heel_lift"]

        if self.max_heel_lift_during_rep is None:
            self.max_heel_lift_during_rep = heel_lift
        else:
            self.max_heel_lift_during_rep = max(
                self.max_heel_lift_during_rep,
                heel_lift,
            )

        if self.min_heel_lift_during_rep is None:
            self.min_heel_lift_during_rep = heel_lift
        else:
            self.min_heel_lift_during_rep = min(
                self.min_heel_lift_during_rep,
                heel_lift,
            )

    def _build_calf_raise_feedback(self):
        if self.max_heel_lift_during_rep is None or self.min_heel_lift_during_rep is None:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Calf raise range of motion could not be measured clearly.",
                feedback_code="range_not_measured",
                feedback_level="warning",
            )

        if self.max_heel_lift_during_rep < self.correct_raise_min_height:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Rise higher onto the balls of your feet.",
                feedback_code="not_raised_high_enough",
                feedback_level="warning",
            )

        if self.min_heel_lift_during_rep > self.correct_lower_max_height:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Lower your heels fully before the next rep.",
                feedback_code="not_lowered_enough",
                feedback_level="warning",
            )

        return RuleResult(
            rep_completed=True,
            keep_active=False,
            is_correct=True,
            feedback="Good calf raise.",
            feedback_code="correct_calf_raise",
            feedback_level="success",
        )

    def _get_pose_metrics(self, landmarks):
        if not landmarks:
            return None

        left_heel_lift = landmarks[31].y - landmarks[29].y
        right_heel_lift = landmarks[32].y - landmarks[30].y
        average_heel_lift = (left_heel_lift + right_heel_lift) / 2

        return {
            "average_heel_lift": average_heel_lift,
        }
