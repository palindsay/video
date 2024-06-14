import os
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor

def process_video(input_file, output_directory, resolution, codec):
    """
    Converts a single video file with CUDA-accelerated ffmpeg.

    Parameters:
        input_file (str): The path to the input video file.
        output_directory (str): The directory where the converted video will be saved.
        resolution (int): The target resolution width for the converted video. Maintains aspect ratio.
        codec (str): The video codec to use for the converted video.
    """
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_filename = f"{base_name}_conv.mp4"
    output_filepath = os.path.join(output_directory, output_filename)

    ffmpeg_command = [
        'ffmpeg',
        '-hwaccel', 'cuda',
        '-i', input_file,
        # '-vf', f'scale=w={resolution}:h=-1:force_original_aspect_ratio=decrease',  # uncomment to set a resolution
        '-c:v', codec,
        '-c:a', 'aac',
        output_filepath
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Successfully converted {input_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting {input_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Batch video converter using CUDA-enabled ffmpeg.")
    parser.add_argument("input_dir", help="Path to the directory containing input videos.")
    parser.add_argument("output_dir", help="Path to the directory for converted videos.")
    parser.add_argument("-r", "--resolution", type=int, default=1920,
                        help="Target resolution width (maintains aspect ratio). Default: 1920")
    parser.add_argument("-c", "--codec", default='hevc_nvenc',
                        help="Video codec. Default: hevc_nvenc")
    args = parser.parse_args()

    for filename in os.listdir(args.input_dir):
            if filename.endswith('.webm'):
            input_filepath = os.path.join(args.input_dir, filename)
                # submit the task to the thread pool and continue with the next file without waiting for this one to finish
                executor.submit(process_video, input_filepath, args.output_dir, args.resolution, args.codec)


