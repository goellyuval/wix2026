import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui


class TestStorefrontSearch:
    """Domain storefront door. Never clicks "Make It Yours" / "Get It" (no purchases)."""

    def test_taken_domain_shows_registered_message(self, home_page, taken_domain):
        results = home_page.search(taken_domain)

        expect(results.taken_message).to_be_visible()
        expect(results.alternatives.first).to_be_visible()

    def test_free_domain_shows_available_card(self, results_page, free_domain):
        results_page.open_for(free_domain)

        expect(results_page.available_card).to_contain_text(free_domain)
        expect(results_page.available_card).to_contain_text("Available now!")

    @pytest.mark.parametrize("domain_fixture", ["taken_domain", "free_domain"], ids=["taken", "free"])
    def test_storefront_matches_public_api(self, request, results_page, domain_search_api, domain_fixture):
        # Parametrize over fixture names so each case reuses the shared test-data fixtures.
        domain = request.getfixturevalue(domain_fixture)
        api_says_available = domain_search_api.check_availability(domain).json()["availability"]["available"]

        ui_says_available = results_page.open_for(domain).is_domain_available()

        assert ui_says_available == api_says_available
