import os
import sys
import re
import argparse
from typing import List, Set

def split_fields(line: str) -> List[str]:
    fields = []
    current_field = []
    in_quotes = False
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            fields.append(''.join(current_field).strip())
            current_field = []
        else:
            current_field.append(char)
    fields.append(''.join(current_field).strip())
    return fields

def clean_field(field: str) -> str:
    # Remove special characters except spaces, keep only alphanumeric and spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', field)
    # Remove extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def break_out_phrases(field: str, phrases: List[str]) -> List[str]:
    result = [field]
    for phrase in phrases:
        new_result = []
        for item in result:
            parts = item.split(phrase)
            for i, part in enumerate(parts):
                if part:
                    new_result.append(part.strip())
                if i < len(parts) - 1:
                    new_result.append(phrase.strip())
        result = new_result
    return [item for item in result if item]

def delete_phrases(field: str, phrases_to_delete: List[str]) -> str:
    for phrase in phrases_to_delete:
        field = field.replace(phrase, '')
    return re.sub(r'\s+', ' ', field).strip()

def clean_caption_file(file_path: str, phrases: List[str], phrases_to_delete: List[str], dry_run: bool = False) -> None:
    with open(file_path, 'r') as file:
        content = file.read().strip()

    # Split content into lines
    lines = content.split('\n')

    # Clean up each line
    cleaned_lines = []
    for line in lines:
        # First, split the line into fields
        fields = split_fields(line)

        # Clean each field and delete specified phrases
        cleaned_fields = [delete_phrases(clean_field(field), phrases_to_delete) for field in fields]

        # Break out phrases for each field
        broken_fields = []
        for field in cleaned_fields:
            broken_fields.extend(break_out_phrases(field, phrases))

        # Remove duplicates while preserving order
        unique_fields: List[str] = []
        seen: Set[str] = set()
        for field in broken_fields:
            if field.lower() not in seen and field:  # Ensure field is not empty
                seen.add(field.lower())
                unique_fields.append(field)

        cleaned_line = ', '.join(unique_fields)
        cleaned_lines.append(cleaned_line)

    # Join cleaned lines
    cleaned_content = '\n'.join(cleaned_lines)

    if dry_run:
        print(f"Would clean file: {file_path}")
        print("Original content:")
        print(content)
        print("\nCleaned content:")
        print(cleaned_content)
    else:
        with open(file_path, 'w') as file:
            file.write(cleaned_content)
        print(f"Cleaned file: {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Clean up caption files in a directory.")
    parser.add_argument("directory", help="Directory containing caption files")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files")
    parser.add_argument("--phrases", nargs='+', help="Phrases to break out into separate fields")
    parser.add_argument("--delete-phrases", nargs='+', help="Phrases to delete from fields")
    args = parser.parse_args()

    directory = args.directory
    dry_run = args.dry_run
    phrases = args.phrases or []
    phrases_to_delete = args.delete_phrases or []

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            clean_caption_file(file_path, phrases, phrases_to_delete, dry_run)

if __name__ == "__main__":
    main()
