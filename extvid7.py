import argparse
import os
import random
import subprocess
import json
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_info(video_path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        data = json.loads(result.stdout)
        video_stream = next(s for s in data['streams'] if s['codec_type'] == 'video')
        return {
            'duration': float(data['format']['duration']),
            'nb_frames': int(video_stream.get('nb_frames', 0)),
            'fps': eval(video_stream['avg_frame_rate']),
            'width': int(video_stream['width']),
            'height': int(video_stream['height'])
        }
    except Exception as e:
        logging.error(f"Error getting video info for {video_path}: {e}")
        return None

def extract_frames(video_path, output_dir, num_frames, mode):
    video_info = get_video_info(video_path)
    if not video_info:
        logging.error(f"Failed to get video info for {video_path}")
        return

    duration = video_info['duration']
    fps = video_info['fps']

    # Skip the first 100 frames
    start_time = 100 / fps
    if duration <= start_time:
        logging.info(f"Skipping {os.path.basename(video_path)}: Not enough frames")
        return

    if mode in [1, 3]:
        interval = (duration - start_time) / num_frames
    
    timestamps_to_extract = []
    
    if mode == 1:  # Evenly divided
        timestamps_to_extract = [start_time + i * interval for i in range(num_frames)]
    elif mode == 2:  # Random
        timestamps_to_extract = [random.uniform(start_time, duration) for _ in range(num_frames)]
    elif mode == 3:  # Combined
        even_timestamps = [start_time + i * interval * 2 for i in range(num_frames // 2)]
        random_timestamps = [random.uniform(start_time, duration) for _ in range(num_frames - len(even_timestamps))]
        timestamps_to_extract = sorted(even_timestamps + random_timestamps)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Construct FFmpeg command to extract all frames at once
    select_expr = '+'.join([f"eq(n,{int(t*fps)})" for t in timestamps_to_extract])
    output_pattern = os.path.join(output_dir, f"{base_name}_frame_%03d.jpg")
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f"select='{select_expr}',scale='iw:ih'",
        '-vsync', '0',
        '-q:v', '1',
        '-f', 'image2',
        output_pattern
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        logging.info(f"Successfully processed {video_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {video_path}: {e.stderr.decode()}")
    except subprocess.TimeoutExpired:
        logging.error(f"Timeout while processing {video_path}")

def process_video(args):
    video_file, input_dir, output_dir, num_frames, mode = args
    video_path = os.path.join(input_dir, video_file)
    try:
        extract_frames(video_path, output_dir, num_frames, mode)
        return video_file
    except Exception as e:
        logging.error(f"Error processing {video_file}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Extract frames from AV1 MP4 videos")
    parser.add_argument("input_dir", help="Input directory containing MP4 files")
    parser.add_argument("output_dir", help="Output directory for extracted frames")
    parser.add_argument("num_frames", type=int, help="Number of frames to extract per video")
    parser.add_argument("mode", type=int, choices=[1, 2, 3], help="1: Evenly divided, 2: Random, 3: Combined")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Number of worker processes")
    args = parser.parse_args()

    logging.info(f"Starting video frame extraction with {args.workers} workers")
    os.makedirs(args.output_dir, exist_ok=True)
    video_files = [f for f in os.listdir(args.input_dir) if f.endswith('.mp4')]
    logging.info(f"Found {len(video_files)} MP4 files to process")

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_video, (video_file, args.input_dir, args.output_dir, args.num_frames, args.mode)) for video_file in video_files]
        
        for future in tqdm(as_completed(futures), total=len(video_files), desc="Processing videos"):
            result = future.result()
            if result:
                logging.info(f"Completed processing {result}")
            else:
                logging.warning("A video failed to process")

    logging.info("Video frame extraction completed")

if __name__ == "__main__":
    main()

