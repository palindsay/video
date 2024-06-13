#!/usr/bin/env python
from __future__ import unicode_literals, print_function
import argparse
import ffmpeg
import glob
import os
import sys


def vid_info(in_filename):
    try:
        probe = ffmpeg.probe(in_filename)
    except ffmpeg.Error as e:
        print('Failed to process {} with Error: {}'.format(in_filename,e.stderr), file=sys.stderr)
        return

    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream is None:
        print('No video stream found', file=sys.stderr)
        return
    width = int(video_stream['width'])
    height = int(video_stream['height'])
    duration = 600
    try:
        duration = int(float(video_stream['duration']))
    except KeyError as e: 
        duration = 600
    # num_frames = int(video_stream['nb_frames'])
    print('{},{},{},{}'.format(in_filename,width,height,duration))
    # 1920 x 1080
    if duration < 600 or (width < 1920 and height < 1080):
        print('Removing {}'.format(in_filename))
        os.remove(in_filename)
    # print('num_frames: {}'.format(num_frames))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get video information')
    parser.add_argument('directory', help='Processing directory')
    args = parser.parse_args()

    # traverse root directory, and list directories as dirs and files as files            
    for root, dir_names, file_names in os.walk(args.directory):
        for f in file_names:
            thefile = os.path.join(root, f)
            if os.path.isfile(thefile):
                vid_info(thefile)
    print("All done.")
