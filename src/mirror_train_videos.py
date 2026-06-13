import cv2
from pathlib import Path


base_dir = Path(__file__).resolve().parent.parent
train_dir = base_dir / "videos" / "train"
mirror_suffix = "_mirrored"


def mirror_video(video_path):
    output_path = video_path.with_name(f"{video_path.stem}{mirror_suffix}{video_path.suffix}")

    if output_path.exists():
        print(f"Skipping existing mirrored video: {output_path.relative_to(base_dir)}")
        return

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Could not open video: {video_path.relative_to(base_dir)}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if not fps or fps <= 0:
        fps = 30

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        mirrored_frame = cv2.flip(frame, 1)
        writer.write(mirrored_frame)
        frame_count += 1

    cap.release()
    writer.release()
    print(f"Created {output_path.relative_to(base_dir)} -> frames: {frame_count}")


if not train_dir.exists():
    print(f"Error, train directory not found: {train_dir}")
    exit()

for exercise_dir in sorted(train_dir.iterdir()):
    if not exercise_dir.is_dir():
        continue

    print(f"\nProcessing train category: {exercise_dir.name}")
    for video_path in sorted(exercise_dir.glob("*.mp4")):
        if video_path.stem.endswith(mirror_suffix):
            continue

        mirror_video(video_path)

print("\nMirroring finished")
