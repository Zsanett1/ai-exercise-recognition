from .base import BaseExerciseRule, RuleResult


class CrunchRule(BaseExerciseRule):
    def __init__(
        self,
        required_consecutive_frames=3,
        crunch_up_threshold=0.06,
        crunch_down_threshold=0.02,
        correct_crunch_min_lift=0.05,
        correct_return_max_lift=0.03,
        max_missing_frames=5,
    ):
        self.required_consecutive_frames = required_consecutive_frames
        self.crunch_up_threshold = crunch_up_threshold
        self.crunch_down_threshold = crunch_down_threshold
        self.correct_crunch_min_lift = correct_crunch_min_lift
        self.correct_return_max_lift = correct_return_max_lift
        self.max_missing_frames = max_missing_frames

        self.crunch_stage = "down"
        self.up_frames = 0
        self.down_frames = 0
        self.missing_frames = 0
        self.start_shoulder_y = None
        self.max_shoulder_lift_during_rep = None
        self.min_shoulder_lift_during_rep = None

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

        shoulder_lift = self._get_shoulder_lift(metrics["shoulder_y"])

        if shoulder_lift >= self.crunch_up_threshold:
            self.up_frames += 1
            self.down_frames = 0
        elif shoulder_lift <= self.crunch_down_threshold:
            self.down_frames += 1
            self.up_frames = 0
        else:
            self.up_frames = 0
            self.down_frames = 0

        if self.crunch_stage == "down" and self.up_frames >= self.required_consecutive_frames:
            self.crunch_stage = "up"

        if self.crunch_stage == "up" and self.down_frames >= self.required_consecutive_frames:
            result = self._build_crunch_feedback()
            self.reset()
            return result

        return RuleResult()

    def reset(self):
        self.crunch_stage = "down"
        self.up_frames = 0
        self.down_frames = 0
        self.missing_frames = 0
        self.start_shoulder_y = None
        self.max_shoulder_lift_during_rep = None
        self.min_shoulder_lift_during_rep = None

    def _update_rep_metrics(self, metrics):
        shoulder_lift = self._get_shoulder_lift(metrics["shoulder_y"])

        if self.max_shoulder_lift_during_rep is None:
            self.max_shoulder_lift_during_rep = shoulder_lift
        else:
            self.max_shoulder_lift_during_rep = max(
                self.max_shoulder_lift_during_rep,
                shoulder_lift,
            )

        if self.min_shoulder_lift_during_rep is None:
            self.min_shoulder_lift_during_rep = shoulder_lift
        else:
            self.min_shoulder_lift_during_rep = min(
                self.min_shoulder_lift_during_rep,
                shoulder_lift,
            )

    def _get_shoulder_lift(self, shoulder_y):
        if self.start_shoulder_y is None or shoulder_y > self.start_shoulder_y:
            self.start_shoulder_y = shoulder_y

        return self.start_shoulder_y - shoulder_y

    def _build_crunch_feedback(self):
        if self.max_shoulder_lift_during_rep is None or self.min_shoulder_lift_during_rep is None:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Crunch range of motion could not be measured clearly.",
                feedback_code="range_not_measured",
                feedback_level="warning",
            )

        if self.max_shoulder_lift_during_rep < self.correct_crunch_min_lift:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Lift your shoulders a little higher during the crunch.",
                feedback_code="not_lifted_high_enough",
                feedback_level="warning",
            )

        if self.min_shoulder_lift_during_rep > self.correct_return_max_lift:
            return RuleResult(
                rep_completed=True,
                keep_active=False,
                is_correct=False,
                feedback="Lower back down with control before the next crunch.",
                feedback_code="not_lowered_enough",
                feedback_level="warning",
            )

        return RuleResult(
            rep_completed=True,
            keep_active=False,
            is_correct=True,
            feedback="Good crunch.",
            feedback_code="correct_crunch",
            feedback_level="success",
        )

    def _get_pose_metrics(self, landmarks):
        if not landmarks:
            return None

        left_shoulder = [landmarks[11].x, landmarks[11].y]
        right_shoulder = [landmarks[12].x, landmarks[12].y]

        shoulder_center = [
            (left_shoulder[0] + right_shoulder[0]) / 2,
            (left_shoulder[1] + right_shoulder[1]) / 2,
        ]

        return {
            "shoulder_y": shoulder_center[1],
        }
