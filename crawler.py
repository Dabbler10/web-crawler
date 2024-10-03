import pathlib
from anytree import Node, RenderTree
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import validators
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from robots import RobotsHandler


def fetch(url: str) -> str | None:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при запросе к {url}: {e}")
        return None


class Crawler:
    def __init__(self, max_threads: int):
        self._allowed_domains = None
        self._start_url = None
        self._visited_urls = set()
        self._save_dir = None
        self._max_threads = max_threads
        self._robots_handler = RobotsHandler()
        self._update_files = False
        self._full_urls_dict = dict()

    def _already_saved(self, url: str) -> bool:
        file_name = hashlib.md5(url.encode()).hexdigest() + ".html"
        files = self._save_dir.iterdir()
        return pathlib.Path(f"{self._save_dir}/{file_name}") in files

    def _is_allowed_domain(self, url: str) -> bool:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain in self._allowed_domains

    def _save_page(self, content: str, url: str) -> None:
        file_name = hashlib.md5(url.encode()).hexdigest() + ".html"
        file = self._save_dir.joinpath(file_name)
        file.touch()
        file.write_text(content, encoding="utf-8")
        print(f"Страница сохранена: {file.name}")

    def _update_page(self, content: str, url: str) -> None:
        file_name = hashlib.md5(url.encode()).hexdigest() + ".html"
        file = self._save_dir.joinpath(file_name)
        if file.read_text(encoding="utf-8") != content:
            file.write_text(content, encoding="utf-8")
            print(f"Страница обновлена: {file.name}")

    def _mirror_page(self, file: pathlib.Path) -> None:
        soup = BeautifulSoup(file.read_text(encoding="utf-8"), 'html.parser')
        full_path = pathlib.Path.cwd().joinpath(self._save_dir)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href")
            full_url = self._full_urls_dict.get(href)
            if full_url is not None:
                a_tag["href"] = full_path.joinpath(hashlib.md5(full_url.encode()).hexdigest() + ".html")
        file.write_text(soup.prettify(), encoding="utf-8")

    def _crawl(self, url: str, parent_node: Node, depth=1) -> list[tuple[str, Node, int]] | None:
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

        if not self._already_saved(url):
            self._save_page(html, url)
        elif self._update_files:
            self._update_page(html, url)

        soup = BeautifulSoup(html, 'html.parser')

        tasks = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href")
            # Приводим относительные URL к полным
            full_url = urljoin(url, href)
            self._full_urls_dict[href] = full_url

            if validators.url(full_url) and full_url not in self._visited_urls and self._is_allowed_domain(full_url):
                root = Node(full_url, parent=parent_node)
                tasks.append((full_url, root, depth))

        return tasks

    def start_crawl(self, start_url: str, allowed_domains: list[str], save_dir: pathlib.Path, depth=2,
                    update_files=False, make_graph=False) -> None:
        self._start_url = start_url
        self._allowed_domains = allowed_domains
        self._visited_urls = set()
        self._update_files = update_files
        self._save_dir = save_dir
        root = Node(self._start_url)

        if not self._save_dir.exists():
            self._save_dir.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self._max_threads) as executor:
            futures = [executor.submit(self._crawl, start_url, root, depth)]

            while futures:
                for future in as_completed(futures):
                    tasks = future.result()
                    if tasks:
                        for url, new_depth, node in tasks:
                            futures.append(executor.submit(self._crawl, url, new_depth, node))
                futures = [f for f in futures if not f.done()]

        if make_graph:
            for pre, fill, node in RenderTree(root):
                print("%s%s" % (pre, node.name))

    def start_mirror_crawl(self, start_url: str, allowed_domains: list[str], mirror_dir: pathlib.Path, depth=2,
                           update_files=False, make_graph=False) -> None:
        self.start_crawl(start_url, allowed_domains, mirror_dir, depth, update_files, make_graph)
        for file in mirror_dir.iterdir():
            self._mirror_page(file)
