"""API-local fixtures."""
import pytest

from src.utils.domains import TAKEN_DOMAIN, random_unregistered_domain


@pytest.fixture
def taken_domain() -> str:
    return TAKEN_DOMAIN


@pytest.fixture
def free_domain() -> str:
    return random_unregistered_domain()
