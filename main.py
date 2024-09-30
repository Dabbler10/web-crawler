import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed


# Папка для сохранения скачанных страниц
save_dir = "downloaded_pages"
# Файл для хранения посещённых URL
saved_files = "saved_urls.txt"
max_threads = 8

# Начальный URL
start_url = "https://quotes.toscrape.com/"
# Список допустимых доменов
allowed_domains = {"quotes.toscrape.com"}

if not os.path.exists(save_dir):
    os.makedirs(save_dir)

visited_urls = set()
saved_urls = set()


def load_saved_urls():
    if os.path.exists(saved_files):
        with open(saved_files, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    return set()

def add_saved_url(url):
    with open(saved_files, 'a', encoding='utf-8') as f:
        f.write(url + "\n")


def fetch(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при запросе к {url}: {e}")
        return None


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def is_allowed_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in allowed_domains


def save_page(content, url):
    file_name = hashlib.md5(url.encode()).hexdigest() + ".html"
    file_path = os.path.join(save_dir, file_name)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Страница сохранена: {file_path}")


def crawl(url, depth=1):
    if url in visited_urls or depth <= 0:
        return

    print(f"Посещаем: {url}\r")
    visited_urls.add(url)

    html = fetch(url)
    if html is None:
        return

    if url not in saved_urls :
        save_page(html, url)
        add_saved_url(url)

    soup = BeautifulSoup(html, 'html.parser')

    tasks = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        # Приводим относительные URL к полным
        full_url = urljoin(url, href)

        if is_valid_url(full_url) and full_url not in visited_urls and is_allowed_domain(full_url):
            tasks.append((full_url, depth - 1))

    return tasks


def start_crawl(start_url, depth=2):
    global visited_urls
    global saved_urls
    saved_urls = load_saved_urls()

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(crawl, start_url, depth)]

        while futures:
            for future in as_completed(futures):
                tasks = future.result()
                if tasks:
                    for url, new_depth in tasks:
                        futures.append(executor.submit(crawl, url, new_depth))
            futures = [f for f in futures if not f.done()]


start_crawl(start_url, depth=2)