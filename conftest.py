"""Global fixtures: used by both API and UI tests."""
import pytest

from src.api.domain_search_api import DomainSearchApi
from src.config import Settings
from src.utils.domains import TAKEN_DOMAIN, random_unregistered_domain


@pytest.fixture(scope="session")
def settings() -> Settings:
    # Session: .env is read once. Lazy: a run that never needs the key never asks for it.
    return Settings.from_env()


@pytest.fixture(scope="session")
def domain_search_api(settings):
    # Session: one HTTP session for the whole run. Global: UI tests use it to cross-check the storefront.
    api = DomainSearchApi(settings.api_base_url, settings.api_key, settings.account_id)
    yield api
    api.close()


@pytest.fixture
def taken_domain() -> str:
    return TAKEN_DOMAIN


@pytest.fixture
def free_domain() -> str:
    # Function scope: a fresh random name per test, so no test depends on another's data.
    return random_unregistered_domain()
