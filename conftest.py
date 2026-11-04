"""Global fixtures (used by both API and UI tests) and the quarantine hook."""
from pathlib import Path

import pytest

from src.api.domain_search_api import DomainSearchApi
from src.config import Settings
from src.utils.domains import TAKEN_DOMAIN, random_unregistered_domain

QUARANTINE_FILE = Path(__file__).parent / "tests" / "quarantine.txt"
QUARANTINE_PREFIX = "QUARANTINED"


def _read_quarantine() -> dict[str, str]:
    entries = {}
    for line in QUARANTINE_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            node_id, reason, *_ = (part.strip() for part in line.split("|"))
            entries[node_id] = reason
    return entries


def pytest_collection_modifyitems(items):
    # A quarantined test still runs (so we see when it recovers) but can't fail the suite.
    quarantine = _read_quarantine()
    for item in items:
        if item.nodeid in quarantine:
            item.add_marker(pytest.mark.xfail(strict=False, reason=f"{QUARANTINE_PREFIX}: {quarantine[item.nodeid]}"))


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
