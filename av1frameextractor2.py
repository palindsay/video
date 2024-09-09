import os
import random
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageFilter
from math import floor
from pathlib import Path

# Function to check if an image is blurry using Laplacian variance
def is_blurry(image_path, threshold=100.0):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
    return laplacian_var < threshold

# Function to extract frames from video using ffmpeg
def extract_frames(video_path, timestamps, output_dir):
    for i, timestamp in enumerate(timestamps):
        output_file = os.path.join(output_dir, f"{Path(video_path).stem}_frame_{i + 1}.png")
        command = [
            'ffmpeg', '-ss', str(timestamp), '-i', video_path, '-vf', 'scale=-1:-1',
            '-vframes', '1', '-q:v', '2', output_file
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if is_blurry(output_file):
            os.remove(output_file)  # Remove blurry images

# Main video processing function
def process_videos(input_dir, output_dir, num_frames, limit_videos=None):
    video_extensions = ['.mp4', '.mkv', '.webm', '.mov', '.avi']
    videos = [f for f in os.listdir(input_dir) if f.endswith(tuple(video_extensions))]
    
    if limit_videos:
        videos = videos[:limit_videos]

    for video in videos:
        video_path = os.path.join(input_dir, video)
        output_subdir = os.path.join(output_dir, Path(video).stem)
        os.makedirs(output_subdir, exist_ok=True)

        # Get video duration using ffprobe
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 
             'default=noprint_wrappers=1:nokey=1', video_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        duration = float(result.stdout)

        # Exclude the first and last minute
        valid_duration = duration - 120
        if valid_duration <= 0:
            print(f"Skipping {video}, too short.")
            continue

        # Evenly spaced frames
        even_timestamps = np.linspace(60, duration - 60, num_frames)

        # Random frames
        random_timestamps = sorted(random.sample(range(60, floor(duration - 60)), num_frames))

        # Extract frames
        extract_frames(video_path, even_timestamps, output_subdir)
        extract_frames(video_path, random_timestamps, output_subdir)

        print(f"Processed {video} and saved frames to {output_subdir}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract high-quality frames from AV1 video files.")
    parser.add_argument("input_dir", type=str, help="Directory containing input AV1 video files.")
    parser.add_argument("output_dir", type=str, help="Directory to save the extracted frames.")
    parser.add_argument("-n", "--num_frames", type=int, default=5, help="Number of frames to extract.")
    parser.add_argument("-l", "--limit", type=int, help="Limit the number of videos to process.")
    
    args = parser.parse_args()

    process_videos(args.input_dir, args.output_dir, args.num_frames, args.limit)
