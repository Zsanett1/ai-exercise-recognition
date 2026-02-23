import cv2
import mediapipe as mp
import os

#Folder with input images
input_folder = "images"

#Mediapipe initialization
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

#Check if input folder exists
if not os.path.exists(input_folder):
    print(f"Error: A(z) {input_folder} folder not found!")
    exit()

#List all image files in the input folder
image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

if not image_files:
    print("No images in the folder!")
    exit()

#Process each image
with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
    for file_name in image_files:
        input_path = os.path.join(input_folder, file_name)
        base_name, ext = os.path.splitext(file_name)
        output_path = os.path.join(input_folder, f"{base_name}.landmarks{ext}")

        print(f"Processing: {file_name}")

        image = cv2.imread(input_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
            )

            cv2.imwrite(output_path, image)
            print(f"Saved with landmarks: {output_path}")
        else:
            print(f"No pose detected: {file_name}")

print("Processing complete.")
