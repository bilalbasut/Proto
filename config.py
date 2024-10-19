import os


class Config:
    JSON_FILE_PATH = 'rewritten_blogs.json'
    WORDPRESS_URL = os.environ.get('WORDPRESS_URL')
    WORDPRESS_USERNAME = os.environ.get('WORDPRESS_USERNAME')
    WORDPRESS_PASSWORD = os.environ.get('WORDPRESS_PASSWORD')
