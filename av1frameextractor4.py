import os
import subprocess
import argparse
import random
from PIL import Image
from blurhash import encode

import numpy as np
from blurhash import decode

def is_image_blurry(image_path, threshold=30):
    """
    Determines if an image is blurry using blurhash.

    Args:
        image_path: Path to the image file.
        threshold: Blurhash threshold value (lower is blurrier).

    Returns:
        True if image is blurry, False otherwise.
    """
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img_array = np.array(img)
            blurhash = encode(img_array)

            # Decode the blurhash (if needed) and extract the DC component
            decoded_components = decode(blurhash.decode() if isinstance(blurhash, bytes) else blurhash, 4, 3)
            dc_component = decoded_components[0][0]

            return dc_component < threshold
    except Exception as e:
        print(f"Error checking blurriness of {image_path}: {e}")
        return True  # Assume blurry on error

def process_video(video_path, output_dir, num_frames, limit_videos=None):
    """
    Processes a video file, extracting high-quality frame snapshots.

    Args:
        video_path: Path to the video file.
        output_dir: Output directory for saving images.
        num_frames: Number of evenly spaced and random frames to extract.
        limit_videos: Optional limit on the number of videos to process (not used in this function).
    """
    video_filename = os.path.basename(video_path)
    video_name, _ = os.path.splitext(video_filename)

    try:
        # Get video duration excluding the first and last minute
        probe_cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
            'default=noprint_wrappers=1:nokey=1', video_path
        ]
        duration_output = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT, text=True)
        total_duration = float(duration_output.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error getting duration of {video_path}: {e.output}")
        return

    valid_duration = max(0, total_duration - 120)

    # Evenly spaced frames
    interval = valid_duration / (num_frames + 1) if valid_duration > 0 else 0
    for i in range(1, num_frames + 1):
        timestamp = 60 + i * interval
        output_path = os.path.join(output_dir, f"{video_name}_even_{i}.png")
        extract_frame(video_path, output_path, timestamp)

    # Random frames
    if valid_duration >= 120:
        random_timestamps = random.sample(range(60, int(total_duration - 60)), num_frames)
        for i, timestamp in enumerate(random_timestamps):
            output_path = os.path.join(output_dir, f"{video_name}_random_{i+1}.png")
            extract_frame(video_path, output_path, timestamp)

def extract_frame(video_path, output_path, timestamp):
    """
    Extracts a single frame from the video at the specified timestamp, ensuring
    it's high quality and not blurry.

    Args:
        video_path: Path to the video file.
        output_path: Output path for saving the image.
        timestamp: Timestamp in seconds.
    """
    max_retries = 3
    retries = 0

    # Check if the file already exists and is non-blurry
    if os.path.exists(output_path) and not is_image_blurry(output_path):
        print(f"Skipping existing non-blurry frame at {timestamp}s: {output_path}")
        return

    while retries < max_retries:
        try:
            # Use hardware acceleration if available and select a keyframe for better quality
            cmd = [
                'ffmpeg', '-hwaccel', 'auto', '-ss', str(timestamp), '-i', video_path,
                '-frames:v', '1', '-q:v', '2', '-vf', 'select=eq(pict_type\,I)', output_path
            ]
            subprocess.check_call(cmd)

            if not is_image_blurry(output_path):
                break
            else:
                print(f"Retry: Blurry frame detected at {timestamp}s. Re-extracting...")
                retries += 1
        except subprocess.CalledProcessError as e:
            print(f"Error extracting frame from {video_path} at {timestamp}s: {e}")
            retries += 1

    if retries == max_retries:
        print(f"Failed to extract a non-blurry frame at {timestamp}s after {max_retries} retries.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="High-performance video frame snapshot extractor")
    parser.add_argument("input_dir", help="Input directory containing AV1 video files")
    parser.add_argument("output_dir", help="Output directory for saving images")
    parser.add_argument("num_frames", type=int, help="Number of frames to extract per video")
    parser.add_argument("-l", "--limit", type=int, help="Limit the number of videos to process")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.webm')
    video_files = [
        f for f in os.listdir(args.input_dir)
        if f.endswith(video_extensions) 
        # and any(keyword in f.lower() for keyword in ["av1", "aom", "libaom"])  # More flexible filtering (optional)
    ]

    if args.limit:
        video_files = video_files[:args.limit]

    for i, video_file in enumerate(video_files):
        video_path = os.path.join(args.input_dir, video_file)
        print(f"Processing video {i+1}/{len(video_files)}: {video_file}")
        process_video(video_path, args.output_dir, args.num_frames)
