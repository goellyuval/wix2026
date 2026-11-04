"""Global fixtures, shared by API and UI tests."""
import pytest

from src.api.domain_search_api import DomainSearchApi
from src.config import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session")
def domain_search_api(settings):
    # Global, not API-local: UI tests use it to cross-check what the storefront shows.
    api = DomainSearchApi(settings.api_base_url, settings.api_key, settings.account_id)
    yield api
    api.close()
