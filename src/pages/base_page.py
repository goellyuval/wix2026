import logging

from playwright.sync_api import Page

log = logging.getLogger(__name__)


class BasePage:
    """Common page infra. PATH is relative to base_url set in pytest.ini."""

    PATH = "/"

    def __init__(self, page: Page):
        self.page = page

    def open(self, query: str = ""):
        log.info("Open %s%s", self.PATH, query)
        self.page.goto(f"{self.PATH}{query}")
        return self

    def by_hook(self, hook: str):
        """Wix renders stable data-hook attributes; prefer them over generated CSS classes."""
        return self.page.locator(f'[data-hook="{hook}"]')
