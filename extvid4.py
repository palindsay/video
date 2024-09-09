import argparse
import os
import random
import subprocess
import json
from tqdm import tqdm

def get_video_info(video_path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    video_stream = next(s for s in data['streams'] if s['codec_type'] == 'video')
    return {
        'duration': float(data['format']['duration']),
        'nb_frames': int(video_stream['nb_frames']),
        'fps': eval(video_stream['avg_frame_rate'])
    }

def extract_frame(video_path, output_path, timestamp):
    cmd = [
        'ffmpeg',
        '-ss', str(timestamp),
        '-i', video_path,
        '-vframes', '1',
        '-q:v', '1',  # Highest quality for JPEG
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_frames(input_dir, output_dir, num_frames, mode):
    os.makedirs(output_dir, exist_ok=True)
    video_files = [f for f in os.listdir(input_dir) if f.endswith('.mp4')]

    for video_file in video_files:
        video_path = os.path.join(input_dir, video_file)
        video_info = get_video_info(video_path)
        
        total_frames = video_info['nb_frames']
        fps = video_info['fps']
        duration = video_info['duration']

        # Skip the first 100 frames
        start_time = 100 / fps
        if duration <= start_time:
            print(f"Skipping {video_file}: Not enough frames")
            continue

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

        base_name = os.path.splitext(video_file)[0]
        
        for i, timestamp in enumerate(tqdm(timestamps_to_extract, desc=f"Processing {video_file}")):
            output_path = os.path.join(output_dir, f"{base_name}_frame_{i+1:04d}.jpg")
            extract_frame(video_path, output_path, timestamp)

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

