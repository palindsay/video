import argparse
import os
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
import ffmpeg

def get_video_duration(input_file):
    probe = ffmpeg.probe(input_file)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    return float(video_info['duration'])

def extract_frame(input_file, output_file, timestamp):
    (
        ffmpeg
        .input(input_file, ss=timestamp)
        .filter('scale', 'iw*2', 'ih*2')  # Upscale by 2x for higher quality
        .output(output_file, vframes=1, format='png', lossless=True)
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

def process_video(input_file, output_dir, num_frames, mode):
    video_name = os.path.splitext(os.path.basename(input_file))[0]
    duration = get_video_duration(input_file)
    
    # Ignore the first 100 frames (assuming 30 fps)
    start_time = 100 / 30

    if mode == 'evenly':
        interval = (duration - start_time) / num_frames
        timestamps = [start_time + i * interval for i in range(num_frames)]
    elif mode == 'random':
        timestamps = [random.uniform(start_time, duration) for _ in range(num_frames)]
    
    for i, timestamp in enumerate(timestamps):
        output_file = os.path.join(output_dir, f"{video_name}_frame_{i:04d}.png")
        extract_frame(input_file, output_file, timestamp)

def main(input_dir, output_dir, num_frames, mode):
    os.makedirs(output_dir, exist_ok=True)
    video_files = [f for f in os.listdir(input_dir) if f.endswith('.mp4')]
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for video_file in video_files:
            input_file = os.path.join(input_dir, video_file)
            futures.append(executor.submit(process_video, input_file, output_dir, num_frames, mode))
        
        for future in futures:
            future.result()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract high-quality frames from AV1 MP4 videos.")
    parser.add_argument("input_dir", help="Input directory containing video files")
    parser.add_argument("output_dir", help="Output directory for extracted frames")
    parser.add_argument("num_frames", type=int, help="Number of frames to extract per video")
    parser.add_argument("mode", choices=['evenly', 'random'], help="Frame selection mode")
    
    args = parser.parse_args()
    main(args.input_dir, args.output_dir, args.num_frames, args.mode)
