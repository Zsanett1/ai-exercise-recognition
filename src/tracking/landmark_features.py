import math


LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
EPSILON = 1e-6


def _distance_2d(first_landmark, second_landmark):
    return math.sqrt(
        (first_landmark.x - second_landmark.x) ** 2
        + (first_landmark.y - second_landmark.y) ** 2
    )


def normalize_landmarks(landmarks):
    left_hip = landmarks[LEFT_HIP]
    right_hip = landmarks[RIGHT_HIP]
    left_shoulder = landmarks[LEFT_SHOULDER]
    right_shoulder = landmarks[RIGHT_SHOULDER]

    center_x = (left_hip.x + right_hip.x) / 2
    center_y = (left_hip.y + right_hip.y) / 2
    center_z = (left_hip.z + right_hip.z) / 2

    shoulder_width = _distance_2d(left_shoulder, right_shoulder)
    hip_width = _distance_2d(left_hip, right_hip)
    scale = max(shoulder_width, hip_width, EPSILON)

    row = []
    for landmark in landmarks:
        row.extend([
            (landmark.x - center_x) / scale,
            (landmark.y - center_y) / scale,
            (landmark.z - center_z) / scale,
            landmark.visibility,
        ])

    return row
