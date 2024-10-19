import json
import os
from config import Config
from wordpress_api import post_to_wordpress, upload_featured_image

def check_for_updates():
    try:
        with open(Config.JSON_FILE_PATH, 'r') as file:
            data = json.load(file)
        
        last_posted_index = get_last_posted_index()
        
        for index, post in enumerate(data[last_posted_index + 1:], start=last_posted_index + 1):
            featured_image_id = upload_featured_image(post['image'])
            if featured_image_id:
                post['featured_media'] = featured_image_id
            
            if post_to_wordpress(post):
                update_last_posted_index(index)
            else:
                break
    except Exception as e:
        print(f"Error checking for updates: {e}")

def get_last_posted_index():
    try:
        with open('last_posted_index.txt', 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return -1

def update_last_posted_index(index):
    with open('last_posted_index.txt', 'w') as file:
        file.write(str(index))
