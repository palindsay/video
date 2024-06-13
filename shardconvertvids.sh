#!/bin/bash

# Dependencies
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Please install it first."
    exit 1
fi

# Input Validation
if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_directory> <shard 0-9>"
    exit 1
fi

input_dir="$1"

# Popular video extensions
extensions=("mp4" "avi" "mkv" "mov" "webm" "wmv")

# Conversion Loop
for file in "$input_dir"/*; do
    if [[ "$file" == *temp* ]]; then
        continue
    fi
    thefilename=$(basename "$file")
    prefix="${thefilename%.*}"
    result="$(( $prefix % 10 ))"
    shard="$2"
    echo "File prefix: $prefix modulus: $result"
    if [[ $result -ne $shard ]]; then
       continue
    fi
    if [[ -f "$file" ]]; then
        filename="${file%.*}"
        extension="${file##*.}"

        # Check if the file has a supported extension
        if [[ " ${extensions[*]} " =~ " ${extension} " ]]; then
            temporary_file="${filename}_temp.mp4"

	    # Check if the video stream is already AV1
            codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$file")

            if [[ "$codec" != "av1" ]]; then
		# Proceed with conversion (as before)
		temporary_file="${filename}_temp.mp4"
		ffmpeg -i "$file" -y -threads 0 -c:v av1_nvenc -cq:v 35 -c:a copy "$temporary_file"
    
		if [ $? -eq 0 ]; then
                    mv -f "$temporary_file" "$file"
                    echo "Converted: $file"
		else
                    echo "Error converting: $file"
                    echo "$file" >> badfiles.txt # Optional: Remove temporary file on error 
		fi
	    else
		echo "File is already AV1, skipping: $file"
            fi
        else
            echo "Skipping unsupported format: $file"
            echo "$file" >> skippedfiles.txt 
        fi
    fi
done
echo "Conversion completed!"
