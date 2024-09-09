import os
import argparse
from collections import Counter
import multiprocessing as mp
import itertools

def process_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            return [attr.strip() for attr in content.split(',')]
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return []

def process_files_chunk(chunk):
    local_counter = Counter()
    for file_path in chunk:
        attributes = process_file(file_path)
        local_counter.update(attributes)
    return local_counter

def process_caption_files(directory):
    file_paths = []
    for root, _, files in os.walk(directory):
        file_paths.extend(os.path.join(root, file) for file in files if file.endswith(".txt"))
    
    num_cores = mp.cpu_count()
    chunk_size = max(1, len(file_paths) // (num_cores * 4))  # Adjust chunk size based on number of files
    
    with mp.Pool(processes=num_cores) as pool:
        results = pool.map(process_files_chunk, (file_paths[i:i+chunk_size] for i in range(0, len(file_paths), chunk_size)))
    
    return sum(results, Counter())

def generate_report(attribute_counter):
    total_attributes = sum(attribute_counter.values())
    report = "Attribute Popularity Report\n"
    report += "==========================\n\n"
    report += f"Total attributes: {total_attributes}\n"
    report += f"Unique attributes: {len(attribute_counter)}\n\n"
    report += "Attributes from most popular to least popular:\n"
    for attr, count in attribute_counter.most_common():
        percentage = (count / total_attributes) * 100
        report += f"{attr}: {count} ({percentage:.2f}%)\n"
    return report

def main():
    parser = argparse.ArgumentParser(description="Process caption files and generate an attribute popularity report.")
    parser.add_argument("directory", help="Directory containing caption files")
    parser.add_argument("-o", "--output", help="Output file for the report (optional)")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: The provided path '{args.directory}' is not a valid directory.")
        return

    print("Processing files...")
    attribute_counter = process_caption_files(args.directory)
    
    print("Generating report...")
    report = generate_report(attribute_counter)

    print("\nReport:")
    print(report)

    if args.output:
        with open(args.output, 'w') as file:
            file.write(report)
        print(f"Report saved to {args.output}")

if __name__ == "__main__":
    main()
