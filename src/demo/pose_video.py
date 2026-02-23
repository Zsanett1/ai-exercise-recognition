import cv2
import mediapipe as mp
import os

#Folder with input videos
input_folder = "videos/_test"

#Mediapipe initialization
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

#Check if input folder exists
if not os.path.exists(input_folder):
    print(f"Error: A(z) {input_folder} folder not found!")
    exit()

#List all video files in the folder
video_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.avi', '.mov'))]

if not video_files:
    print("No videos in the folder!")
    exit()

#Analyze video frames
with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    for video_name in video_files:
        video_path = os.path.join(input_folder, video_name)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_name}")
            continue

        print(f"Processing video: {video_name}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Resize frame for faster processing
            frame = cv2.resize(frame, (640, 480))

            # Convert to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            results = pose.process(image)

            # Convert back to BGR
            image.flags.writeable = True
            frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Draw landmarks if detected
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)
                )

            cv2.imshow('Pose Detection', frame)

            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()

cv2.destroyAllWindows()
print("All videos processed.")