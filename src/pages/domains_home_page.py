import logging

from src.pages.base_page import BasePage
from src.pages.domain_results_page import DomainResultsPage

log = logging.getLogger(__name__)


class DomainsHomePage(BasePage):
    """Domain storefront landing page: https://www.wix.com/domains"""

    PATH = "/domains"

    def __init__(self, page):
        super().__init__(page)
        # The page has two identical search boxes (hero + footer); the first is the hero one.
        self.search_input = page.get_by_role("searchbox", name="Type the domain you want").first
        self.search_button = page.get_by_role("button", name="Search Domains").first

    def open(self, query: str = ""):
        super().open(query)
        # Hydration race: on "load" the search box accepts text, but its click handler isn't
        # attached yet, so "Search" silently does nothing (first search ignored 5/5 headless runs).
        # Playwright usually discourages networkidle, but here it is the measured "ready" signal:
        # after it, the first search worked 3/3 (~4.7 s). See FINDINGS.md.
        self.page.wait_for_load_state("networkidle")
        return self

    def search(self, domain: str) -> DomainResultsPage:
        log.info("Search for %s", domain)
        self.search_input.fill(domain)
        self.search_button.click()
        self.page.wait_for_url("**/domain/result/**")
        return DomainResultsPage(self.page)
