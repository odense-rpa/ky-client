import logging

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from ky_client.selectors import KYSelectors


logger = logging.getLogger(__name__)


def _is_placeholder_header_row(values: list[str]) -> bool:
    """Return True when the row only contains an empty-state placeholder text."""
    if len(values) != 1:
        return False

    value = " ".join(values[0].lower().split())
    exact_placeholders = {
        "no items found",
        "ingen elementer fundet",
        "ingen resultater fundet",
        "ingen fundet",
    }
    if value in exact_placeholders:
        return True

    has_not_found_da = "ingen" in value and "fundet" in value
    has_result_or_items_da = "resultat" in value or "element" in value
    has_not_found_en = "found" in value and ("no" in value or "none" in value)
    return (has_not_found_da and has_result_or_items_da) or has_not_found_en


def extract_keyed_table(page: Page, table_selector: str) -> dict[str, str]:
    """Extract a two-column label/value table into a dict."""
    return page.evaluate(f"""() => {{
		const rows = document.querySelectorAll('{table_selector} tbody tr');
		const result = {{}};
		rows.forEach(row => {{
			const cells = row.querySelectorAll('td:not(.handlinger)');
			if (cells.length >= 2) {{
				result[cells[0].innerText.trim()] = cells[1].innerText.trim();
			}}
		}});
		return result;
	}}""")


def extract_header_table(page: Page, table_selector: str) -> list[dict[str, str]]:
    """Extract a header-based table into a list of dicts."""
    rows: list[dict[str, str]] = page.evaluate(f"""() => {{
		const table = document.querySelector('{table_selector}');
		const isVisibleRow = (row) => {{
			if (!row || row.nodeType !== Node.ELEMENT_NODE) return false;
			const style = window.getComputedStyle(row);
			if (style.display === 'none' || style.visibility === 'hidden') return false;
			return row.offsetParent !== null;
		}};
		const headers = Array.from(table.querySelectorAll('thead th')).map(th => {{
			for (const span of th.querySelectorAll('span[data-textkey]')) {{
				if (!span.closest('ul')) return span.innerText.trim();
			}}
			return null;
		}});
		return Array.from(table.querySelectorAll('tbody tr')).filter(isVisibleRow).map(row => {{
			const cells = row.querySelectorAll('td:not(.handlinger)');
			const obj = {{}};
			cells.forEach((cell, i) => {{
				if (headers[i]) obj[headers[i]] = cell.innerText.trim();
			}});
			return obj;
		}});
	}}""")

    filtered_rows: list[dict[str, str]] = []
    for row in rows:
        values = [str(value).strip() for value in row.values() if str(value).strip()]

        if not values:
            logger.debug(
                "Skipping empty header row in table '%s': %s", table_selector, row
            )
            continue

        if _is_placeholder_header_row(values):
            logger.debug(
                "Skipping placeholder header row in table '%s': %s",
                table_selector,
                row,
            )
            continue

        filtered_rows.append(row)

    return filtered_rows


