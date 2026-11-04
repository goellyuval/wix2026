import requests

from src.api.base_client import BaseClient


class DomainSearchApi(BaseClient):
    """Wix public Domain Search API v2.

    Docs: https://dev.wix.com/docs/api-reference/account-level/domains/domain-search/introduction
    api_key / account_id are optional so auth tests can build a client with either one missing.
    """

    def __init__(self, base_url: str, api_key: str | None = None, account_id: str | None = None):
        headers = {}
        if api_key:
            headers["Authorization"] = api_key
        if account_id:
            headers["wix-account-id"] = account_id
        super().__init__(base_url, headers)

    def check_availability(self, domain: str) -> requests.Response:
        return self.get("/domain-search/v2/check-domain-availability", params={"domain": domain})

    def suggest_domains(self, query: str, limit: int | None = None, tlds: list[str] | None = None) -> requests.Response:
        params = {"query": query}
        if limit is not None:
            params["paging.limit"] = limit
        if tlds:
            params["tlds"] = tlds  # requests repeats the key: tlds=com&tlds=net
        return self.get("/domain-search/v2/suggest-domains", params=params)
