"""UI-local fixtures. `page` and `base_url` come from pytest-playwright / pytest.ini."""
import pytest

from src.pages.domain_results_page import DomainResultsPage
from src.pages.domains_home_page import DomainsHomePage


@pytest.fixture
def browser_context_args(browser_context_args):
    # Pin locale so text assertions ("is already registered") are stable.
    # Geo (prices, currency, .co.il) still follows the machine's IP.
    return {**browser_context_args, "locale": "en-US"}


@pytest.fixture
def home_page(page) -> DomainsHomePage:
    return DomainsHomePage(page).open()


@pytest.fixture
def results_page(page) -> DomainResultsPage:
    return DomainResultsPage(page)
