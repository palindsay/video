import subprocess
import json
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_video_duration(input_file):
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        input_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])

def extract_frame(input_file, output_file, timestamp):
    cmd = [
        'ffmpeg',
        '-ss', str(timestamp),
        '-i', input_file,
        '-vf', 'scale=in_range=full:out_range=full',
        '-frames:v', '1',
        '-c:v', 'png',
        '-pix_fmt', 'rgb48be',
        '-compression_level', '0',
        '-y',
        output_file
    ]
    subprocess.run(cmd, check=True)

def process_video(input_file, output_dir, num_snapshots=20):
    video_name = os.path.splitext(os.path.basename(input_file))[0]
    video_output_dir = os.path.join(output_dir, video_name)
    
    if not os.path.exists(video_output_dir):
        os.makedirs(video_output_dir)

    duration = get_video_duration(input_file)
    interval = duration / (num_snapshots + 1)

    timestamps = [interval * (i + 1) for i in range(num_snapshots)]

    with ThreadPoolExecutor() as executor:
        futures = []
        for i, timestamp in enumerate(timestamps):
            output_file = os.path.join(video_output_dir, f'snapshot_{i:02d}.png')
            future = executor.submit(extract_frame, input_file, output_file, timestamp)
            futures.append(future)

        for future in as_completed(futures):
            future.result()

def process_directory(input_dir, output_dir, num_snapshots=20):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    video_extensions = ['.mp4', '.mov', '.avi', '.mkv']  # Add more if needed
    
    for filename in os.listdir(input_dir):
        if any(filename.lower().endswith(ext) for ext in video_extensions):
            input_file = os.path.join(input_dir, filename)
            print(f"Processing {filename}...")
            process_video(input_file, output_dir, num_snapshots)
            print(f"Finished processing {filename}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate snapshots from AV1 MP4 videos")
    parser.add_argument("input_dir", help="Directory containing input video files")
    parser.add_argument("output_dir", help="Directory to save output snapshots")
    parser.add_argument("--num_snapshots", type=int, default=20, help="Number of snapshots to generate per video (default: 20)")
    
    args = parser.parse_args()

    process_directory(args.input_dir, args.output_dir, args.num_snapshots)
