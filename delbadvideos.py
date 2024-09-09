import os
import argparse
import ffmpeg

def is_hd_quality(width, height):
    return width >= 1280 and height >= 720

def is_long_enough(duration):
    return duration >= 480  # 8 minutes = 480 seconds

def is_valid_video(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None:
            return False
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        duration = float(probe['format']['duration'])
        return is_hd_quality(width, height) and is_long_enough(duration)
    except ffmpeg.Error:
        return False

def clean_videos(input_dir, dry_run=False):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v')):
                file_path = os.path.join(root, file)
                if not is_valid_video(file_path):
                    if dry_run:
                        print(f"Would delete: {file_path}")
                    else:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Clean video files based on quality and duration.")
    parser.add_argument("input_dir", help="Input directory containing video files")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without deleting files")
    args = parser.parse_args()

    clean_videos(args.input_dir, args.dry_run)

if __name__ == "__main__":
    main()
