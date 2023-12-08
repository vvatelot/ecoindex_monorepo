from tempfile import NamedTemporaryFile

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class EcoindexSpider(CrawlSpider):
    name = "EcoindexSpider"
    custom_settings = {"LOG_ENABLED": False}
    rules = (Rule(LinkExtractor(), callback="parse_item", follow=True),)

    def __init__(
        self,
        allowed_domains: list[str],
        start_urls: list[str],
        temp_file: NamedTemporaryFile,  # type: ignore
        *a,
        **kw,
    ):
        self.links: set[str] = set()
        self.allowed_domains = allowed_domains
        self.start_urls = start_urls
        self.temp_file = temp_file
        super().__init__(*a, **kw)

    def parse_item(self, response):
        self.temp_file.write(f"{response.url}\n")
