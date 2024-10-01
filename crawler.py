import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from robots import RobotsHandler


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def fetch(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при запросе к {url}: {e}")
        return None


class Crawler:
    def __init__(self, save_dir: str, file_for_urls: str, max_threads: int):
        self._allowed_domains = None
        self._start_url = None
        self._visited_urls = set()
        self._saved_urls = set()
        self._file_for_urls = file_for_urls
        self._save_dir = save_dir
        self._max_threads = max_threads
        self._robots_handler = RobotsHandler()

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def _load_saved_urls(self):
        if os.path.exists(self._file_for_urls):
            with open(self._file_for_urls, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f)
        return set()

    def _add_saved_url(self, url):
        with open(self._file_for_urls, 'a', encoding='utf-8') as f:
            f.write(url + "\n")

    def _is_allowed_domain(self, url):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain in self._allowed_domains

    def _save_page(self, content, url):
        file_name = hashlib.md5(url.encode()).hexdigest() + ".html"
        file_path = os.path.join(self._save_dir, file_name)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Страница сохранена: {file_path}")


    def _crawl(self, url, depth=1):
        if url in self._visited_urls or depth <= 0:
            return

        if not self._robots_handler.can_fetch(url):
            print(f"Доступ к {url} запрещен правилами robots.txt\r")
            return

        print(f"Посещаем: {url}\r")
        self._visited_urls.add(url)

        html = fetch(url)
        if html is None:
            return

        if url not in self._saved_urls:
            self._save_page(html, url)
            self._add_saved_url(url)

        soup = BeautifulSoup(html, 'html.parser')

        tasks = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href")
            # Приводим относительные URL к полным
            full_url = urljoin(url, href)

            if is_valid_url(full_url) and full_url not in self._visited_urls and self._is_allowed_domain(full_url):
                tasks.append((full_url, depth))

        return tasks

    def start_crawl(self, start_url: str, allowed_domains: list[str], depth=2):
        self._saved_urls = self._load_saved_urls()
        self._start_url = start_url
        self._allowed_domains = allowed_domains
        self._visited_urls = set()

        with ThreadPoolExecutor(max_workers=self._max_threads) as executor:
            futures = [executor.submit(self._crawl, start_url, depth)]

            while futures:
                for future in as_completed(futures):
                    tasks = future.result()
                    if tasks:
                        for url, new_depth in tasks:
                            futures.append(executor.submit(self._crawl, url, new_depth))
                futures = [f for f in futures if not f.done()]