from dataclasses import dataclass


@dataclass
class FrameDecision:
    active_label: str | None
    active_confidence: float
    display_label: str | None
    display_confidence: float
    total_reps: int
    correct_reps: int
    feedback: str | None
    feedback_code: str | None
    feedback_level: str | None
    feedback_severity: float | None
    capture_feedback_frame: bool

@dataclass
class RuleResult:
    rep_completed: bool = False
    hold_completed: bool = False
    keep_active: bool = True
    is_correct: bool = True
    feedback: str | None = None
    feedback_code: str | None = None
    feedback_level: str | None = None
    feedback_severity: float | None = None
    capture_feedback_frame: bool = False

class BaseExerciseRule:
    def validate_activation(self, landmarks):
        return True

    def on_activate(self):
        pass

    def process_active_frame(self, landmarks):
        return RuleResult()

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
        min_confidence_to_consider=None,
        rules=None,
    ):
        self.class_names = class_names
        self.hidden_classes = hidden_classes
        self.min_confidence_to_display = min_confidence_to_display
        self.min_confidence_to_consider = min_confidence_to_consider or min_confidence_to_display
        self.required_consecutive_frames = required_consecutive_frames
        self.required_non_exercise_frames = required_non_exercise_frames
        self.rules = rules or {}

        self.last_detected_label = None
        self.consecutive_detection_count = 0
        self.active_label = None
        self.active_confidence = 0.0
        self.display_label = None
        self.display_confidence = 0.0
        self.non_exercise_frame_count = 0
        self.exercise_counts = {
            label: 0 for label in class_names if label not in hidden_classes
        }
        self.correct_counts = {
            label: 0 for label in class_names if label not in hidden_classes
        }
        self.current_feedback = None
        self.current_feedback_code = None
        self.current_feedback_level = None
        self.current_feedback_severity = None
        self.label_priority = {
            "shoulder_press": 0,
            "overhead_extension": 1,
        }

    def process_candidates(self, candidates, landmarks):
        selected_label = None
        selected_confidence = 0.0

        prioritized_candidates = sorted(
            candidates,
            key=lambda candidate: (
                self.label_priority.get(candidate[0], 10),
                -candidate[1],
            ),
        )

        for label, confidence in prioritized_candidates:
            if self._is_valid_candidate(
                label,
                confidence,
                landmarks,
                min_confidence=self.min_confidence_to_consider,
            ):
                selected_label = label
                selected_confidence = confidence
                break

        return self.process_frame(
            selected_label,
            selected_confidence,
            landmarks,
            min_confidence=self.min_confidence_to_consider,
        )

    def process_frame(self, label, confidence, landmarks, min_confidence=None):
        rule = self.rules.get(label) if label else None
        is_candidate = self._is_valid_candidate(
            label,
            confidence,
            landmarks,
            min_confidence=min_confidence,
        )

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
        capture_feedback_frame = False
        if self.active_label:
            active_rule = self.rules.get(self.active_label)

            if active_rule:
                rule_result = active_rule.process_active_frame(landmarks)
                capture_feedback_frame = rule_result.capture_feedback_frame
                self.current_feedback = rule_result.feedback
                self.current_feedback_code = rule_result.feedback_code
                self.current_feedback_level = rule_result.feedback_level
                self.current_feedback_severity = rule_result.feedback_severity

                if rule_result.rep_completed:
                    self.exercise_counts[self.active_label] += 1
                    if rule_result.is_correct:
                        self.correct_counts[self.active_label] += 1
                    self.display_label = self.active_label
                    self.display_confidence = self.active_confidence
                elif rule_result.hold_completed:
                    self.display_label = self.active_label
                    self.display_confidence = self.active_confidence
                if not rule_result.keep_active:
                    active_rule.reset()
                    self._clear_active_state()
            elif self.non_exercise_frame_count >= self.required_non_exercise_frames:
                self.exercise_counts[self.active_label] += 1
                self._clear_active_state()

        return FrameDecision(
            active_label=self.active_label,
            active_confidence=self.active_confidence,
            display_label=self.display_label,
            display_confidence=self.display_confidence,
            total_reps=sum(self.exercise_counts.values()),
            correct_reps=sum(self.correct_counts.values()),
            feedback=self.current_feedback,
            feedback_code=self.current_feedback_code,
            feedback_level=self.current_feedback_level,
            feedback_severity=getattr(self, "current_feedback_severity", None),
            capture_feedback_frame=capture_feedback_frame,
        )

    def _is_valid_candidate(self, label, confidence, landmarks, min_confidence=None):
        if not label or label in self.hidden_classes:
            return False

        confidence_threshold = min_confidence or self.min_confidence_to_display
        if confidence < confidence_threshold:
            return False

        rule = self.rules.get(label)
        if rule:
            return rule.validate_activation(landmarks)

        return True

    def _clear_active_state(self):
        self.active_label = None
        self.active_confidence = 0.0
        self.last_detected_label = None
        self.consecutive_detection_count = 0
