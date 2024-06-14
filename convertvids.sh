#!/bin/bash

# Dependencies: This section of the script checks if ffmpeg, which is a command-line tool used to manipulate and convert media files, is installed on the system. If not, it prints an error message and exits the script with a non-zero status code, indicating failure.
command -v ffmpeg >/dev/null 2>&1 || { echo "Error: ffmpeg is not installed." >&2; exit 1; }

# Input Validation: This section checks if the user has provided exactly one argument to the script (the input directory). If not, it prints a usage message and exits the script with a non-zero status code.
if (( $# != 1 )); then
    echo "Usage: $0 <input_directory>"
    exit 1
fi

# Store the input directory provided by the user in a variable for easier use throughout the script.
input_dir="$1"

# Define an array of popular video extensions that are supported for conversion using ffmpeg.
extensions=("mp4" "avi" "mkv" "mov" "webm" "wmv")

# Conversion Loop: This section loops over all files in the input directory and checks if their extension is present in the supported extensions array. If not, it prints a message indicating that the file format is unsupported and skips to the next iteration of the loop without processing the file.
for file in "$input_dir"/*; do
    filename="${file%.*}"  # Extract the filename from the full path of the file
    extension="${file##*.}"  # Extract the extension from the full path of the file
    if ! [[ " ${extensions[*]} " =~ " ${extension} " ]]; then
            echo "Skipping unsupported format: $file"
        echo "$file" >> skippedfiles.txt  # Append the name of the skipped file to a text file for later reference
        continue
    fi

    # Additional processing code would go here for supported files (not provided in the original script)
done

# Print a message indicating that the conversion process has completed successfully.
echo "Conversion completed!"
