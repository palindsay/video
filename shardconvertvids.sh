#!/bin/bash

# This script requires ffmpeg to be installed in order to convert video files.
# The script checks if ffmpeg is available, and exits with an error message if it's not.
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Please install it first."
    exit 1
fi

# The script expects two arguments: the input directory and a shard number (0-9).
# If these are not provided, the script prints a usage message and exits.
if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_directory> <shard 0-9>"
    exit 1
fi

# Store the input directory for later use.
input_dir="$1"

# Define a list of popular video extensions that the script supports.
extensions=("mp4" "avi" "mkv" "mov" "webm" "wmv")

# Loop through each file in the input directory.
for file in "$input_dir"/*; do
    # Ignore temporary files (files containing 'temp' in their name).
    if [[ "$file" == *temp* ]]; then
        continue
    fi

    # Extract the filename and prefix from the full path of the current file.
    thefilename=$(basename "$file")
    prefix="${thefilename%.*}"

    # Calculate the result of the modulus operation (prefix % 10) to determine if the file should be processed based on the shard number provided by the user.
    result="$(( $prefix % 10 ))"
    shard="$2"
    echo "File prefix: $prefix modulus: $result"

    # If the result does not match the shard number, skip to the next file in the loop.
    if [[ $result -ne $shard ]]; then
       continue
    fi

    # Check if the current file is a regular file (not a directory or special file).
    if [[ -f "$file" ]]; then
        # Extract the filename and extension from the full path of the current file.
        filename="${file%.*}"
        extension="${file##*.}"

        # Check if the extension of the current file is supported by the script.
        if [[ " ${extensions[*]} " =~ " ${extension} " ]]; then
            # Define a temporary file to store the converted output.
            temporary_file="${filename}_temp.mp4"

            # Check if the video stream of the current file is already AV1.
            codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$file")

            # If the video stream is not AV1, proceed with the conversion.
            if [[ "$codec" != "av1" ]]; then
		ffmpeg -i "$file" -y -threads 0 -c:v av1_nvenc -cq:v 35 -c:a copy "$temporary_file"
    
                # If the conversion was successful, replace the original file with the converted file.
		# Otherwise, append the filename to a list of bad files and skip to the next file in the loop.
		if [ $? -eq 0 ]; then
                    mv -f "$temporary_file" "$file"
                    echo "Converted: $file"
		else
                    echo "Error converting: $file"
                    echo "$file" >> badfiles.txt # Optional: Remove temporary file on error
		fi
            # If the video stream is already AV1, print a message and skip to the next file in the loop.
	    else
		echo "File is already AV1, skipping: $file"
            fi
        # If the extension of the current file is not supported, print a message and append the filename to a list of skipped files.
        else
            echo "Skipping unsupported format: $file"
            echo "$file" >> skippedfiles.txt 
        fi
    fi
done
echo "Conversion completed!"
