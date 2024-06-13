import os
import subprocess
import argparse

def process_video(input_file, output_directory, resolution, codec):
    """Converts a single video file with CUDA-accelerated ffmpeg."""

    output_filename = os.path.splitext(os.path.basename(input_file))[0] + f"_conv.mp4"
    output_filepath = os.path.join(output_directory, output_filename)

    ffmpeg_command = [
        'ffmpeg',
        '-hwaccel', 'cuda',
        '-i', input_file, 
    #    '-vf', f'scale=w={resolution}:h={resolution}:force_original_aspect_ratio=decrease',
        '-c:v', codec,
        '-c:a', 'aac',
        output_filepath
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Successfully converted {input_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting {input_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch video converter using CUDA-enabled ffmpeg.")
    parser.add_argument("input_dir", help="Path to the directory containing input videos.")
    parser.add_argument("output_dir", help="Path to the directory for converted videos.")
    parser.add_argument("-r", "--resolution", type=int, default=1920,
                        help="Target resolution width (maintains aspect ratio). Default: 1920")
    parser.add_argument("-c", "--codec", default='hevc_nvenc', 
                        help="Video codec. Default: hevc_nvenc")
    args = parser.parse_args()

    for filename in os.listdir(args.input_dir):
        if filename.endswith(('.webm')):  
            input_filepath = os.path.join(args.input_dir, filename)
            process_video(input_filepath, args.output_dir, args.resolution, args.codec)
