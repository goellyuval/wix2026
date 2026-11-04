import pytest

from src.utils.domains import is_full_domain

pytestmark = pytest.mark.api

QUERY = "sunny bakery"


class TestSuggestDomains:
    """Suggestions are generated, so these tests check the contract, never the exact names."""

    def test_returns_at_most_the_requested_limit(self, domain_search_api):
        response = domain_search_api.suggest_domains(QUERY, limit=5)

        assert response.status_code == 200
        assert 0 < len(response.json()["suggestions"]) <= 5

    def test_count_matches_number_of_suggestions(self, domain_search_api):
        body = domain_search_api.suggest_domains(QUERY, limit=5).json()

        assert body["pagingMetadata"]["count"] == len(body["suggestions"])

    def test_every_suggestion_is_a_full_domain(self, domain_search_api):
        suggestions = domain_search_api.suggest_domains(QUERY, limit=10).json()["suggestions"]

        bad = [s["domain"] for s in suggestions if not is_full_domain(s["domain"])]
        assert not bad, f"not a valid name.tld: {bad}"

    def test_tld_filter_returns_only_that_tld(self, domain_search_api):
        suggestions = domain_search_api.suggest_domains(QUERY, limit=5, tlds=["com"]).json()["suggestions"]

        domains = [s["domain"] for s in suggestions]
        assert domains, "expected at least one .com suggestion"
        assert all(d.endswith(".com") for d in domains), domains

    def test_tld_with_leading_dot_returns_400(self, domain_search_api):
        # Docs: TLDs are passed without the dot ("com", not ".com").
        response = domain_search_api.suggest_domains(QUERY, limit=3, tlds=[".com"])

        assert response.status_code == 400
        assert response.json()["message"] == "INVALID_TLD_FORMAT"

    def test_suggested_domains_are_available(self, domain_search_api):
        # Docs: suggestions are "available for purchase". Verify with the other endpoint.
        suggestions = domain_search_api.suggest_domains(QUERY, limit=3, tlds=["com"]).json()["suggestions"]

        not_available = [
            s["domain"]
            for s in suggestions
            if not domain_search_api.check_availability(s["domain"]).json()["availability"]["available"]
        ]
        assert not not_available, f"suggested but not available: {not_available}"
