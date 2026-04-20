from playwright.sync_api import Page
from ky_client.client import KYClient
from ky_client.selectors import KYSelectors


def _extract_keyed_table(page: Page, table_id: str) -> dict[str, str]:
    """Extract a two-column label/value table into a dict."""
    return page.evaluate(f"""() => {{
        const rows = document.querySelectorAll('table#{table_id} tbody tr');
        const result = {{}};
        rows.forEach(row => {{
            const cells = row.querySelectorAll('td:not(.handlinger)');
            if (cells.length >= 2) {{
                result[cells[0].innerText.trim()] = cells[1].innerText.trim();
            }}
        }});
        return result;
    }}""")


def _extract_header_table(page: Page, table_id: str) -> list[dict[str, str]]:
    """Extract a header-based table into a list of dicts."""
    return page.evaluate(f"""() => {{
        const table = document.querySelector('table#{table_id}');
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => {{
            for (const span of th.querySelectorAll('span[data-textkey]')) {{
                if (!span.closest('ul')) return span.innerText.trim();
            }}
            return '';
        }}).filter(h => h);
        return Array.from(table.querySelectorAll('tbody tr')).map(row => {{
            const cells = row.querySelectorAll('td:not(.handlinger)');
            const obj = {{}};
            cells.forEach((cell, i) => {{
                if (headers[i]) obj[headers[i]] = cell.innerText.trim();
            }});
            return obj;
        }});
    }}""")


class BorgereClient:
    def __init__(self, ky_client: KYClient) -> None:
        self._page: Page = ky_client.page

    def hent_borgersag(self, cpr: str) -> dict:
        """
        Søg efter en borgersag via CPR-nummer og returner personoplysninger,
        sagsoversigt og ubehandlede opgaver.

        Args:
            cpr: CPR-nummer på borgeren

        Returns:
            Dict med 'person_oplysninger' (dict), 'sagsoversigt' (list) og
            'ubehandlede_opgaver' (list)
        """
        self._page.fill(KYSelectors.Main.TOP_SEARCH, cpr)
        self._page.press(KYSelectors.Main.TOP_SEARCH, "Enter")
        self._page.wait_for_selector(KYSelectors.Borgere.PERSON_OPLYSNINGER, timeout=30000)

        return {
            "person_oplysninger": _extract_keyed_table(self._page, "person-oplysninger"),
            "sagsoversigt": _extract_header_table(self._page, "sagsoversigt"),
            "ubehandlede_opgaver": _extract_header_table(self._page, "ubehandlede-opgaver"),
            "livssituation": _extract_keyed_table(self._page, "person-overblik-livssituation"),
        }
