import os
import argparse
import cv2
import random

def extract_frames(video_path, output_dir, num_frames, mode):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Skip the first 100 frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    # Adjust total_frames to account for skipped frames
    total_frames -= 100

    if mode == 1:  # Evenly spaced
        frame_indices = [int(i * total_frames / num_frames) + 100 for i in range(num_frames)]
    elif mode == 2:  # Random
        frame_indices = random.sample(range(100, total_frames), num_frames)
    elif mode == 3:  # Combined
        even_frames = int(num_frames / 2)
        random_frames = num_frames - even_frames
        frame_indices = [int(i * total_frames / even_frames) + 100 for i in range(even_frames)] + random.sample(range(100, total_frames), random_frames)

    for frame_index in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        if ret:
            output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_{frame_index}.png")
            cv2.imwrite(output_path, frame)

    cap.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from AV1 MP4 videos")
    parser.add_argument("input_dir", help="Input directory containing video files")
    parser.add_argument("output_dir", help="Output directory for image frames")
    parser.add_argument("num_frames", type=int, help="Number of frames to extract")
    parser.add_argument("mode", type=int, choices=[1, 2, 3], help="Frame selection mode: 1-Evenly spaced, 2-Random, 3-Combined")

    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    for filename in os.listdir(args.input_dir):
        if filename.endswith(".mp4"):
            video_path = os.path.join(args.input_dir, filename)
            extract_frames(video_path, args.output_dir, args.num_frames, args.mode)

