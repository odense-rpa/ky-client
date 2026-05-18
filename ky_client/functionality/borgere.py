import re

from pathlib import Path
from playwright.sync_api import Page
from ky_client.client import KYClient
from ky_client.selectors import KYSelectors
from ky_client.utils import (
    extract_header_table,
    extract_keyed_table,
    navigate_to,
    naviger_til_borger,
)
from ky_client.models import Indtaegter


class BorgereClient:
    def __init__(self, ky_client: KYClient) -> None:
        self._page: Page = ky_client.page
        self.p_id: str | None = None

    def hent_borgersag(self, cpr: str) -> dict:
        naviger_til_borger(self._page, cpr, timeout=30000)

        match = re.search(r"pId=([a-f0-9\-]*)", self._page.url)
        self.p_id = match.group(1) if match else None

        data = {
            "Personoplysninger": extract_keyed_table(
                self._page, "table#person-oplysninger"
            ),
            "Relationer": extract_keyed_table(
                self._page, "table#person-overblik-relationer"
            ),
            "Livssituation": extract_keyed_table(
                self._page, "table#person-overblik-livssituation"
            ),
            "Ubehandlede opgaver": extract_header_table(
                self._page, "table#ubehandlede-opgaver"
            ),
            "Sagsoversigt": extract_header_table(self._page, "table#sagsoversigt"),
            "Seneste hændelser": extract_header_table(
                self._page, "table#seneste-haendelser"
            ),
        }

        return data

    def hent_ferie_oplysninger(self, cpr: str) -> dict:
        naviger_til_borger(self._page, cpr, timeout=30000)
        navigate_to(
            self._page,
            KYSelectors.Borgere.FERIE,
            KYSelectors.Borgere.FERIEPERIODER_TIL_BEREGNING,
        )

        data = {
            "Ferieperioder til beregning": extract_header_table(
                self._page, KYSelectors.Borgere.FERIEPERIODER_TIL_BEREGNING
            ),
            "Fravær fra Jobcenter": extract_header_table(
                self._page, KYSelectors.Borgere.FRAVÆR_FRA_JOBCENTER
            ),
            "Feriekonto": extract_header_table(
                self._page, KYSelectors.Borgere.FERIEKONTO
            ),
            "Ferieperioder fra Feriekonto": extract_header_table(
                self._page, KYSelectors.Borgere.FERIEPERIODER_FRA_FERIEKONTO
            ),
        }

        return data

    def upload_dokument(self, cpr: str, sagsnøgle: str, file_path: Path) -> None:
        naviger_til_borger(self._page, cpr, timeout=30000)
        self._page.wait_for_selector(KYSelectors.Borgere.SAGSOVERSIGT, timeout=30000)
        sag_row = self._page.locator(
            f"{KYSelectors.Borgere.SAGSOVERSIGT} tbody tr", has_text=sagsnøgle
        ).first

        if sag_row.count() == 0:
            raise ValueError(f"Kunne ikke finde sag med sagsnøgle: {sagsnøgle}")

        row_click_target = sag_row.locator("a, button, td:not(.handlinger)").first
        if row_click_target.count() > 0:
            row_click_target.click()
        else:
            sag_row.click()

        self._page.click(
            "button[onclick=\"loadGenericModal('/entitet/sag/uploadfilesModal');\"]"
        )
        upload_file = file_path.resolve()
        self._page.set_input_files("input.upload-input[name='file']", str(upload_file))
        self._page.click(
            "button.btn-submit-form[data-url='/entitet/sag/submitUploads/']"
        )

    def indtast_indtægter(self, cpr: str, indtaegter: Indtaegter) -> None:
        naviger_til_borger(self._page, cpr, timeout=30000)
        self._page.locator(KYSelectors.Borgere.HANDLINGER_DROPDOWN).click(timeout=30000)
        self._page.locator(KYSelectors.Borgere.HANDLINGER_SUBPROCESSER).click(
            timeout=30000
        )
        self._page.locator(KYSelectors.Borgere.HANDLINGER_SUBPROCESSER_INDTÆGTER).click(
            timeout=30000
        )
        self._page.locator(KYSelectors.Borgere.INDTÆGTER_MANUEL_INDTASTNING).click(
            timeout=30000
        )

        # Fill all possible fields if present, using selectors from KYSelectors.Borgere
        if indtaegter.cvr_se_nummer:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_CVR_SE_NUMMER, indtaegter.cvr_se_nummer
            )
        if indtaegter.virksomhedsnavn:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_VIRKSOMHEDSNAVN,
                indtaegter.virksomhedsnavn,
            )
        if indtaegter.indtaegtstype:
            self._page.wait_for_selector(
                KYSelectors.Borgere.INDTÆGTER_TYPE, timeout=30000
            )
            self._page.select_option(
                KYSelectors.Borgere.INDTÆGTER_TYPE, label=indtaegter.indtaegtstype.value
            )
        if indtaegter.beloeb is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_BELOEB,
                _to_danish_decimal(indtaegter.beloeb),
            )
        if indtaegter.dispositionsdato:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_DISPOSITIONSDATO,
                indtaegter.dispositionsdato,
            )
        if indtaegter.periode_fra:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_PERIODE_FRA, indtaegter.periode_fra
            )
        if indtaegter.periode_til:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_PERIODE_TIL, indtaegter.periode_til
            )
        if indtaegter.pensionsbidrag_eget is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_PENSIONSBIDRAG_EGET,
                _to_danish_decimal(indtaegter.pensionsbidrag_eget),
            )
        if indtaegter.pensionsbidrag_arbejdsgiver is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_PENSIONSBIDRAG_ARBEJDSGIVER,
                _to_danish_decimal(indtaegter.pensionsbidrag_arbejdsgiver),
            )
        if indtaegter.atp_bidrag_eget is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_ATP_BIDRAG_EGET,
                _to_danish_decimal(indtaegter.atp_bidrag_eget),
            )
        if indtaegter.atp_bidrag_arbejdsgiver is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_ATP_BIDRAG_ARBEJDSGIVER,
                _to_danish_decimal(indtaegter.atp_bidrag_arbejdsgiver),
            )
        if indtaegter.am_bidrag is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_AM_BIDRAG,
                _to_danish_decimal(indtaegter.am_bidrag),
            )
        if indtaegter.timer_i_perioden is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_TIMER_I_PERIODEN,
                str(indtaegter.timer_i_perioden),
            )
        if indtaegter.nettoferiepenge is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_NETTOFERIEPENGE,
                _to_danish_decimal(indtaegter.nettoferiepenge),
            )
        if indtaegter.bruttoficerede_nettoferiepenge is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_BRUTTOFICEREDE_NETTOFERIEPENGE,
                _to_danish_decimal(indtaegter.bruttoficerede_nettoferiepenge),
            )
        if indtaegter.bruttoferiepenge_timeloennede is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_BRUTTOFERIEPENGE_TIMELOENNDE,
                _to_danish_decimal(indtaegter.bruttoferiepenge_timeloennede),
            )
        if indtaegter.a_indkomst_som_feriepenge is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_A_INDKOMST_SOM_FERIEPENGE,
                _to_danish_decimal(indtaegter.a_indkomst_som_feriepenge),
            )
        if indtaegter.soegne_og_helligdagsbetaling is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_SOEGNE_OG_HELLIGDAGSBETALING,
                _to_danish_decimal(indtaegter.soegne_og_helligdagsbetaling),
            )
        if indtaegter.fri_kost_og_logi is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_FRI_KOST_OG_LOGI,
                _to_danish_decimal(indtaegter.fri_kost_og_logi),
            )
        if indtaegter.fri_bil is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_FRI_BIL,
                _to_danish_decimal(indtaegter.fri_bil),
            )
        if indtaegter.fri_telefon is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_FRI_TELEFON,
                _to_danish_decimal(indtaegter.fri_telefon),
            )
        if indtaegter.sundhedsforsikring_og_gruppeliv is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_SUNDHEDSFORSIKRING_OG_GRUPPELIV,
                _to_danish_decimal(indtaegter.sundhedsforsikring_og_gruppeliv),
            )
        if indtaegter.skattefri_rejse_og_befordringsgodtgoerelse is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_SKATTEFRI_REJSE_OG_BEFORDRINGSGODTGOERELSE,
                _to_danish_decimal(
                    indtaegter.skattefri_rejse_og_befordringsgodtgoerelse
                ),
            )
        if indtaegter.opsparet_feriefridage is not None:
            self._page.fill(
                KYSelectors.Borgere.INDTÆGTER_OPSPARET_FERIEFRIDAGE,
                _to_danish_decimal(indtaegter.opsparet_feriefridage),
            )
        if indtaegter.ydelsesarter:
            self._page.wait_for_selector(
                KYSelectors.Borgere.INDTÆGTER_YDELSESARTER, timeout=30000
            )
            self._page.select_option(
                KYSelectors.Borgere.INDTÆGTER_YDELSESARTER,
                label=indtaegter.ydelsesarter.value,
            )

        self._page.locator(KYSelectors.Borgere.INDTÆGTER_GEM).click(timeout=30000)
        # GEM is accepted when the indtægter form closes and fields disappear
        self._page.wait_for_selector(
            KYSelectors.Borgere.INDTÆGTER_BELOEB, state="hidden", timeout=30000
        )

        self._page.locator(KYSelectors.Borgere.INDTÆGTER_GODKEND).click(timeout=30000)
        # Wait for Godkend to disappear before clicking Luk to avoid async race
        self._page.wait_for_selector(
            KYSelectors.Borgere.INDTÆGTER_GODKEND, state="detached", timeout=30000
        )
        self._page.locator(KYSelectors.Borgere.INDTÆGTER_LUK).click(timeout=30000)
        self._page.wait_for_selector(
            KYSelectors.Borgere.UBEHANDLEDE_OPGAVER, timeout=30000
        )


def _to_danish_decimal(val: float) -> str:
    # Converts 6509.73 -> '6.509,73' (Danish format)
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
