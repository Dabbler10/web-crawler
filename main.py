from crawler import Crawler
from config import settings


def main():
    crawler = Crawler(settings.save_dir, settings.max_threads)
    crawler.start_crawl(settings.start_url, settings.Allowed_domains, depth=2)

if __name__ == '__main__':
    main()