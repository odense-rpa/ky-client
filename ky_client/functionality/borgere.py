from playwright.sync_api import Page
from ky_client.client import KYClient
from ky_client.selectors import KYSelectors


class BorgereClient:
    def __init__(self, ky_client: KYClient) -> None:
        self._page: Page = ky_client.page

    def hent_borgersag(self, cpr: str) -> dict[str, str]:
        """
        Søg efter en borgersag via CPR-nummer og returner personoplysninger.

        Args:
            cpr: CPR-nummer på borgeren

        Returns:
            Dict med personoplysninger (label → værdi)
        """
        self._page.fill(KYSelectors.Main.TOP_SEARCH, cpr)
        self._page.press(KYSelectors.Main.TOP_SEARCH, "Enter")
        self._page.wait_for_selector(KYSelectors.Borgere.PERSON_OPLYSNINGER, timeout=30000)

        return self._page.evaluate("""() => {
            const rows = document.querySelectorAll('table#person-oplysninger tbody tr');
            const result = {};
            rows.forEach(row => {
                const cells = row.querySelectorAll('td:not(.handlinger)');
                if (cells.length >= 2) {
                    result[cells[0].innerText.trim()] = cells[1].innerText.trim();
                }
            });
            return result;
        }""")
