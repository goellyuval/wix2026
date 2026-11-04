import pytest
from playwright.sync_api import expect

from src.utils.domains import TAKEN_DOMAIN, random_unregistered_domain

pytestmark = pytest.mark.ui


class TestStorefrontSearch:
    """Domain storefront door. Never clicks "Make It Yours" / "Get It" (no purchases)."""

    def test_taken_domain_shows_registered_message(self, home_page):
        results = home_page.search(TAKEN_DOMAIN)

        expect(results.taken_message).to_be_visible()
        expect(results.alternatives.first).to_be_visible()

    def test_free_domain_shows_available_card(self, results_page):
        domain = random_unregistered_domain()

        results_page.open_for(domain)

        expect(results_page.available_card).to_contain_text(domain)
        expect(results_page.available_card).to_contain_text("Available now!")

    @pytest.mark.parametrize("domain", [TAKEN_DOMAIN, random_unregistered_domain()], ids=["taken", "free"])
    def test_storefront_matches_public_api(self, results_page, domain_search_api, domain):
        api_says_available = domain_search_api.check_availability(domain).json()["availability"]["available"]

        ui_says_available = results_page.open_for(domain).is_domain_available()

        assert ui_says_available == api_says_available
