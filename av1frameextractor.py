#!/usr/bin/env python3
"""
Multi-format AV1 Frame Extractor

This script processes video files that may contain AV1 video in various container
formats, extracting high-quality frame snapshots both evenly spaced and randomly
across the video timeline.

Usage:
    python multi_format_av1_extractor.py input_dir output_dir num_snapshots [--limit LIMIT]

Dependencies:
    - FFmpeg (https://ffmpeg.org/)
    - Python 3.6+
    - ffmpeg-python (pip install ffmpeg-python)
    - Pillow (pip install Pillow)

Author: Claude
Date: September 4, 2024
"""

import argparse
import os
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ffmpeg
from PIL import Image

# List of common container formats that can host AV1 video
SUPPORTED_EXTENSIONS = ('.mp4', '.webm', '.mkv', '.avi', '.mov', '.ogg', '.ts', '.m4v')

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        print("Error: FFmpeg is not installed or not in the system PATH.")
        print("Please install FFmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)

    try:
        import ffmpeg
    except ImportError:
        print("Error: ffmpeg-python is not installed.")
        print("Please install it using: pip install ffmpeg-python")
        sys.exit(1)

    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow is not installed.")
        print("Please install it using: pip install Pillow")
        sys.exit(1)

def get_video_info(video_path):
    """Get video information using FFprobe."""
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        if video_stream is None:
            print(f"No video stream found in {video_path}")
            return None

        return {
            'duration': float(probe['format']['duration']),
            'codec': video_stream['codec_name'],
            'width': int(video_stream['width']),
            'height': int(video_stream['height'])
        }
    except ffmpeg.Error as e:
        print(f"Error probing video {video_path}: {e.stderr.decode()}")
        return None

def extract_frame(video_path, output_path, timestamp):
    """Extract a single frame from the video at the given timestamp."""
    try:
        (
            ffmpeg
            .input(video_path, ss=timestamp)
            .filter('select', 'gte(n,0)')
            .output(output_path, vframes=1, format='image2', vcodec='png')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True
    except ffmpeg.Error as e:
        print(f"Error extracting frame at {timestamp} from {video_path}: {e.stderr.decode()}")
        return False

def is_high_quality(image_path, min_width=640, min_height=480):
    """Check if the image meets the quality criteria."""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return width >= min_width and height >= min_height
    except Exception as e:
        print(f"Error checking image quality for {image_path}: {e}")
        return False

def process_video(video_path, output_dir, num_snapshots):
    """Process a single video file, extracting evenly spaced and random frames."""
    video_name = Path(video_path).stem
    video_info = get_video_info(video_path)
    
    if video_info is None:
        print(f"Skipping {video_path}: Unable to get video information")
        return

    if video_info['codec'].lower() != 'av1':
        print(f"Skipping {video_path}: Not an AV1 encoded video (codec: {video_info['codec']})")
        return

    duration = video_info['duration']
    if duration <= 120:  # Skip videos shorter than 2 minutes
        print(f"Skipping {video_path}: Too short (duration: {duration:.2f} seconds)")
        return

    print(f"Processing {video_path} (duration: {duration:.2f} seconds, resolution: {video_info['width']}x{video_info['height']})")

    # Exclude first and last minute
    start_time = 60
    end_time = duration - 60
    interval = (end_time - start_time) / (num_snapshots + 1)

    # Evenly spaced snapshots
    even_timestamps = [start_time + i * interval for i in range(1, num_snapshots + 1)]
    
    # Random snapshots
    random_timestamps = [random.uniform(start_time, end_time) for _ in range(num_snapshots)]

    for i, timestamp in enumerate(even_timestamps + random_timestamps):
        snapshot_type = "even" if i < num_snapshots else "random"
        output_path = os.path.join(output_dir, f"{video_name}_{snapshot_type}_{i % num_snapshots + 1}.png")
        
        if extract_frame(video_path, output_path, timestamp):
            if is_high_quality(output_path):
                print(f"Extracted {snapshot_type} frame {i % num_snapshots + 1} from {video_name}")
            else:
                os.remove(output_path)
                print(f"Discarded low-quality {snapshot_type} frame {i % num_snapshots + 1} from {video_name}")

def main():
    """Main function to process video files and extract frame snapshots."""
    parser = argparse.ArgumentParser(description="Extract high-quality frame snapshots from AV1 videos in various container formats.")
    parser.add_argument("input_dir", help="Input directory containing video files")
    parser.add_argument("output_dir", help="Output directory for extracted frame snapshots")
    parser.add_argument("num_snapshots", type=int, help="Number of snapshots to extract per video")
    parser.add_argument("--limit", type=int, help="Limit the number of videos to process")
    args = parser.parse_args()

    check_dependencies()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    video_files = [f for f in input_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS]
    if args.limit:
        video_files = video_files[:args.limit]

    print(f"Found {len(video_files)} potentially compatible video files to process")

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_video, str(video), str(output_dir), args.num_snapshots) for video in video_files]
        for future in futures:
            future.result()

    print("Frame extraction completed")

if __name__ == "__main__":
    main()
