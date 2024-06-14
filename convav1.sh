#!/bin/bash

# The script starts by checking if ffmpeg, a command-line tool for handling multimedia data,
# is installed in the system. If it's not found, an error message is printed and the script exits with status 1.
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install it first and try again."
    exit 1
fi

# The usage function is defined to display a help message that shows how to use the script.
usage() {
    echo "Usage: $0 <input_directory> <output_directory>"
}

# The script expects two arguments, which are the input and output directories for video conversion.
# If these arguments are not provided, the usage function is called and the script exits.
if [ "$#" -ne 2 ]; then
    usage
    exit 1
fi

# Convert the input and output directory paths to absolute paths using realpath command.
input_dir=$(realpath "$1")
output_dir=$(realpath "$2")

# Check if the input directory exists. If it doesn't, an error message is printed and the script exits with status 1.
if [[ ! -d "$input_dir" ]]; then
    echo "Error: Input directory does not exist."
    exit 1
fi

# Create the output directory if it doesn't already exist. If creation fails, an error message is printed and the script exits with status 1.
mkdir -p "$output_dir" || {
    echo "Error: Failed to create output directory."
    exit 1
}

# The find command is used to locate all mp4 files in the input directory, even if they have spaces or special characters in their names.
find "$input_dir" -type f -name '*.mp4' | while IFS= read -r file; do
    # Extract the filename from each found file path.
    filename=$(basename "$file")
    # Generate output filename by replacing '.mp4' extension with '_AV1'.
    output_file="${output_dir}/${filename%.mp4}_AV1.mp4"

    # Check if an output file already exists for the current input file.
    # If it doesn't, print a conversion message and run ffmpeg command to convert the input video to AV1 format with a constant quality of 35 and copy the audio stream without re-encoding.
    # If it does exist, print a skipping message as no conversion is needed for this file.
    if [[ ! -f "$output_file" ]]; then
        echo "Converting: $file"
        ffmpeg -hide_banner -y -i "$file" -c:v av1_nvenc -cq:v 35 -c:a copy "$output_file"
    else
        echo "Skipping: $file (already converted)"
    fi
done

# After the loop finishes processing all input files, print a completion message.
echo "Conversion completed!"
