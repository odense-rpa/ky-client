import httpx
import logging

from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from .hooks import create_response_logging_hook
from .selectors import KYSelectors


class KYClient:
    @property
    def cookies(self) -> dict[str, str]:
        """Get the current active cookies."""
        return self._cookies

    @cookies.setter
    def cookies(self, value: dict[str, str]) -> None:
        """Set the active cookies."""
        self._cookies = value

    def __init__(
        self,
        username: str,
        password: str,
        idp: str,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        response_hook = create_response_logging_hook(logger=self.logger)
        hooks = {"response": [response_hook]}

        self._username = username
        self._password = password
        self._idp = idp
        self._base_url = "https://fs0461.fs.kommunernesydelsessystem.dk/ky-fagsystem"
        self._cookies: dict[str, str] = {}
        self._timeout = 30
        self._client = httpx.Client(
            timeout=self._timeout,
            event_hooks=hooks,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
            },
        )
        self.login()

    def login(self) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                storage_state=None,
                accept_downloads=False,
                ignore_https_errors=True,
            )
            page = context.new_page()
            page.goto(self._base_url)

            try:
                page.select_option(KYSelectors.Login.MUNICIPALITY_SELECT, self._idp)
                page.click(KYSelectors.Login.OK_BUTTON)
            except Exception:
                self.logger.debug("Skipping municipality select")

            try:
                page.wait_for_selector(KYSelectors.Login.USERNAME, timeout=5000)
                page.fill(KYSelectors.Login.USERNAME, self._username)
                page.click(KYSelectors.Login.SUBMIT_BUTTON)
            except Exception:
                self.logger.debug("Skipping username entry")

            try:
                page.wait_for_selector(KYSelectors.Login.PASSWORD, timeout=5000)
                page.fill(KYSelectors.Login.PASSWORD, self._password)
                page.click(KYSelectors.Login.SUBMIT_BUTTON)
            except Exception:
                self.logger.debug("Skipping password entry")

            page.wait_for_selector(KYSelectors.Main.LOGO, timeout=30000)

            cookie_names = ["JSESSIONID", "__RequestVerificationToken_L3J1bnRpbWU1"]
            self._client.cookies = {
                c["name"]: c["value"]
                for c in context.cookies()
                if c.get("name") in cookie_names and c.get("value")
            }

    def _normalize_url(self, endpoint: str) -> str:
        """Ensure the URL is absolute, handling relative URLs."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return urljoin(self._base_url, endpoint)

    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        url = self._normalize_url(endpoint)
        response = self._client.get(url, **kwargs)
        response.raise_for_status()
        return response

    def post(self, endpoint: str, json: dict | None = None, **kwargs) -> httpx.Response:
        url = self._normalize_url(endpoint)
        response = self._client.post(url, json=json, **kwargs)
        response.raise_for_status()
        return response

    def put(self, endpoint: str, json: dict | None = None, **kwargs) -> httpx.Response:
        url = self._normalize_url(endpoint)
        response = self._client.put(url, json=json, **kwargs)
        response.raise_for_status()
        return response

    def patch(self, endpoint: str, json: dict | None = None, **kwargs) -> httpx.Response:
        url = self._normalize_url(endpoint)
        response = self._client.patch(url, json=json, **kwargs)
        response.raise_for_status()
        return response

    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        url = self._normalize_url(endpoint)
        response = self._client.delete(url, **kwargs)
        response.raise_for_status()
        return response
