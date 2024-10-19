import requests
import base64
import json
from config import Config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def post_to_wordpress(post_data):
    url = f"{Config.WORDPRESS_URL}/wp-json/wp/v2/posts"

    # Create base64 encoded credentials
    credentials = Config.WORDPRESS_USERNAME + ':' + Config.WORDPRESS_PASSWORD
    token = base64.b64encode(credentials.encode()).decode('utf-8')

    headers = {'Authorization': 'Basic ' + token}

    data = {
        "title": post_data['title'],
        "content": post_data['full_text'],
        "status": "publish",
        "categories": [post_data['categories']]
    }

    if 'featured_media' in post_data:
        data['featured_media'] = post_data['featured_media']

    try:
        logger.info(f"Attempting to post to WordPress: {post_data['title']}")
        logger.debug(f"Post data: {json.dumps(data, indent=2)}")
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully posted: {post_data['title']}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error posting to WordPress: {e}")
        logger.error(
            f"Response status code: {getattr(e.response, 'status_code', 'No response')}"
        )
        logger.error(
            f"Response content: {getattr(e.response, 'text', 'No response')}")
        return False


def upload_featured_image(image_url):
    url = f"{Config.WORDPRESS_URL}/wp-json/wp/v2/media"

    # Create base64 encoded credentials
    credentials = f"{Config.WORDPRESS_USERNAME}:{Config.WORDPRESS_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode('utf-8')

    headers = {
        "Content-Type": "image/jpeg",
        "Authorization": f"Basic {token}",
        "Content-Disposition":
        f'attachment; filename="{image_url.split("/")[-1]}"'
    }

    try:
        logger.info(f"Attempting to upload featured image: {image_url}")
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        image_data = image_response.content

        response = requests.post(url, data=image_data, headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully uploaded featured image: {image_url}")
        return response.json()['id']
    except requests.exceptions.RequestException as e:
        logger.error(f"Error uploading featured image: {e}")
        logger.error(
            f"Response status code: {getattr(e.response, 'status_code', 'No response')}"
        )
        logger.error(
            f"Response content: {getattr(e.response, 'text', 'No response')}")
        return None
