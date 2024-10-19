import requests
from bs4 import BeautifulSoup
import json
import logging
import schedule
import time
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlogScraper:
    def __init__(self):
        self.headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def scrape(self):
        all_blog_posts = []
        for website in self.config['websites']:
            blog_posts = self.scrape_website(website)
            all_blog_posts.extend(blog_posts)
        return all_blog_posts

    def scrape_website(self, website):
        logger.info(f"Scraping {website['name']}")
        url = website['url']
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.select(website['article_selector'])
        logger.info(f"Found {len(articles)} articles on {website['name']}")

        blog_posts = []
        last_scraped_title = self.get_last_scraped_title(website['name'])

        for i, article in enumerate(articles):
            article_data = self.extract_article_data(article, website)
            if article_data:
                if article_data['title'] == last_scraped_title:
                    logger.info(
                        f"Reached last scraped article for {website['name']}")
                    break
                blog_posts.append(article_data)
                logger.info(f"Article {i+1} title: '{article_data['title']}'")

        if blog_posts:
            self.update_last_scraped_title(website['name'],
                                           blog_posts[0]['title'])

        return blog_posts

    def extract_article_data(self, article, website):
        try:
            logger.info(f"Extracting data for {website['name']} article")

            title_elem = article.select_one(website['title_selector'])
            link_elem = article.select_one(website['link_selector'])
            image_elem = article.select_one(website['image_selector'])
            date_elem = article.select_one(website['date_selector'])

            logger.debug(f"Title element: {title_elem}")
            logger.debug(f"Link element: {link_elem}")
            logger.debug(f"Image element: {image_elem}")
            logger.debug(f"Date element: {date_elem}")

            if not (title_elem and link_elem):
                logger.warning(
                    f"Missing title or link for article in {website['name']}")
                return None

            title = title_elem.text.strip()
            link = link_elem['href']
            if not link.startswith('http'):
                link = urljoin(website['url'], link)

            image_url = None
            if image_elem:
                if 'src' in image_elem.attrs:
                    image_url = image_elem['src']
                elif 'data-src' in image_elem.attrs:
                    image_url = image_elem['data-src']
                elif 'style' in image_elem.attrs:
                    style = image_elem['style']
                    if 'background-image' in style:
                        image_url = style.split('url(')[1].split(')')[0].strip("'\"")
            
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(website['url'], image_url)

            logger.info(f"Extracted image URL for {website['name']}: {image_url}")
            
            if website['name'] == 'Karar':
                logger.info(f"Karar.com image element: {image_elem}")
                logger.info(f"Karar.com image element attributes: {image_elem.attrs if image_elem else 'No attributes'}")
                logger.info(f"Karar.com image URL extraction process:")
                logger.info(f"  - 'src' in attributes: {'src' in image_elem.attrs if image_elem else False}")
                logger.info(f"  - 'data-src' in attributes: {'data-src' in image_elem.attrs if image_elem else False}")
                logger.info(f"  - 'style' in attributes: {'style' in image_elem.attrs if image_elem else False}")
                if image_elem and 'style' in image_elem.attrs:
                    logger.info(f"  - Style attribute content: {image_elem['style']}")

            date = date_elem.text.strip() if date_elem else None

            if website['name'] == 'BBC Turkish':
                category = 10
            else:
                category = 1

            article_data = {
                'title': title,
                'link': link,
                'image': image_url,
                'date': date,
                'categories': category
            }

            if website['name'] == 'BBC Turkish':
                article_content = self.parse_bbc_article_content(link)
            else:
                article_content = self.parse_article_content(link, website)
            article_data.update(article_content)

            logger.info(f"Processed article from {website['name']}: {title}")
            return article_data
        except Exception as e:
            logger.error(
                f"Error in extract_article_data for {website['name']}: {str(e)}"
            )
            return None

    def parse_bbc_article_content(self, article_url):
        try:
            response = requests.get(article_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            main_content = soup.select_one('main[role="main"]')

            if main_content:
                content_blocks = main_content.find_all(
                    ['p', 'h2', 'h3', 'ul', 'ol'])
                full_text = '\n'.join([
                    block.get_text(strip=True) for block in content_blocks
                    if block.get_text(strip=True)
                ])
                logger.info(
                    f"Extracted full text (first 200 characters): {full_text[:200]}..."
                )
            else:
                full_text = "Content not found"
                logger.warning(
                    "Main content element not found in BBC Turkish article")

            tags = soup.select("li.bbc-1msyfg1")
            logger.info(
                f"Extracted tags: {[tag.text.strip() for tag in tags]}")

            return {
                'full_text': full_text,
                'tags': [tag.text.strip() for tag in tags] if tags else []
            }
        except Exception as e:
            logger.error(
                f"Error parsing BBC article content for {article_url}: {str(e)}"
            )
            return {}

    def parse_article_content(self, article_url, website):
        if not article_url:
            return {}

        try:
            response = requests.get(article_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching article {article_url}: {str(e)}")
            return {}

        article_content = soup.select_one(website['content_selector'])

        if not article_content:
            logger.warning(f"Could not find article content for {article_url}")
            return {}

        text_content = article_content.select(website['text_content_selector'])
        full_text = '\n'.join([p.text.strip() for p in text_content])
        tags = article_content.select(website['tag_selector'])

        return {
            'full_text': full_text,
            'tags': [tag.text.strip() for tag in tags] if tags else []
        }

    def get_last_scraped_title(self, website_name):
        try:
            with open('last_scraped_titles.json', 'r') as f:
                last_scraped_titles = json.load(f)
            return last_scraped_titles.get(website_name, '')
        except (FileNotFoundError, json.JSONDecodeError):
            return ''

    def update_last_scraped_title(self, website_name, title):
        try:
            with open('last_scraped_titles.json', 'r') as f:
                last_scraped_titles = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            last_scraped_titles = {}

        last_scraped_titles[website_name] = title

        with open('last_scraped_titles.json', 'w') as f:
            json.dump(last_scraped_titles, f)

    def save_to_json(self, new_data, filename='scraped_data.json'):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        merged_data = existing_data.copy()
        for article in new_data:
            if not any(existing['link'] == article['link']
                       for existing in existing_data):
                merged_data.append(article)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {filename}")

def run_scraper():
    scraper = BlogScraper()
    try:
        new_blog_posts = scraper.scrape()
        scraper.save_to_json(new_blog_posts)
        logger.info(
            f"Successfully scraped {len(new_blog_posts)} new blog posts from multiple websites"
        )
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

def main():
    logger.info("Starting the scraper scheduler")
    schedule.every(1).hour.do(run_scraper)

    run_scraper()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()