def extract_datatable_all_pages(page: Page, table_id: str) -> list[dict[str, str]]:
    """Extract all rows from a DataTable across all pages into a list of dicts."""
    table_selector = f"table#{table_id}"
    all_rows: list[dict[str, str]] = []

    def _wait_ready(timeout_ms: int = 5000) -> None:
        try:
            page.wait_for_selector(f"{table_selector} tbody", timeout=timeout_ms)
        except PlaywrightError as e:
            if page.is_closed():
                raise RuntimeError(f"Page was closed while waiting for table '{table_id}'") from e
            raise
        
        try:
            page.wait_for_function(
                """(id) => {
					const processing = document.querySelector(`#${id}_processing`);
					if (!processing) return true;
					const style = window.getComputedStyle(processing);
					return style.display === 'none' || style.visibility === 'hidden';
				}""",
                arg=table_id,
                timeout=timeout_ms,
            )
        except PlaywrightError as e:
            if page.is_closed():
                raise RuntimeError(f"Page was closed while waiting for table '{table_id}' to be ready") from e
            logger.warning(f"Table '{table_id}' processing check timed out, continuing anyway")

    _wait_ready()

    def _read_page_state() -> dict:
        return page.evaluate(
            """(id) => {
				const table = document.querySelector(`table#${id}`);
				if (!table) return { rows: [], page: 0, nextDisabled: true, totalCount: 0 };

				const headers = Array.from(table.querySelectorAll('thead th')).map((th) => {
					const span = th.querySelector('span[data-textkey]');
					const text = span ? span.innerText.trim() : th.innerText.trim();
					return text || null;
				});

				const rowElements = Array.from(table.querySelectorAll('tbody tr.table-row'))
					.filter((row) => !row.querySelector('td.dataTables_empty'));

				const rows = rowElements.map((row) => {
					const cells = Array.from(row.querySelectorAll('td')).map((td) => td.innerText.trim());
					const obj = {};
					cells.forEach((cell, i) => {
						if (headers[i]) obj[headers[i]] = cell;
					});
					// Add data-opgaveid attribute to the row object
					obj['data-opgaveid'] = row.getAttribute('data-opgaveid') || 'N/A';
					return obj;
				});

				const page = Number(table.getAttribute('data-page') || '0');
				const totalCount = Number(table.getAttribute('data-total-count') || '0');

				const next = document.querySelector(`#${id}_next`) || document.querySelector(`#${id}_paginate a.paginate_button.next`);
				const nextDisabled = !next || next.classList.contains('disabled') || next.getAttribute('aria-disabled') === 'true';

				return { rows, page, nextDisabled, totalCount };
			}""",
            arg=table_id,
        )

    table_meta = page.evaluate(
        """(id) => {
			const table = document.querySelector(`table#${id}`);
			if (!table) return { totalCount: 0, pageSize: 10 };
			return {
				totalCount: Number(table.getAttribute('data-total-count') || '0'),
				pageSize: Math.max(1, Number(table.getAttribute('data-page-size') || '10')),
			};
		}""",
        arg=table_id,
    )
    expected_pages = max(
        1,
        (int(table_meta["totalCount"]) + int(table_meta["pageSize"]) - 1)
        // int(table_meta["pageSize"]),
    )

    for page_index in range(expected_pages):
        state = _read_page_state()

        if page_index == 0 and not state["rows"] and int(state["totalCount"]) > 0:
            _wait_ready(timeout_ms=3000)
            state = _read_page_state()

        page_rows = [
            row
            for row in state["rows"]
            if not _is_placeholder_header_row(
                [str(value).strip() for value in row.values() if str(value).strip()]
            )
        ]
        all_rows.extend(page_rows)

        if page_index >= expected_pages - 1 or state["nextDisabled"]:
            break

        next_button = page.locator(f"#{table_id}_next")
        if next_button.count() == 0:
            next_button = page.locator(f"#{table_id}_paginate a.paginate_button.next")

        next_class = next_button.get_attribute("class") or ""
        next_aria_disabled = (next_button.get_attribute("aria-disabled") or "").lower()
        if "disabled" in next_class or next_aria_disabled == "true":
            break

        try:
            next_button.click(timeout=5000)
        except PlaywrightTimeoutError:
            logger.debug(
                "Next button click timed out for table '%s'; stopping pagination.",
                table_id,
            )
            break
        try:
            page.wait_for_function(
                """({ id, previous }) => {
					const table = document.querySelector(`table#${id}`);
					if (!table) return false;
					return Number(table.getAttribute('data-page') || '0') !== previous;
				}""",
                arg={"id": table_id, "previous": int(state["page"])},
                timeout=4000,
            )
        except PlaywrightTimeoutError:
            logger.debug(
                "Timed out waiting for data-page change in table '%s'; continuing after readiness wait.",
                table_id,
            )
        _wait_ready(timeout_ms=3000)

    logger.debug("Extracted %d total rows from table '%s'", len(all_rows), table_id)
    return all_rows


def navigate_to(
    page: Page,
    nav_selector: str,
    wait_for_selector: str,
    timeout: int = 30000,
) -> None:
    """Click a nav tab and wait for the expected content to appear."""
    page.click(nav_selector)
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except PlaywrightError:
        logger.debug("Page did not reach networkidle state, continuing anyway")
    
    try:
        page.wait_for_selector(wait_for_selector, timeout=timeout)
    except PlaywrightError as e:
        if page.is_closed():
            raise RuntimeError(f"Page was closed while waiting for '{wait_for_selector}'") from e
        raise


def naviger_til_borger(page: Page, cpr: str, timeout: int = 30000) -> None:
    """Search for a borgersag by CPR and wait for overblik to be ready."""
    search_input = page.locator(KYSelectors.Main.TOP_SEARCH)
    search_input.wait_for(state="visible", timeout=timeout)
    search_input.click()
    search_input.fill(cpr)
    search_input.press("Enter")

    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except PlaywrightError:
        logger.debug("Page did not reach networkidle state after search, continuing anyway")

    try:
        page.wait_for_selector(KYSelectors.Borgere.PERSON_OPLYSNINGER, timeout=timeout)
    except PlaywrightTimeoutError:
        logger.warning(
            "CPR search did not navigate on first Enter for CPR '%s'. Retrying.",
            cpr,
        )
        search_input.click()
        search_input.fill(cpr)
        page.keyboard.press("Enter")
        
        try:
            page.wait_for_load_state("networkidle", timeout=timeout)
        except PlaywrightError:
            logger.debug("Page did not reach networkidle state after retry, continuing anyway")
        
        try:
            page.wait_for_selector(KYSelectors.Borgere.PERSON_OPLYSNINGER, timeout=timeout)
        except PlaywrightError as e:
            if page.is_closed():
                raise RuntimeError(f"Page was closed while searching for CPR '{cpr}'") from e
            raise
    except PlaywrightError as e:
        if page.is_closed():
            raise RuntimeError(f"Page was closed while searching for CPR '{cpr}'") from e
        raise
