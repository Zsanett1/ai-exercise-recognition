from .base import RuleManager
from .squat import SquatRule


def build_rule_manager(
    class_names,
    hidden_classes,
    min_confidence_to_display,
    required_consecutive_frames,
    required_non_exercise_frames,
):
    rules = {}

    if "squat" in class_names:
        rules["squat"] = SquatRule(
            required_consecutive_frames=required_consecutive_frames
        )

    return RuleManager(
        class_names=class_names,
        hidden_classes=hidden_classes,
        min_confidence_to_display=min_confidence_to_display,
        required_consecutive_frames=required_consecutive_frames,
        required_non_exercise_frames=required_non_exercise_frames,
        rules=rules,
    )
