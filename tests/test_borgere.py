from datetime import datetime
from decimal import Decimal
from ky_client import KYClientManager
from pathlib import Path
from ky_client.models import (
    AfbrydType,
    Journalnotat,
    Indtægter,
    IndtægterType,
    RedigerOpgave,
    Ydelsesarter,
)


def test_hent_borgersag(ky_manager: KYClientManager, test_cpr: str):
    result = ky_manager.borgere.hent_borgersag(test_cpr)
    assert isinstance(result, dict)


def test_hent_ferieoplysninger(ky_manager: KYClientManager, test_cpr: str):
    result = ky_manager.borgere.hent_ferieoplysninger(test_cpr)
    assert isinstance(result, dict)


def test_hent_skatteoplysninger(ky_manager: KYClientManager, test_cpr: str):
    result = ky_manager.borgere.hent_skatteoplysninger(test_cpr)
    assert isinstance(result, dict)


def test_upload_dokument(ky_manager: KYClientManager, test_cpr: str):
    sagsnøgle = "HENV-MJOML7"  # Erstat med en gyldig sagsnøgle for testen
    file_path = (
        Path(__file__).resolve().parents[1] / "Test Upload.txt"
    )  # Erstat med stien til den fil, du vil uploade
    ky_manager.borgere.upload_dokument(test_cpr, sagsnøgle, file_path)


def test_indtast_indtægter(ky_manager: KYClientManager, test_cpr: str):
    indtaegter = Indtægter(
        indtaegtstype=IndtægterType.FERIEPENGE_SELVVALGT,
        beloeb=Decimal("173.84"),
        dispositionsdato="03-06-2026",
        periode_fra="01-06-2026",
        periode_til="30-06-2026",
        timer_i_perioden=0,
        ydelsesarter=Ydelsesarter.HJAELP_TIL_FORSOERGGELSE,
    )

    journalnotat = Journalnotat(
        indhold="Der er modtaget oplysninger fra feriekonto om udbetaling af feriepenge på 173,84 den 03-06-2026. \nDer fremgår ikke aftalt ferie med Jobcenter. \nDer er 15-06-2026 sendt agterskrivelse. \nAgterskrivelsen får virkning som afgørelse fra den 15-06-2026. \nNettoferiepengene 173.84 modregnes i kontanthjælpen i june hvor feriepengene er udbetalt.",
        sagstype="HTF",
        skabelongruppe="KH",
        skabelon="Agterskrivelse - feriepenge",
    )

    ky_manager.borgere.indtast_indtægter(test_cpr, indtaegter, journalnotat)


def test_rediger_opgave(ky_manager: KYClientManager, test_cpr: str):
    ky_manager.borgere.rediger_opgave(
        cpr=test_cpr,
        opgave_id="15740507-cb3b-4c6f-b922-ea90e516577d",
        ændringer=RedigerOpgave(
            opfølgningsopgavetype="KH - Tyra ferie",
            forfalds_dato=datetime.fromordinal(
                datetime.now().toordinal() + 11
            ).strftime("%d-%m-%Y"),
        ),
    )


def test_åbn_opgave(ky_manager: KYClientManager, test_cpr: str):
    initierede_hændelser = ky_manager.borgere.åbn_opgave(
        test_cpr, "1491ae3e-c7f1-4b4b-adf9-646d2a213563"
    )
    assert isinstance(initierede_hændelser, list)


def test_afbryd_opgave(ky_manager: KYClientManager, test_cpr: str):
    ky_manager.borgere.afbryd_opgave(
        test_cpr,
        "1acc834d-b4c5-47f7-a7c2-13b631b52e27",
        AfbrydType.AFBRYD_OG_SLET,
    )


def test_godkend_opgave(ky_manager: KYClientManager, test_cpr: str):
    ky_manager.borgere.godkend_opgave(
        test_cpr,
        "1acc834d-b4c5-47f7-a7c2-13b631b52e27",
    )


def test_luk_borgersag(ky_manager: KYClientManager, test_cpr: str):
    borger_sag = ky_manager.borgere.hent_borgersag(test_cpr)
    ky_manager.borgere.luk_borgersag(borger_sag["pId"])
