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

    def search(self, domain: str) -> DomainResultsPage:
        log.info("Search for %s", domain)
        # fill() right after load is racy: if the input isn't hydrated yet, the value is set
        # but the search silently does nothing (observed ~1 in 2 runs). Typing key by key
        # goes through the component's handlers and was stable.
        self.search_input.click()
        self.search_input.press_sequentially(domain, delay=30)
        self.search_button.click()
        self.page.wait_for_url("**/domain/result/**")
        return DomainResultsPage(self.page)
