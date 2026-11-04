import pytest

from src.utils.domains import DOCUMENTED_PREMIUM_TYPES

pytestmark = pytest.mark.api


class TestCheckAvailability:

    def test_taken_domain_is_not_available(self, domain_search_api, taken_domain):
        response = domain_search_api.check_availability(taken_domain)

        assert response.status_code == 200
        assert response.json()["availability"]["available"] is False

    def test_free_domain_is_available(self, domain_search_api, free_domain):
        response = domain_search_api.check_availability(free_domain)

        assert response.status_code == 200
        availability = response.json()["availability"]
        assert availability["domain"] == free_domain
        assert availability["available"] is True
        assert availability["premium"] is False

    def test_response_has_documented_fields(self, domain_search_api, taken_domain):
        availability = domain_search_api.check_availability(taken_domain).json()["availability"]

        assert isinstance(availability["domain"], str)
        assert isinstance(availability["available"], bool)
        assert isinstance(availability["premium"], bool)
        assert isinstance(availability["premiumType"], str)

    def test_uppercase_domain_is_returned_lowercase(self, domain_search_api, taken_domain):
        response = domain_search_api.check_availability(taken_domain.upper())

        assert response.status_code == 200
        assert response.json()["availability"]["domain"] == taken_domain

    def test_63_character_name_is_accepted(self, domain_search_api):
        # Boundary: the limit is 63 characters for the name, not counting the TLD.
        response = domain_search_api.check_availability("a" * 63 + ".com")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "domain, expected_message",
        [
            pytest.param("mybakery", "INVALID_DOMAIN", id="missing_tld"),
            pytest.param("mybakery.notatld", "INVALID_DOMAIN", id="unknown_tld"),
            pytest.param("", "domain must not be empty", id="empty"),
            pytest.param("my_bakery.com", "not a valid hostname", id="underscore"),
            pytest.param("-bakery.com", "not a valid hostname", id="leading_hyphen"),
            pytest.param("bakery-.com", "not a valid hostname", id="trailing_hyphen"),
            pytest.param("קפה.com", "not a valid hostname", id="non_latin"),
            pytest.param("a" * 64 + ".com", "DOMAIN_TOO_LONG", id="64_character_name"),
        ],
    )
    def test_invalid_domain_returns_400(self, domain_search_api, domain, expected_message):
        response = domain_search_api.check_availability(domain)

        assert response.status_code == 400
        assert expected_message in response.json()["message"]

    def test_tld_not_sold_by_wix_returns_400(self, domain_search_api):
        # .gov is a real TLD, but not one Wix sells.
        response = domain_search_api.check_availability("qa-bakery-test.gov")

        assert response.status_code == 400
        assert response.json()["details"]["applicationError"]["code"] == "DOMAINS_UNSUPPORTED_TLD"

    @pytest.mark.xfail(strict=True, reason="API returns UNKNOWN_PREMIUM_TYPE, not in the documented enum. See FINDINGS.md")
    def test_premium_type_is_a_documented_value(self, domain_search_api, taken_domain):
        availability = domain_search_api.check_availability(taken_domain).json()["availability"]

        assert availability["premiumType"] in DOCUMENTED_PREMIUM_TYPES
