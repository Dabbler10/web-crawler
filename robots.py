import urllib.robotparser as robot_parser
from urllib.parse import urljoin, urlparse

class RobotsHandler:
    def __init__(self):
        self.parsers = {}

    def can_fetch(self, url, user_agent='*'):
        domain = urlparse(url).netloc
        if domain not in self.parsers:
            robots_url = urljoin(f'http://{domain}', '/robots.txt')
            rp = robot_parser.RobotFileParser()
            try:
                rp.set_url(robots_url)
                rp.read()
                self.parsers[domain] = rp
            except Exception as e:
                print(f"Ошибка при загрузке robots.txt для {domain}: {e}")
                self.parsers[domain] = None

        # Если robots.txt отсутствует или не смогли его загрузить, запрещаем обход
        if self.parsers[domain] is None:
            return False

        return self.parsers[domain].can_fetch(user_agent, url)