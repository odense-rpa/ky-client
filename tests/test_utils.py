from playwright.sync_api import sync_playwright

from ky_client.utils import extract_header_table


def test_extract_header_table_handles_empty_data_tables():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.set_content("""
            <table id="tabel_udbetalingstotaler_123" class="datatable table dataTable">
                <thead>
                    <tr>
                        <th><span data-textkey="fagsystem.person.udbetalinger.ydelsesart">Ydelsesart</span></th>
                        <th><span data-textkey="fagsystem.person.udbetalinger.periode_fra">Periode fra</span></th>
                        <th><span data-textkey="fagsystem.person.udbetalinger.netto">Nettobeløb</span></th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="3">Ingen resultater fundet</td></tr>
                </tbody>
            </table>
        """)

        result = extract_header_table(page, "table[id^='tabel_udbetalingstotaler_']")

        assert result == []
        browser.close()


def test_extract_header_table_handles_real_rows():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.set_content("""
            <table id="tabel_udbetalingstotaler_123" class="datatable table dataTable">
                <thead>
                    <tr>
                        <th><span data-textkey="fagsystem.person.udbetalinger.ydelsesart">Ydelsesart</span></th>
                        <th><span data-textkey="fagsystem.person.udbetalinger.periode_fra">Periode fra</span></th>
                        <th><span data-textkey="fagsystem.person.udbetalinger.netto">Nettobeløb</span></th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Kontanthjælp</td>
                        <td>01-01-2025</td>
                        <td>2500</td>
                    </tr>
                </tbody>
            </table>
        """)

        result = extract_header_table(page, "table[id^='tabel_udbetalingstotaler_']")

        assert result == [{"Ydelsesart": "Kontanthjælp", "Periode fra": "01-01-2025", "Nettobeløb": "2500"}]
        browser.close()
