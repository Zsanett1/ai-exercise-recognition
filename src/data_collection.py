import cv2
import mediapipe as mp
import pandas as pd
import os
from pathlib import Path

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode = False,
    min_detection_confidence = 0.5,
    min_tracking_confidence = 0.5
)

base_dir = Path(__file__).resolve().parent.parent
video_dir = base_dir / "videos"
output_dir = base_dir / "data" 
output_file = output_dir / "dataset.csv"

data_list = []
metadata_columns = ["label", "split", "source_file", "source_mtime"]
processed_videos = {}
existing_df = None

print("Collecting data, please wait")

if output_file.exists():
    existing_df = pd.read_csv(output_file)

    if {"split", "source_file", "source_mtime"}.issubset(existing_df.columns):
        processed_videos = (
            existing_df[["source_file", "source_mtime"]]
            .drop_duplicates()
            .set_index("source_file")["source_mtime"]
            .to_dict()
        )
        print(f"Found existing dataset with {len(processed_videos)} processed videos")
    else:
        print("Legacy dataset format detected, rebuilding dataset once to add source metadata")
        existing_df = None

if not os.path.exists(video_dir): 
    print(f"Error, '{video_dir}' is not found")
else:
    for split in ["train", "validation", "test"]:
        split_path = video_dir / split

        if not os.path.isdir(split_path):
            continue

        print(f"\nProcessing split: {split.upper()}")

        for label in os.listdir(split_path):
            folder_path = split_path / label

            if not os.path.isdir(folder_path):
                continue

            print(f"\nProcessing category: {label.upper()}")

            for video_name in os.listdir(folder_path):
                video_path = folder_path / video_name

                if not video_path.is_file():
                    continue

                video_key = str(video_path.relative_to(base_dir))
                video_mtime = video_path.stat().st_mtime

                if processed_videos.get(video_key) == video_mtime:
                    print(f"Skipping already processed video: {video_key}")
                    continue

                cap = cv2.VideoCapture(str(video_path))
                frame_count = 0

                while cap.isOpened():
                    ret, frame =cap.read()
                    if not ret:
                        break

                    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose.process(image_rgb)

                    if not results.pose_landmarks:
                        continue

                    landmarks = results.pose_landmarks.landmark

                    row = []
                    for lm in landmarks:
                        row.extend([lm.x, lm.y, lm.z, lm.visibility])

                    row = [label, split, video_key, video_mtime] + row
                    data_list.append(row)
                    frame_count += 1

                cap.release()
                print(f"Processed {video_key} -> collected frames: {frame_count}")

if data_list:
    columns = metadata_columns.copy()
    for i in range(33):
        columns.extend([f'x{i}', f'y{i}', f'z{i}', f'v{i}'])

    new_df = pd.DataFrame(data_list, columns=columns)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if existing_df is not None:
        updated_video_keys = new_df["source_file"].unique().tolist()
        existing_df = existing_df[~existing_df["source_file"].isin(updated_video_keys)]
        df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df = new_df

    df.to_csv(output_file, index = False)
    print(f"\nSuccess, dataset saved to: {output_file}")
    print(f"\nNew rows collected: {len(new_df)}")
    print(f"Total rows in dataset: {len(df)}")
else:
    if existing_df is not None:
        print("No new videos found, existing dataset kept unchanged")
    else:
        print("Error, no data collected")
