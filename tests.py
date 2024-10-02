import hashlib
import pathlib
import tempfile
from crawler import Crawler


def test_already_saved():
    with tempfile.TemporaryDirectory() as temp_dir:
        path_dir = pathlib.Path(temp_dir)
        crawler = Crawler(path_dir, max_threads=8)
        url = "https://www.example.com/page"
        assert not crawler._already_saved(url)

        file_name = hashlib.md5(url.encode()).hexdigest() + ".html"
        file = path_dir.joinpath(file_name)
        file.touch()
        assert crawler._already_saved(url)


def test_is_allowed_domain():
    with tempfile.TemporaryDirectory() as temp_dir:
        path_dir = pathlib.Path(temp_dir)
        crawler = Crawler(path_dir, max_threads=8)
        crawler._allowed_domains = ["example.com"]
        assert crawler._is_allowed_domain("https://www.example.com/page")
        assert not crawler._is_allowed_domain("https://www.anotherexample.com/page")


def test_save_page():
    with tempfile.TemporaryDirectory() as temp_dir:
        path_dir = pathlib.Path(temp_dir)

        crawler = Crawler(path_dir, max_threads=8)
        content = "<html><body><h1>Test Page</h1></body></html>"
        url = "https://www.example.com/page"
        file_name = path_dir.joinpath(hashlib.md5(url.encode()).hexdigest() + ".html")

        crawler._save_page(content, url)
        assert file_name.exists()
        assert file_name.read_text() == content


def test_start_crawl():
    with tempfile.TemporaryDirectory() as temp_dir:
        path_dir = pathlib.Path(temp_dir)
        start_url = "https://www.example.com"
        allowed_domains = ["example.com"]
        file = path_dir.joinpath(hashlib.md5(start_url.encode()).hexdigest() + ".html")
        fake_file = path_dir.joinpath("aboba.html")

        crawler = Crawler(path_dir, max_threads=8)
        crawler.start_crawl(start_url, allowed_domains, depth=1)

        assert len(crawler._visited_urls) == 1
        assert file.exists()
        assert not fake_file.exists()


def test_robots():
    with tempfile.TemporaryDirectory() as temp_dir:
        path_dir = pathlib.Path(temp_dir)
        start_url = "https://ru.linkedin.com/"
        allowed_domains = ["ru.linkedin.com"]

        crawler = Crawler(path_dir, max_threads=8)
        crawler.start_crawl(start_url, allowed_domains, depth=1)
        assert len(crawler._visited_urls) == 0
