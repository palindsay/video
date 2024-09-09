import os
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def process_file(file_info, keywords, dry_run, delete_if_found):
    filename, directory = file_info
    if filename.endswith('.txt'):
        base_name = os.path.splitext(filename)[0]
        txt_path = os.path.join(directory, filename)
        img_path = os.path.join(directory, base_name + '.png')
        
        # If .png doesn't exist, try .jpg
        if not os.path.exists(img_path):
            img_path = os.path.join(directory, base_name + '.jpg')
        
        # If neither .png nor .jpg exist, return None
        if not os.path.exists(img_path):
            return None
        
        with open(txt_path, 'r') as f:
            caption_words = set(word.strip().lower() for word in f.read().split(','))
        
        keyword_found = any(keyword.lower() in caption_words for keyword in keywords)
        should_delete = keyword_found if delete_if_found else not keyword_found
        
        if should_delete:
            if dry_run:
                return f"Would delete {txt_path} and {img_path}"
            else:
                os.remove(txt_path)
                os.remove(img_path)
                return f"Deleted {txt_path} and {img_path}"
    return None

def process_directory(directory, keywords, dry_run, delete_if_found):
    start_time = time.time()
    total_files = sum(1 for _ in os.listdir(directory) if _.endswith('.txt'))
    processed_files = 0
    deleted_files = 0

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        future_to_file = {executor.submit(process_file, (filename, directory), keywords, dry_run, delete_if_found): filename 
                          for filename in os.listdir(directory) if filename.endswith('.txt')}
        
        for future in as_completed(future_to_file):
            result = future.result()
            processed_files += 1
            
            if result:
                print(result)
                deleted_files += 1
            
            # Update progress
            progress = processed_files / total_files
            elapsed_time = time.time() - start_time
            files_per_second = processed_files / elapsed_time
            
            # Clear the line and print progress
            print(f"\rProgress: [{('=' * int(50 * progress)):50s}] {progress:.1%} "
                  f"({processed_files}/{total_files}) "
                  f"Files deleted: {deleted_files} "
                  f"Speed: {files_per_second:.2f} files/sec", end='', flush=True)

    print("\n")  # Move to next line after progress bar
    elapsed_time = time.time() - start_time
    print(f"Processing completed in {elapsed_time:.2f} seconds.")
    print(f"Total files processed: {processed_files}")
    print(f"Files {'that would be' if dry_run else ''} deleted: {deleted_files}")
    print(f"Average processing speed: {processed_files / elapsed_time:.2f} files/second")

def main():
    parser = argparse.ArgumentParser(description='Process image-caption pairs based on keywords.')
    parser.add_argument('directory', help='Directory containing image-caption pairs')
    parser.add_argument('keywords', nargs='+', help='Keywords to search for in captions')
    
    # Create mutually exclusive group for delete/keep mode
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--delete-if-found', action='store_true', 
                            help='Delete files if keywords are found in the caption')
    mode_group.add_argument('--delete-if-not-found', action='store_true', 
                            help='Delete files if keywords are not found in the caption')
    
    parser.add_argument('--dry-run', action='store_true', 
                        help='Perform a dry run without actually deleting files')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        sys.exit(1)
    
    print("Starting processing...")
    print(f"Dry run: {'Yes' if args.dry_run else 'No'}")
    if args.delete_if_found:
        print("Mode: Delete files when keywords are found")
    else:
        print("Mode: Delete files when keywords are not found")
    print(f"Keywords: {', '.join(args.keywords)}")
    print(f"Directory: {args.directory}")
    print("---")
    
    process_directory(args.directory, args.keywords, args.dry_run, args.delete_if_found)

if __name__ == "__main__":
    main()
 
