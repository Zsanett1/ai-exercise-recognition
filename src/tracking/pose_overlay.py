import av
import cv2
import mediapipe as mp
from pathlib import Path
import time
from datetime import datetime
from src.tracking.exercise_session import ExerciseTrackingSession

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pending_error_frames = {}

pose = mp_pose.Pose(min_detection_confidence = 0.5, min_tracking_confidence = 0.5,)

tracking_session = ExerciseTrackingSession()

last_display_label = None
last_display_confidence = 0.0
last_total_reps = 0
last_correct_reps = 0
display_label_until = 0
captured_feedback_codes = set()
metrics_window_started_at = None
metrics_window_frames = 0
metrics_first_frame_at = None
metrics_last_frame_at = None
metrics_total_frames = 0
metrics_current_fps = 0.0
metrics_resolution = None
metrics_current_latency_ms = 0.0
metrics_total_latency_ms = 0.0
metrics_latency_samples = 0

base_dir = Path(__file__).resolve().parent.parent.parent
screenshot_dir = base_dir / "assets" / "session_screenshots"

def reset_tracking_session(target_label = None):
    global tracking_session, last_display_label, last_display_confidence
    global last_total_reps, last_correct_reps, display_label_until, captured_feedback_codes, pending_error_frames
    global metrics_window_started_at, metrics_window_frames, metrics_first_frame_at, metrics_last_frame_at
    global metrics_total_frames, metrics_current_fps, metrics_resolution
    global metrics_current_latency_ms, metrics_total_latency_ms, metrics_latency_samples

    tracking_session = ExerciseTrackingSession(target_label = target_label)
    last_display_label = None
    last_display_confidence = 0.0
    last_total_reps = 0
    last_correct_reps = 0
    display_label_until = 0
    captured_feedback_codes = set()
    pending_error_frames = {}
    metrics_window_started_at = None
    metrics_window_frames = 0
    metrics_first_frame_at = None
    metrics_last_frame_at = None
    metrics_total_frames = 0
    metrics_current_fps = 0.0
    metrics_resolution = None
    metrics_current_latency_ms = 0.0
    metrics_total_latency_ms = 0.0
    metrics_latency_samples = 0

def update_tracking_metrics(image):
    global metrics_window_started_at, metrics_window_frames, metrics_first_frame_at, metrics_last_frame_at
    global metrics_total_frames, metrics_current_fps, metrics_resolution

    now = time.time()
    height, width = image.shape[:2]
    metrics_resolution = (width, height)
    metrics_total_frames += 1
    metrics_last_frame_at = now
    if metrics_first_frame_at is None:
        metrics_first_frame_at = now
    if metrics_window_started_at is None:
        metrics_window_started_at = now
        metrics_window_frames = 0
    metrics_window_frames += 1
    window_elapsed = now - metrics_window_started_at
    if window_elapsed >= 1.0:
        metrics_current_fps = metrics_window_frames / window_elapsed
        metrics_window_started_at = now
        metrics_window_frames = 0

def update_processing_latency(started_at):
    global metrics_current_latency_ms, metrics_total_latency_ms, metrics_latency_samples

    metrics_current_latency_ms = (time.perf_counter() - started_at) * 1000
    metrics_total_latency_ms += metrics_current_latency_ms
    metrics_latency_samples += 1

def get_tracking_metrics():
    average_fps = 0.0
    average_latency_ms = 0.0
    if metrics_first_frame_at and metrics_last_frame_at and metrics_last_frame_at > metrics_first_frame_at:
        average_fps = metrics_total_frames / (metrics_last_frame_at - metrics_first_frame_at)
    if metrics_latency_samples > 0:
        average_latency_ms = metrics_total_latency_ms / metrics_latency_samples
    return {
        "current_fps": metrics_current_fps,
        "average_fps": average_fps,
        "resolution": metrics_resolution,
        "total_frames": metrics_total_frames,
        "current_latency_ms": metrics_current_latency_ms,
        "average_latency_ms": average_latency_ms,
    }

def save_error_screenshot(image, frame_decision):
    global pending_error_frames
    feedback_code = frame_decision.feedback_code or "unknown_error"
    if feedback_code in captured_feedback_codes:
        return
    screenshot_dir.mkdir(parents = True, exist_ok = True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rep_{frame_decision.total_reps}_{feedback_code}_{timestamp}.jpg"
    image_path = screenshot_dir / filename
    pending_frame = pending_error_frames.pop(feedback_code, None)
    image_to_save = pending_frame["image"] if pending_frame else image
    cv2.imwrite(str(image_path), image_to_save)
    relative_path = image_path.relative_to(base_dir).as_posix()
    captured_feedback_codes.add(feedback_code)
    tracking_session.add_error_screenshot(
        rep_number = frame_decision.total_reps, feedback_code = feedback_code,
        feedback = frame_decision.feedback or "No feedback recorded.", image_path = relative_path,
    )
    pending_error_frames.clear()

def remember_most_critical_feedback_frame(image, frame_decision):
    feedback_code = frame_decision.feedback_code
    if not feedback_code:
        return
    severity = frame_decision.feedback_severity
    if severity is None:
        severity = 0.0
    current_frame = pending_error_frames.get(feedback_code)
    if current_frame is None or severity >= current_frame["severity"]:
        pending_error_frames[feedback_code] = {
            "image": image.copy(),
            "severity": severity,
        }

def draw_pose_landmarks(frame):
    global last_display_label, last_display_confidence, last_total_reps, last_correct_reps, display_label_until
    frame_started_at = time.perf_counter()
    image = frame.to_ndarray(format = "bgr24")
    update_tracking_metrics(image)
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
        if frame_decision.capture_feedback_frame and frame_decision.feedback_code:
            remember_most_critical_feedback_frame(analysis_image, frame_decision)
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
        update_processing_latency(frame_started_at)
        # metrics = get_tracking_metrics()
        # resolution = metrics["resolution"]
        # resolution_label = f"{resolution[0]}x{resolution[1]}" if resolution else "unknown"
        cv2.rectangle(image, (0, 0), (390, 105), (15, 23, 42), -1)
        cv2.putText(image, f"Action: {label}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA,)
        cv2.putText(image, f"Confidence: {confidence:.2f}", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 184, 166), 2, cv2.LINE_AA,)
        cv2.putText(image, f"Reps: {reps}", (15, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 184, 166), 2, cv2.LINE_AA,)
        # cv2.putText(image, f"FPS: {metrics['current_fps']:.1f} | Res: {resolution_label}", (15, 116), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (148, 163, 184), 2, cv2.LINE_AA,)
        # cv2.putText(image, f"Latency: {metrics['current_latency_ms']:.0f} ms", (15, 142), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (148, 163, 184), 2, cv2.LINE_AA,)

    return av.VideoFrame.from_ndarray(image, format = "bgr24")

def get_tracking_summary():
    return tracking_session.get_summary()
