#!/usr/bin/env python3

import argparse
import os
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import laplace
from tqdm import tqdm

def install_dependencies():
    """Install required Python packages."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "tqdm", "pillow", "scipy"])

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: FFmpeg is not installed or not in the system PATH.")
        print("Please install FFmpeg and make sure it's accessible from the command line.")
        sys.exit(1)

def get_video_duration(video_path):
    """Get the duration of a video using FFprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout)

def extract_frame(video_path, output_path, timestamp):
    """Extract a single frame from the video at the given timestamp."""
    cmd = [
        "ffmpeg",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        "-filter:v", "scale=iw*sar:ih",
        str(output_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Frame extraction failed: {output_path} was not created")

def is_blurry(image_path, threshold=100, downscale_factor=2, edge_percent=0.1):
    """
    Check if an image is blurry using an improved Laplacian variance method.
    
    Args:
    image_path (str): Path to the image file.
    threshold (float): Laplacian variance threshold for blur detection.
    downscale_factor (int): Factor by which to downscale the image before processing.
    edge_percent (float): Percentage of highest edge values to consider.
    
    Returns:
    bool: True if the image is blurry, False otherwise.
    """
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale and downscale
            img_gray = img.convert('L')
            width, height = img_gray.size
            img_small = img_gray.resize((width // downscale_factor, height // downscale_factor))
            
            # Convert to numpy array
            img_array = np.array(img_small, dtype=np.float64)
            
            # Compute Laplacian
            laplacian = np.abs(laplace(img_array))
            
            # Focus on the strongest edges
            num_pixels = laplacian.size
            num_edge_pixels = int(num_pixels * edge_percent)
            top_edges = np.partition(laplacian.flatten(), -num_edge_pixels)[-num_edge_pixels:]
            
            # Compute variance of the strongest edges
            edge_variance = np.var(top_edges)
            
            return edge_variance < threshold
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return True  # Assume blurry if there's an error

def process_video(video_path, output_dir, num_frames, blur_threshold):
    """Process a single video, extracting frames and checking for blur."""
    video_name = video_path.stem
    try:
        duration = get_video_duration(video_path)
        
        if duration <= 120:  # Skip videos shorter than 2 minutes
            print(f"Skipping {video_name}: Duration too short ({duration:.2f} seconds)")
            return
        
        start_time = 60
        end_time = duration - 60
        interval = (end_time - start_time) / (num_frames + 1)
        
        extracted_frames = 0
        random_timestamps = random.sample(range(int(start_time), int(end_time)), num_frames)
        
        for i in range(num_frames * 2):
            if i < num_frames:
                timestamp = start_time + (i + 1) * interval
            else:
                timestamp = random_timestamps[i - num_frames]
            
            frame_name = f"{video_name}_frame_{i+1:03d}.png"
            frame_path = output_dir / frame_name
            
            try:
                extract_frame(video_path, frame_path, timestamp)
                if os.path.exists(frame_path):
                    if not is_blurry(frame_path, threshold=blur_threshold):
                        extracted_frames += 1
                    else:
                        os.remove(frame_path)
                        print(f"Removed blurry frame: {frame_name}")
                else:
                    print(f"Frame extraction failed: {frame_name}")
            except subprocess.CalledProcessError as e:
                print(f"Error extracting frame {i+1} from {video_name}: {str(e)}")
            except Exception as e:
                print(f"Unexpected error processing frame {i+1} from {video_name}: {str(e)}")
        
        print(f"Processed {video_name}: Extracted {extracted_frames} non-blurry frames")
    except Exception as e:
        print(f"Error processing video {video_name}: {str(e)}")

def main(input_dir, output_dir, num_frames, max_videos, blur_threshold):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.webm')
    video_files = [f for f in input_path.glob('*') if f.suffix.lower() in video_extensions]
    
    if max_videos:
        video_files = video_files[:max_videos]
    
    with ThreadPoolExecutor() as executor:
        list(tqdm(
            executor.map(lambda v: process_video(v, output_path, num_frames, blur_threshold), video_files),
            total=len(video_files),
            desc="Processing videos"
        ))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract high-quality frame snapshots from AV1 videos.")
    parser.add_argument("input_dir", help="Input directory containing video files")
    parser.add_argument("output_dir", help="Output directory for extracted frames")
    parser.add_argument("num_frames", type=int, help="Number of frames to extract per video")
    parser.add_argument("--max_videos", type=int, help="Maximum number of videos to process (optional)")
    parser.add_argument("--blur_threshold", type=float, default=100, help="Threshold for blur detection (default: 100)")
    args = parser.parse_args()
    
    print("Checking dependencies...")
    check_ffmpeg()
    install_dependencies()
    
    print(f"Processing videos from: {args.input_dir}")
    print(f"Saving frames to: {args.output_dir}")
    print(f"Extracting {args.num_frames} frames per video")
    print(f"Blur detection threshold: {args.blur_threshold}")
    if args.max_videos:
        print(f"Processing up to {args.max_videos} videos")
    
    main(args.input_dir, args.output_dir, args.num_frames, args.max_videos, args.blur_threshold)
    print("Processing complete!")
