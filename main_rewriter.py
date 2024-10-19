import json
import logging
import argparse
import os
import time
from blog_rewriter import rewrite_blog_posts
from config_rewriter import (
    INPUT_FILE, OUTPUT_FILE, CHECK_INTERVAL,
    check_file_exists, validate_json_file, ensure_directory_exists
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_input_file(file_path, blogs, processed_indices):
    updated_blogs = [blog for i, blog in enumerate(blogs) if i not in processed_indices]
    try:
        ensure_directory_exists(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_blogs, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully updated input file: {file_path}")
        logging.info(f"Removed {len(processed_indices)} processed blog posts from the input file.")
    except OSError as e:
        logging.error(f"Error updating input file {file_path}: {str(e)}")
        raise

def process_blogs(input_file, output_file):
    try:
        # Check input file
        check_file_exists(input_file)
        validate_json_file(input_file)

        # Read input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            blogs = json.load(f)

        if not blogs:
            logging.info("No new blog posts to process.")
            return

        # Rewrite blog posts
        rewritten_blogs, processed_indices = rewrite_blog_posts(blogs)

        # Ensure output directory exists
        ensure_directory_exists(output_file)

        # Append to output JSON file with UTF-8 encoding and ensure_ascii=False
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r+', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_data.extend(rewritten_blogs)
                    f.seek(0)
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
                    f.truncate()
            except json.JSONDecodeError:
                logging.error(f"Error parsing existing output file '{output_file}'. Creating a new file.")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(rewritten_blogs, f, indent=2, ensure_ascii=False)
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rewritten_blogs, f, indent=2, ensure_ascii=False)

        logging.info(f"Successfully rewrote and appended {len(rewritten_blogs)} blog posts to {output_file}")

        # Update the input file by removing processed posts
        update_input_file(input_file, blogs, processed_indices)

    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in file: {str(e)}")
    except PermissionError as e:
        logging.error(f"Permission denied: {str(e)}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Rewrite blog posts using OpenAI API')
    parser.add_argument('--input', default=INPUT_FILE, help='Input JSON file containing blog posts')
    parser.add_argument('--output', default=OUTPUT_FILE, help='Output JSON file for rewritten blog posts')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making API calls')
    args = parser.parse_args()

    if args.dry_run:
        try:
            check_file_exists(args.input)
            validate_json_file(args.input)
            with open(args.input, 'r', encoding='utf-8') as f:
                blogs = json.load(f)
            logging.info(f"Dry run: Would process {len(blogs)} blog posts")
            for i, blog in enumerate(blogs, 1):
                logging.info(f"Blog {i}: Title: {blog['title']}, Content length: {len(blog.get('full_text', ''))}")
        except FileNotFoundError as e:
            logging.error(f"File not found: {str(e)}")
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in file: {str(e)}")
        except PermissionError as e:
            logging.error(f"Permission denied: {str(e)}")
        except Exception as e:
            logging.error(f"Error during dry run: {str(e)}")
    else:
        while True:
            try:
                process_blogs(args.input, args.output)
                logging.info(f"Waiting for {CHECK_INTERVAL // 60} minutes before checking for new content...")
                time.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                logging.info("Program interrupted by user. Exiting...")
                break
            except Exception as e:
                logging.error(f"An error occurred during execution: {str(e)}")
                logging.info("Retrying in 60 seconds...")
                time.sleep(60)

if __name__ == "__main__":
    main()
