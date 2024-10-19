import json
import logging
import time
from chat_request import send_openai_request
from config_rewriter import MAX_TOKENS, RATE_LIMIT_DELAY

def chunk_content(content, max_tokens):
    words = content.split()
    chunks = []
    current_chunk = []
    current_token_count = 0

    for word in words:
        word_token_count = len(word.encode('utf-8')) // 4  # Better estimate for UTF-8 encoded text
        if current_token_count + word_token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_token_count = word_token_count
        else:
            current_chunk.append(word)
            current_token_count += word_token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def rewrite_blog_posts(blogs):
    rewritten_blogs = []
    processed_indices = []

    for i, blog in enumerate(blogs):
        logging.info(f"Processing blog post {i+1} of {len(blogs)}")

        try:
            if 'full_text' not in blog or not blog['full_text']:
                raise ValueError(f"Blog post {i+1} has no content")
            
            rewritten_content = rewrite_blog_post(blog['title'], blog['full_text'])
            rewritten_blog = {
                'title': rewritten_content['title'],
                'full_text': rewritten_content['content'],
                'image': blog.get('image', ''),
                'link': blog.get('link', ''),
                'categories': blog.get('categories', '')
            }
            rewritten_blogs.append(rewritten_blog)
            processed_indices.append(i)
            logging.info(f"Successfully rewrote blog post {i+1}")
        except ValueError as ve:
            logging.error(f"Error rewriting blog post {i+1}: {str(ve)}")
        except Exception as e:
            logging.error(f"Unexpected error rewriting blog post {i+1}: {str(e)}")

        time.sleep(RATE_LIMIT_DELAY)  # Rate limiting

    return rewritten_blogs, processed_indices

def rewrite_blog_post(title, content):
    chunks = chunk_content(content, MAX_TOKENS)
    rewritten_chunks = []

    for i, chunk in enumerate(chunks):
        prompt = f'''
Aşağıdaki blog yazısını yeniden yaz. İçerisindeki yazım hatalarından ve anlaşılmaz karakterlerden de kurtul. Orjinal bilgileri koru ancak farklı kelimeler ve yapı kullan. Sonucu 'content' anahtarı ile bir JSON nesnesi olarak döndürün. Türkçe karakterleri koruyun.

Orijinal Başlık: {title}

Orijinal İçerik Parçası:
{chunk}

Yeniden yazılmış versiyon:
'''

        try:
            response = send_openai_request(prompt)
            rewritten_chunk = json.loads(response)
            if 'content' not in rewritten_chunk:
                raise ValueError(f"ChatGPT response for chunk {i+1} does not contain 'content' key")
            rewritten_chunks.append(rewritten_chunk['content'])
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse ChatGPT response as JSON for chunk {i+1}")
        except Exception as e:
            raise Exception(f"Error in ChatGPT API call for chunk {i+1}: {str(e)}")

        time.sleep(RATE_LIMIT_DELAY)  # Rate limiting

    # Rewrite the title
    title_prompt = f'''
Aşağıdaki blog yazısı başlığını yeniden yaz. Genel mesajı koruyu ancak ilgi çekici olsun. Sonucu 'title' anahtarı ile bir JSON nesnesi olarak döndürün. Türkçe karakterleri koruyun.

Orijinal Başlık: {title}

Yeniden yazılmış versiyon:
'''

    try:
        title_response = send_openai_request(title_prompt)
        rewritten_title_json = json.loads(title_response)
        if 'title' not in rewritten_title_json:
            raise ValueError("ChatGPT response for title does not contain 'title' key")
        rewritten_title = rewritten_title_json['title']
    except json.JSONDecodeError:
        raise ValueError("Failed to parse ChatGPT response as JSON for title")
    except Exception as e:
        raise Exception(f"Error in ChatGPT API call for title: {str(e)}")

    return {
        'title': rewritten_title,
        'content': ' '.join(rewritten_chunks)
    }
