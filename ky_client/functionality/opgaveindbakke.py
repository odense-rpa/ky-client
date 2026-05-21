import logging
import re

from ky_client.client import KYClient
from ky_client.selectors import KYSelectors
from ky_client.utils import extract_datatable_all_pages

logger = logging.getLogger(__name__)


class OpgaveindbakkeClient:
    def __init__(self, ky_client: KYClient):
        self._client = ky_client

    def hent_opgaver(self, opgavepakke: str) -> list[dict[str, str]]:
        page = self._client.page
        page.goto(page.url.split("/ky-fagsystem")[0] + "/ky-fagsystem/opgaveindbakke")
        page.click(KYSelectors.Opgaveindbakke.VÆLG_OPGAVEPAKKE)
        previous_total = page.get_attribute(
            "table#ubehandledeTable", "data-total-count"
        )

        # Match option text even when UI appends dynamic count suffix like "(223)".
        option_prefix = re.sub(r"\s*\(\d+\)\s*$", "", opgavepakke).strip()
        option_pattern = re.compile(rf"^{re.escape(option_prefix)}\s*(\(\d+\))?$")

        page.locator("li a .text > span").first.wait_for(state="visible", timeout=10000)
        option_span = page.locator("li a .text > span", has_text=option_pattern).first
        option_text = option_span.inner_text().strip()
        expected_total_match = re.search(r"\((\d+)\)\s*$", option_text)
        expected_total = (
            int(expected_total_match.group(1)) if expected_total_match else None
        )
        option_span.click()
        page.wait_for_selector("table#ubehandledeTable", timeout=30000)

        # Wait until server-side reload has updated table state for the selected package.
        page.wait_for_function(
            """({ prevTotal, expectedTotal }) => {
                const table = document.querySelector('table#ubehandledeTable');
                if (!table) return false;

                const processing = document.querySelector('#ubehandledeTable_processing');
                if (processing) {
                    const style = window.getComputedStyle(processing);
                    if (style.display !== 'none' && style.visibility !== 'hidden') return false;
                }

                const totalCount = Number(table.getAttribute('data-total-count') || '-1');
                if (totalCount < 0) return false;

                if (Number.isFinite(expectedTotal) && expectedTotal >= 0 && totalCount !== expectedTotal) {
                    return false;
                }

                const prev = Number(prevTotal ?? '-1');
                const hasRealRows = table.querySelectorAll('tbody tr.table-row:not(:has(td.dataTables_empty))').length > 0;
                const hasEmptyCell = table.querySelectorAll('tbody td.dataTables_empty').length > 0;

                if (prev >= 0 && totalCount === prev && !hasRealRows && !hasEmptyCell) return false;
                if (totalCount > 0) return hasRealRows || table.querySelector('#ubehandledeTable_next');
                return hasEmptyCell || totalCount === 0;
            }""",
            arg={"prevTotal": previous_total, "expectedTotal": expected_total},
            timeout=30000,
        )

        data = extract_datatable_all_pages(page, "ubehandledeTable")
        # Add fictional column "Opgave-Id" to each row based on "data-opgaveid"
        for row in data:
            row["Opgave-Id"] = row.get("data-opgaveid", "N/A")
        return data
