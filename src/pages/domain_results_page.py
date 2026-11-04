import logging
import re
from urllib.parse import quote

from src.pages.base_page import BasePage

log = logging.getLogger(__name__)


class DomainResultsPage(BasePage):
    """Search results: https://www.wix.com/domain/result/?q=<domain>

    Free domain      -> one "Exact Match" card (data-hook="hero-card").
    Taken domain     -> "is already registered" message + alternatives.
    TLD not sold     -> "<.tld> domains aren't available" message + alternatives.
    Name too long    -> "Domains should contain ..." message + shorter alternatives.
    """

    PATH = "/domain/result/"

    def __init__(self, page):
        super().__init__(page)
        self.available_card = self.by_hook("hero-card")
        self.taken_message = page.get_by_text("is already registered")
        # The page uses a typographic apostrophe (aren’t), so match any character there.
        self.unsupported_tld_message = page.get_by_text(re.compile(r"domains aren.t available"))
        self.length_limit_message = page.get_by_text(re.compile(r"Domains should contain"))

    def open_for(self, domain: str) -> "DomainResultsPage":
        return self.open(f"?q={quote(domain)}")

    def wait_for_result(self) -> None:
        """Wait until the page shows either result: available or taken."""
        self.available_card.or_(self.taken_message).first.wait_for()

    def is_domain_available(self) -> bool:
        self.wait_for_result()
        available = self.available_card.is_visible()
        log.info("Storefront shows domain as %s", "available" if available else "taken")
        return available

    def length_limit_text(self) -> str:
        self.length_limit_message.wait_for()
        return self.length_limit_message.inner_text()
