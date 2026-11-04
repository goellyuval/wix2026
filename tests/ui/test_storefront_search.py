import pytest
from playwright.sync_api import expect

from src.utils.domains import random_unregistered_domain

pytestmark = [pytest.mark.ui, pytest.mark.regression]


class TestStorefrontSearch:
    """Domain storefront door. Lean on purpose: one flow and one assertion per test.
    Contract and data checks live in the API tests. Never clicks "Make It Yours" / "Get It" (no purchases).
    """

    def test_taken_domain_shows_registered_message(self, home_page, taken_domain):
        # The only test that goes through the home page search box; the others open results by URL.
        results = home_page.search(taken_domain)

        expect(results.taken_message).to_be_visible()

    def test_free_domain_shows_available_card(self, results_page, free_domain):
        results_page.open_for(free_domain)

        expect(results_page.available_card).to_contain_text(free_domain)

    @pytest.mark.sanity
    @pytest.mark.parametrize("domain_fixture", ["taken_domain", "free_domain"], ids=["taken", "free"])
    def test_storefront_matches_public_api(self, request, results_page, domain_search_api, domain_fixture):
        # Parametrize over fixture names so each case reuses the shared test-data fixtures.
        domain = request.getfixturevalue(domain_fixture)
        api_says_available = domain_search_api.check_availability(domain).json()["availability"]["available"]

        ui_says_available = results_page.open_for(domain).is_domain_available()

        assert ui_says_available == api_says_available

    def test_tld_not_sold_by_wix_shows_message(self, results_page):
        results_page.open_for(random_unregistered_domain(tld="gov"))

        expect(results_page.unsupported_tld_message).to_be_visible()

    @pytest.mark.xfail(strict=True, reason="Says 'fewer than 63' but 63 is allowed and suggested. See FINDINGS.md F3")
    def test_length_limit_message_matches_the_real_limit(self, results_page):
        results_page.open_for("a" * 64 + ".com")

        assert "fewer than 63" not in results_page.length_limit_text()
