import os
import argparse
import ffmpeg

def is_hd_quality(width, height):
    return width >= 720 or height >= 720

def is_long_enough(duration):
    try:
        return float(duration) >= 300  # 5 minutes = 300 seconds
    except (ValueError, TypeError):
        return False

def get_video_info(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None:
            return None
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        duration = float(probe['format']['duration'])
        return width, height, duration
    except (ffmpeg.Error, KeyError, ValueError, TypeError):
        return None

def clean_videos(input_dir, dry_run=False):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v')):
                file_path = os.path.join(root, file)
                video_info = get_video_info(file_path)
                
                if video_info is None:
                    reason = "File is corrupted or unreadable"
                    resolution = "N/A"
                    duration = "N/A"
                else:
                    width, height, duration = video_info
                    resolution = f"{width}x{height}"
                    duration_str = f"{duration:.2f} seconds"
                    
                    if not is_hd_quality(width, height):
                        reason = "Not HD quality (below 720x720)"
                    elif not is_long_enough(duration):
                        reason = "Duration less than 8 minutes"
                    else:
                        continue  # File meets all criteria, skip to next file
                
                if dry_run:
                    print(f"Would delete: {file_path}")
                else:
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except OSError as e:
                        print(f"Error deleting {file_path}: {e}")
                
                print(f"  Resolution: {resolution}")
                print(f"  Duration: {duration_str if 'duration_str' in locals() else duration}")
                print(f"  Reason: {reason}")
                print()

def main():
    parser = argparse.ArgumentParser(description="Clean video files based on quality and duration.")
    parser.add_argument("input_dir", help="Input directory containing video files")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without deleting files")
    args = parser.parse_args()

    clean_videos(args.input_dir, args.dry_run)

if __name__ == "__main__":
    main()

