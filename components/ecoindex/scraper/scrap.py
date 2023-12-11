import json
import os
from datetime import datetime
from time import sleep
from uuid import uuid4

from ecoindex.compute import compute_ecoindex
from ecoindex.exceptions.scraper import EcoindexScraperStatusException
from ecoindex.models.compute import PageMetrics, Result, ScreenShot, WindowSize
from ecoindex.models.scraper import Requests
from ecoindex.scraper.user_agent import get_user_agent
from ecoindex.utils.screenshots import convert_screenshot_to_webp, set_screenshot_rights
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from typing_extensions import deprecated


class EcoindexScraper:
    def __init__(
        self,
        url: str,
        window_size: WindowSize = WindowSize(width=1920, height=1080),
        wait_before_scroll: float = 1,
        wait_after_scroll: float = 1,
        screenshot: ScreenShot | None = None,
        screenshot_uid: int | None = None,
        screenshot_gid: int | None = None,
        page_load_timeout: int = 20,
    ):
        self.url = url
        self.window_size = window_size
        self.wait_before_scroll = wait_before_scroll
        self.wait_after_scroll = wait_after_scroll
        self.screenshot = screenshot
        self.screenshot_uid = screenshot_uid
        self.screenshot_gid = screenshot_gid
        self.page_load_timeout = page_load_timeout
        self.all_requests = Requests()
        self.now = datetime.now()
        self.har_temp_file_path = (
            f"/tmp/ecoindex-{self.now.strftime('%Y-%m-%d-%H-%M-%S-%f')}-{uuid4()}.har"
        )

    @deprecated("This method is useless with new version of EcoindexScraper")
    def init_chromedriver(self):
        return self

    async def get_page_analysis(self) -> Result:
        page_metrics = await self.scrap_page()
        ecoindex = await compute_ecoindex(**page_metrics.model_dump())

        return Result(
            **ecoindex.model_dump(),
            **self.window_size.model_dump(),
            **page_metrics.model_dump(),
            date=self.now,
            url=self.url,
        )

    async def scrap_page(self) -> PageMetrics:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            user_agent = await get_user_agent()
            print(f"Make request to {self.url} with {user_agent}")
            self.page = await browser.new_page(
                record_har_path=self.har_temp_file_path,
                screen=self.window_size.model_dump(),
                ignore_https_errors=True,
                user_agent=user_agent,
            )
            await stealth_async(self.page)
            response = await self.page.goto(self.url)
            if response and response.status != 200:
                raise EcoindexScraperStatusException(
                    url=self.url,
                    status=response.status,
                    message=response.status_text,
                )

            await self.page.wait_for_load_state()
            sleep(self.wait_before_scroll)
            await self.generate_screenshot()
            await self.page.evaluate(
                "window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })"
            )
            sleep(self.wait_after_scroll)
            total_nodes = await self.get_nodes_count()

            await self.page.close()
            await browser.close()

        await self.get_requests_from_har_file()

        return PageMetrics(
            size=self.all_requests.total_size / 1000,
            nodes=total_nodes,
            requests=self.all_requests.total_count,
        )

    async def generate_screenshot(self) -> None:
        if self.screenshot and self.screenshot.folder and self.screenshot.id:
            await self.page.screenshot(path=self.screenshot.get_png())
            await convert_screenshot_to_webp(self.screenshot)
            await set_screenshot_rights(
                screenshot=self.screenshot,
                uid=self.screenshot_uid,
                gid=self.screenshot_gid,
            )

    async def get_requests_from_har_file(self):
        with open(self.har_temp_file_path, "r") as f:
            trace = json.load(f)

            for entry in trace["log"]["entries"]:
                self.all_requests.items.append(
                    {
                        "url": entry["request"]["url"],
                        "mime_type": entry["response"]["content"]["mimeType"],
                        "status": entry["response"]["status"],
                        "size": entry["response"]["_transferSize"],
                    }
                )

                self.all_requests.total_count += 1
                self.all_requests.total_size += entry["response"]["_transferSize"]

        os.remove(self.har_temp_file_path)

    async def get_nodes_count(self) -> int:
        nodes = await self.page.locator("*").all()
        svgs = await self.page.locator("//*[local-name()='svg']//*").all()

        return len(nodes) - len(svgs)
