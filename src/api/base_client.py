import logging

import requests

log = logging.getLogger(__name__)


class BaseClient:
    """Thin wrapper over requests.Session: base URL, default headers, timeout, logging.

    Returns the raw Response so tests can assert on status codes for negative cases.
    """

    TIMEOUT_SECONDS = 15
    LOG_BODY_CHARS = 500

    def __init__(self, base_url: str, headers: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(headers or {})

    def get(self, path: str, params=None) -> requests.Response:
        url = f"{self.base_url}{path}"
        # Headers are never logged: they carry the API key.
        log.info("GET %s params=%s", url, params)
        response = self.session.get(url, params=params, timeout=self.TIMEOUT_SECONDS)
        log.info("-> %s in %.0f ms", response.status_code, response.elapsed.total_seconds() * 1000)
        log.debug("-> body: %s", response.text[: self.LOG_BODY_CHARS])
        return response

    def close(self) -> None:
        self.session.close()
