import av
import numpy as np
import os
import argparse
from PIL import Image

def extract_n_frames(video_path, n_frames, output_dir):
    with av.open(video_path) as container:
        stream = container.streams.video[0]
        total_frames = stream.frames
        step = max(total_frames // n_frames, 1)
        
        # Get video dimensions
        width = stream.width
        height = stream.height
        
        os.makedirs(output_dir, exist_ok=True)
        
        for frame_num, frame in enumerate(container.decode(stream)):
            if frame_num % step == 0:
                img = frame.to_image()
                
                # Maintain aspect ratio
                img.thumbnail((width, height), Image.LANCZOS)
                
                # Save the image
                output_path = os.path.join(output_dir, f"frame_{frame_num:04d}.png")
                img.save(output_path)
                
                print(f"Saved frame {frame_num} to {output_path}")
            
            if frame_num // step >= n_frames:
                break

def main():
    parser = argparse.ArgumentParser(description="Extract frames from AV1 video files.")
    parser.add_argument("input_dir", help="Directory containing input video files")
    parser.add_argument("output_dir", help="Directory to save extracted frames")
    parser.add_argument("n_frames", type=int, help="Number of frames to extract per video")
    args = parser.parse_args()

    for filename in os.listdir(args.input_dir):
        if filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):  # Add more extensions if needed
            video_path = os.path.join(args.input_dir, filename)
            video_output_dir = os.path.join(args.output_dir, os.path.splitext(filename)[0])
            print(f"Processing {filename}...")
            extract_n_frames(video_path, args.n_frames, video_output_dir)

if __name__ == "__main__":
    main()

