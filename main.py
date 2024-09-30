from crawler import Crawler

# Папка для сохранения скачанных страниц
save_dir = "downloaded_pages"
# Файл для хранения посещённых URL
saved_files = "saved_urls.txt"
#Максимальное число потоков
max_threads = 8
# Начальный URL
start_url = "https://quotes.toscrape.com/"
# Список допустимых доменов
allowed_domains = ["quotes.toscrape.com"]

def main():
    crawler = Crawler(save_dir, saved_files, max_threads)
    crawler.start_crawl(start_url, allowed_domains, depth=2)

if __name__ == '__main__':
    main()