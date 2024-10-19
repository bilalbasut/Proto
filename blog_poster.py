import json
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from wordpress_api import post_to_wordpress, upload_featured_image
from config import Config

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHECK_INTERVAL = 300  # 5 minutes

def get_last_posted_index():
    try:
        with open('last_posted_index.txt', 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return -1

def update_last_posted_index(index):
    with open('last_posted_index.txt', 'w') as file:
        file.write(str(index))

def check_for_updates():
    try:
        logger.info("Checking for updates...")
        with open(Config.JSON_FILE_PATH, 'r') as file:
            data = json.load(file)
        
        last_posted_index = get_last_posted_index()
        
        for index, post in enumerate(data[last_posted_index + 1:], start=last_posted_index + 1):
            logger.info(f"Processing post {index}: {post['title']}")
            
            featured_image_id = upload_featured_image(post['image'])
            if featured_image_id:
                post['featured_media'] = featured_image_id
            else:
                logger.warning(f"Failed to upload featured image for post {index}")
            
            if post_to_wordpress(post):
                update_last_posted_index(index)
                logger.info(f"Successfully posted and updated index to {index}")
            else:
                logger.error(f"Failed to post article {index}")
                break
        logger.info("Update check completed.")
    except Exception as e:
        logger.exception(f"Error checking for updates: {e}")

def main():
    logger.info("Starting blog posting script")
    
    if not all([Config.WORDPRESS_URL, Config.WORDPRESS_USERNAME, Config.WORDPRESS_PASSWORD]):
        logger.error("WordPress configuration is incomplete. Please set WORDPRESS_URL, WORDPRESS_USERNAME, and WORDPRESS_PASSWORD environment variables.")
        return

    # Manually trigger an update check when the script starts
    check_for_updates()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_for_updates, trigger="interval", seconds=CHECK_INTERVAL)
    scheduler.start()

    logger.info(f"Blog posting script is running. Checking for updates every {CHECK_INTERVAL} seconds. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Script stopped.")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
