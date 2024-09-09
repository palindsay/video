import argparse
import os
import random
from pathlib import Path
import subprocess
import json

import ffmpeg
import numpy as np
from tqdm import tqdm

def get_video_info(video_path):
    probe = ffmpeg.probe(video_path)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    return {
        'width': int(video_info['width']),
        'height': int(video_info['height']),
        'num_frames': int(video_info['nb_frames']),
        'duration': float(video_info['duration']),
        'fps': eval(video_info['avg_frame_rate'])
    }

def extract_frame(video_path, output_path, timestamp):
    try:
        (
            ffmpeg
            .input(video_path, ss=timestamp)
            .filter('scale', 'iw', 'ih')
            .output(output_path, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(f"Error extracting frame at {timestamp}: {e.stderr.decode()}")

def extract_frames(video_path, output_dir, num_frames, start_frame=200):
    video_info = get_video_info(video_path)
    total_frames = video_info['num_frames']
    fps = video_info['fps']
    duration = video_info['duration']
    
    if total_frames <= start_frame:
        print(f"Warning: Video {video_path} has fewer frames than the start_frame. Skipping.")
        return

    start_time = start_frame / fps

    # Calculate frame indices for even distribution
    even_timestamps = np.linspace(start_time, duration, num_frames)
    
    # Calculate frame indices for random distribution
    random_timestamps = sorted(np.random.uniform(start_time, duration, num_frames))
    
    all_timestamps = sorted(set(even_timestamps) | set(random_timestamps))
    
    video_name = Path(video_path).stem
    for i, timestamp in enumerate(tqdm(all_timestamps, desc=f"Processing {video_name}")):
        frame_type = "even" if timestamp in even_timestamps else "random"
        output_path = os.path.join(output_dir, f"{video_name}_{frame_type}_{i:04d}.png")
        extract_frame(video_path, output_path, timestamp)

def process_directory(input_dir, output_dir, num_frames):
    video_extensions = ['.mp4']
    for root, _, files in os.walk(input_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_path = os.path.join(root, file)
                extract_frames(video_path, output_dir, num_frames)

def main():
    parser = argparse.ArgumentParser(description="Extract high-quality frames from AV1 MP4 videos.")
    parser.add_argument("input_dir", help="Input directory containing video files")
    parser.add_argument("output_dir", help="Output directory for extracted frames")
    parser.add_argument("num_frames", type=int, help="Number of frames to extract (per method)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    process_directory(args.input_dir, args.output_dir, args.num_frames)

if __name__ == "__main__":
    main()

