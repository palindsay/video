import argparse
import os
import random
import cv2
from tqdm import tqdm

def extract_frames(input_dir, output_dir, num_frames, mode):
    os.makedirs(output_dir, exist_ok=True)
    video_files = [f for f in os.listdir(input_dir) if f.endswith('.mp4')]

    for video_file in video_files:
        video_path = os.path.join(input_dir, video_file)
        cap = cv2.VideoCapture(video_path)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Skip the first 100 frames
        start_frame = 100
        if total_frames <= start_frame:
            print(f"Skipping {video_file}: Not enough frames")
            continue

        if mode in [1, 3]:
            interval = (total_frames - start_frame) // num_frames
        
        frames_to_extract = []
        
        if mode == 1:  # Evenly divided
            frames_to_extract = range(start_frame, total_frames, interval)[:num_frames]
        elif mode == 2:  # Random
            frames_to_extract = random.sample(range(start_frame, total_frames), num_frames)
        elif mode == 3:  # Combined
            even_frames = range(start_frame, total_frames, interval * 2)[:num_frames // 2]
            random_frames = random.sample(list(set(range(start_frame, total_frames)) - set(even_frames)), num_frames - len(even_frames))
            frames_to_extract = sorted(list(even_frames) + random_frames)

        base_name = os.path.splitext(video_file)[0]
        
        for i, frame_number in enumerate(tqdm(frames_to_extract, desc=f"Processing {video_file}")):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            if ret:
                output_path = os.path.join(output_dir, f"{base_name}_frame_{i+1:04d}.png")
                cv2.imwrite(output_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])

        cap.release()

def main():
    parser = argparse.ArgumentParser(description="Extract frames from AV1 MP4 videos")
    parser.add_argument("input_dir", help="Input directory containing MP4 files")
    parser.add_argument("output_dir", help="Output directory for extracted frames")
    parser.add_argument("num_frames", type=int, help="Number of frames to extract per video")
    parser.add_argument("mode", type=int, choices=[1, 2, 3], help="1: Evenly divided, 2: Random, 3: Combined")
    args = parser.parse_args()

    extract_frames(args.input_dir, args.output_dir, args.num_frames, args.mode)

if __name__ == "__main__":
    main()

