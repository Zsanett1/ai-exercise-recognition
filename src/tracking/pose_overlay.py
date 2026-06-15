import av
import cv2
import mediapipe as mp
from pathlib import Path
import time
from datetime import datetime
from src.tracking.exercise_session import ExerciseTrackingSession

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(min_detection_confidence = 0.5, min_tracking_confidence = 0.5,)

tracking_session = ExerciseTrackingSession()

last_display_label = None
last_display_confidence = 0.0
last_total_reps = 0
last_correct_reps = 0
display_label_until = 0
captured_feedback_codes = set()

base_dir = Path(__file__).resolve().parent.parent.parent
screenshot_dir = base_dir / "assets" / "session_screenshots"

def reset_tracking_session():
    global tracking_session, last_display_label, last_display_confidence
    global last_total_reps, last_correct_reps, display_label_until, captured_feedback_codes

    tracking_session = ExerciseTrackingSession()
    last_display_label = None
    last_display_confidence = 0.0
    last_total_reps = 0
    last_correct_reps = 0
    display_label_until = 0
    captured_feedback_codes = set()

def save_error_screenshot(image, frame_decision):
    feedback_code = frame_decision.feedback_code or "unknown_error"
    if feedback_code in captured_feedback_codes:
        return
    screenshot_dir.mkdir(parents = True, exist_ok = True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rep_{frame_decision.total_reps}_{feedback_code}_{timestamp}.jpg"
    image_path = screenshot_dir / filename
    cv2.imwrite(str(image_path), image)
    relative_path = image_path.relative_to(base_dir).as_posix()
    captured_feedback_codes.add(feedback_code)
    tracking_session.add_error_screenshot(
        rep_number = frame_decision.total_reps, feedback_code = feedback_code,
        feedback = frame_decision.feedback or "No feedback recorded.", image_path = relative_path,
    )

def draw_pose_landmarks(frame):
    global last_display_label, last_display_confidence, last_total_reps, last_correct_reps, display_label_until
    image = frame.to_ndarray(format = "bgr24")
    analysis_image = image.copy()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_image)
    frame_decision = None
    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        frame_decision = tracking_session.process_landmarks(landmarks)
        mp_drawing.draw_landmarks(analysis_image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,)
    else:
        frame_decision = tracking_session.process_landmarks(None)
    if frame_decision:
        current_time = time.time()
        reps = frame_decision.total_reps
        correct_reps = frame_decision.correct_reps
        if reps > last_total_reps and correct_reps == last_correct_reps:
            save_error_screenshot(analysis_image, frame_decision)
        if frame_decision.display_label and reps > last_total_reps:
            last_display_label = frame_decision.display_label
            last_display_confidence = frame_decision.display_confidence
            display_label_until = current_time + 2.0
        elif frame_decision.display_label == "plank":
            last_display_label = frame_decision.display_label
            last_display_confidence = frame_decision.display_confidence
            display_label_until = current_time + 2.0
        last_total_reps = reps
        if current_time <= display_label_until and last_display_label:
            label = last_display_label
            confidence = last_display_confidence
        else:
            label = "waiting"
            confidence = 0.0
        last_correct_reps = correct_reps
        cv2.rectangle(image, (0, 0), (320, 95), (15, 23, 42), -1)
        cv2.putText(image, f"Action: {label}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA,)
        cv2.putText(image, f"Confidence: {confidence:.2f}", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 184, 166), 2, cv2.LINE_AA,)
        cv2.putText(image, f"Reps: {reps}", (15, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 184, 166), 2, cv2.LINE_AA,)

    return av.VideoFrame.from_ndarray(image, format = "bgr24")

def get_tracking_summary():
    return tracking_session.get_summary()
