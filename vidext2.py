import os
import random
import argparse
import ffmpeg
from PIL import Image
import numpy as np

def extract_frames(input_dir, output_dir, num_frames, mode):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    video_files = [f for f in os.listdir(input_dir) if f.endswith(".mp4")]
    
    for video_file in video_files:
        video_path = os.path.join(input_dir, video_file)
        probe = ffmpeg.probe(video_path)
        duration = float(probe['streams'][0]['duration'])
        frame_rate = eval(probe['streams'][0]['r_frame_rate'])
        total_frames = int(duration * frame_rate)

        if total_frames <= 100:
            print(f"Video {video_file} is too short to process.")
            continue

        frames_to_extract = []

        if mode == 1:  # Evenly divided frames
            interval = (total_frames - 100) // num_frames
            frames_to_extract = [100 + i * interval for i in range(num_frames)]

        elif mode == 2:  # Randomly selected frames
            frames_to_extract = random.sample(range(101, total_frames), num_frames)

        elif mode == 3:  # Combined mode
            half = num_frames // 2
            interval = (total_frames - 100) // half
            even_frames = [100 + i * interval for i in range(half)]
            random_frames = random.sample(range(101, total_frames), half)
            frames_to_extract = even_frames + random_frames

        for i, frame_number in enumerate(frames_to_extract):
            frame_output_path = os.path.join(output_dir, f"{os.path.splitext(video_file)[0]}_frame_{i+1}.png")
            (
                ffmpeg.input(video_path, ss=frame_number/frame_rate)
                .output(frame_output_path, vframes=1, format='png', vcodec='png')
                .run(capture_stdout=True, capture_stderr=True)
            )

def main():
    parser = argparse.ArgumentParser(description="Extract frames from AV1 MP4 video files.")
    parser.add_argument("input_dir", type=str, help="Input directory containing video files")
    parser.add_argument("output_dir", type=str, help="Output directory for extracted images")
    parser.add_argument("num_frames", type=int, help="Number of frames to extract")
    parser.add_argument("mode", type=int, choices=[1, 2, 3], help="Frame selection mode: 1 - evenly divided, 2 - random, 3 - combined")
    args = parser.parse_args()

    extract_frames(args.input_dir, args.output_dir, args.num_frames, args.mode)

if __name__ == "__main__":
    main()

