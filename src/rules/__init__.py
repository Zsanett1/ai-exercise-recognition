from .bicep_curl import BicepCurlRule
from .base import RuleManager
from .calf_raises import CalfRaisesRule
from .crunch import CrunchRule
from .overhead_extension import OverheadExtensionRule
from .plank import PlankRule
from .push_up import PushUpRule
from .shoulder_press import ShoulderPressRule
from .squat import SquatRule
from .superman import SupermanRule


def build_rule_manager(
    class_names,
    hidden_classes,
    min_confidence_to_display,
    required_consecutive_frames,
    required_non_exercise_frames,
    min_confidence_to_consider=None,
):
    rules = {}

    if "squat" in class_names:
        rules["squat"] = SquatRule(
            required_consecutive_frames=required_consecutive_frames
        )

    if "push_up" in class_names:
        rules["push_up"] = PushUpRule(
            required_consecutive_frames=required_consecutive_frames
        )

    if "plank" in class_names:
        rules["plank"] = PlankRule()

    if "bicep_curl" in class_names:
        rules["bicep_curl"] = BicepCurlRule(
            required_consecutive_frames=required_consecutive_frames
        )

    if "shoulder_press" in class_names:
        rules["shoulder_press"] = ShoulderPressRule(
            required_consecutive_frames=required_consecutive_frames
        )

    if "overhead_extension" in class_names:
        rules["overhead_extension"] = OverheadExtensionRule(
            required_consecutive_frames=required_consecutive_frames
        )

    if "calf_raises" in class_names:
        rules["calf_raises"] = CalfRaisesRule(
            required_consecutive_frames=required_consecutive_frames
        )

    if "calf_raise" in class_names:
        rules["calf_raise"] = CalfRaisesRule(
            required_consecutive_frames=required_consecutive_frames
        )

    if "crunch" in class_names:
        rules["crunch"] = CrunchRule(
            required_consecutive_frames=required_consecutive_frames
        )

    if "superman" in class_names:
        rules["superman"] = SupermanRule(
            required_consecutive_frames=required_consecutive_frames
        )

    return RuleManager(
        class_names=class_names,
        hidden_classes=hidden_classes,
        min_confidence_to_display=min_confidence_to_display,
        required_consecutive_frames=required_consecutive_frames,
        required_non_exercise_frames=required_non_exercise_frames,
        min_confidence_to_consider=min_confidence_to_consider,
        rules=rules,
    )
