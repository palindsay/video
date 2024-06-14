# Import necessary libraries
import os
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_video(input_file, output_directory, resolution, codec):
    """
    Convert a single video file with CUDA-accelerated ffmpeg.

    :param input_file: Path to the input video file
    :param output_directory: Directory where converted videos will be saved
    :param resolution: Target width for scaling (height is automatically adjusted)
    :param codec: Video codec to use for conversion
    :return: String indicating success or failure of the conversion process
    """
    # Extracts the base name and extension of the input file
    base_name, ext = os.path.splitext(os.path.basename(input_file))
    output_filename = f"{base_name}_{resolution}{ext}"  # Keeps the original format
    output_filepath = os.path.join(output_directory, output_filename)

    # Constructs the command to run FFmpeg with CUDA-accelerated encoding and scaling options
    ffmpeg_command = [
        'ffmpeg',  # FFmpeg executable
        '-hwaccel', 'cuda',  # Hardware acceleration using CUDA
        '-i', input_file,  # Input file path
        '-vf', f'scale=w={resolution}:h=-1:force_original_aspect_ratio=decrease',  # Scaling options (only width is specified)
        '-c:v', codec,  # Video codec to use for conversion
        output_filepath  # Output file path
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)  # Executes the FFmpeg command and checks for errors
        return f"Successfully converted {input_file}"
    except subprocess.CalledProcessError as e:
        return f"Error converting {input_file}: {e}"

def main():
    """
    Main function to handle command-line arguments, process videos and manage threads for concurrent conversion.
    """
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Batch video converter using CUDA-enabled ffmpeg.")
    parser.add_argument("input_dir", help="Path to the directory containing input videos.")
    parser.add_argument("output_dir", help="Path to the directory for converted videos.")
    parser.add_argument("-r", "--resolution", type=int, default=1920,
                        help="Target resolution width (maintains aspect ratio). Default: 1920")
    parser.add_argument("-c", "--codec", default='h264_nvenc',
                        help="Video codec. Default: h264_nvenc")
    args = parser.parse_args()

    # List of video files to process (filtered by extension)
    videos_to_process = [os.path.join(args.input_dir, filename) for filename in os.listdir(args.input_dir)
                         if filename.endswith(('.mp4', '.mov', '.avi', '.webm'))]

    # Uses threading to process videos concurrently and prints the results as they complete
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_video, video, args.output_dir, args.resolution, args.codec) for video in videos_to_process}
        for future in as_completed(futures):
            print(future.result())  # Prints the result of each completed thread
if __name__ == "__main__":
    main()  # Runs the main function if the script is executed directly
