import pytest

from src.api.domain_search_api import DomainSearchApi

pytestmark = pytest.mark.api


class TestAuthentication:
    """Docs: 'This call requires an account level API key'. In practice the API answers anyway."""

    @pytest.mark.xfail(strict=True, reason="Auth is not enforced: request succeeds. See FINDINGS.md")
    @pytest.mark.parametrize(
        "use_key, use_account_id",
        [
            pytest.param(False, False, id="no_key_no_account"),
            pytest.param(False, True, id="no_key"),
            pytest.param(True, False, id="no_account_id"),
        ],
    )
    def test_missing_credentials_are_rejected(self, settings, taken_domain, use_key, use_account_id):
        api = DomainSearchApi(
            settings.api_base_url,
            api_key=settings.api_key if use_key else None,
            account_id=settings.account_id if use_account_id else None,
        )

        response = api.check_availability(taken_domain)

        assert response.status_code in (401, 403)

    @pytest.mark.xfail(strict=True, reason="Auth is not enforced: a fake key succeeds. See FINDINGS.md")
    def test_invalid_key_is_rejected(self, settings, taken_domain):
        api = DomainSearchApi(settings.api_base_url, api_key="not-a-real-key", account_id=settings.account_id)

        response = api.check_availability(taken_domain)

        assert response.status_code in (401, 403)
