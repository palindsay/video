#!/bin/bash

# Check for dependencies
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Please install it first."
    exit 1
fi

# Check for correct number of arguments
if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_directory> <output_directory>"
    exit 1
fi

input_dir="$1"
output_dir="$2"

mkdir -p "$output_dir"

for file in "$input_dir"/*.mp4; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        extension="${filename##*.}"
        output_file="${output_dir}/${filename%.*}_AV1.mp4"

	if ! [[ -f "$output_file" ]]; then
            # Encoding command using the AV1 NVENC encoder
	    echo "Converting: $file"
            ffmpeg -i "$file" -c:v av1_nvenc -cq:v 35 -c:a copy "$output_file"
	fi
    fi
done

echo "Conversion completed!" 
