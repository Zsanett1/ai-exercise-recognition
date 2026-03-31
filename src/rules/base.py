from dataclasses import dataclass


@dataclass
class FrameDecision:
    active_label: str | None
    active_confidence: float
    total_reps: int


class BaseExerciseRule:
    def validate_activation(self, landmarks):
        return True

    def on_activate(self):
        pass

    def process_active_frame(self, landmarks):
        return False, True

    def reset(self):
        pass


class RuleManager:
    def __init__(
        self,
        class_names,
        hidden_classes,
        min_confidence_to_display,
        required_consecutive_frames,
        required_non_exercise_frames,
        rules=None,
    ):
        self.class_names = class_names
        self.hidden_classes = hidden_classes
        self.min_confidence_to_display = min_confidence_to_display
        self.required_consecutive_frames = required_consecutive_frames
        self.required_non_exercise_frames = required_non_exercise_frames
        self.rules = rules or {}

        self.last_detected_label = None
        self.consecutive_detection_count = 0
        self.active_label = None
        self.active_confidence = 0.0
        self.non_exercise_frame_count = 0
        self.exercise_counts = {
            label: 0 for label in class_names if label not in hidden_classes
        }

    def process_frame(self, label, confidence, landmarks):
        rule = self.rules.get(label) if label else None
        is_candidate = False

        if label and label not in self.hidden_classes and confidence >= self.min_confidence_to_display:
            is_candidate = True
            if rule:
                is_candidate = rule.validate_activation(landmarks)

        if is_candidate:
            if label == self.last_detected_label:
                self.consecutive_detection_count += 1
            else:
                self.last_detected_label = label
                self.consecutive_detection_count = 1
            self.non_exercise_frame_count = 0
        else:
            self.last_detected_label = None
            self.consecutive_detection_count = 0
            self.non_exercise_frame_count += 1

        if (
            is_candidate
            and self.consecutive_detection_count >= self.required_consecutive_frames
            and self.active_label != label
        ):
            self.active_label = label
            self.active_confidence = confidence
            active_rule = self.rules.get(label)
            if active_rule:
                active_rule.on_activate()

        if self.active_label:
            active_rule = self.rules.get(self.active_label)

            if active_rule:
                rep_completed, keep_active = active_rule.process_active_frame(landmarks)
                if rep_completed:
                    self.exercise_counts[self.active_label] += 1
                if not keep_active:
                    active_rule.reset()
                    self._clear_active_state()
            elif self.non_exercise_frame_count >= self.required_non_exercise_frames:
                self.exercise_counts[self.active_label] += 1
                self._clear_active_state()

        return FrameDecision(
            active_label=self.active_label,
            active_confidence=self.active_confidence,
            total_reps=sum(self.exercise_counts.values()),
        )

    def _clear_active_state(self):
        self.active_label = None
        self.active_confidence = 0.0
        self.last_detected_label = None
        self.consecutive_detection_count = 0
