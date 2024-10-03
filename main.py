from crawler import Crawler
from config import settings


def main():
    crawler = Crawler(settings.max_threads)
    crawler.start_crawl(settings.start_url, settings.allowed_domains, settings.save_dir, depth=2, update_files=True, make_graph=True)
    #crawler.start_mirror_crawl(settings.start_url, settings.allowed_domains, settings.mirror_dir, depth=2, update_files=False)

if __name__ == '__main__':
    main()