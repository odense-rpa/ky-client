import random

from ky_client import KYClientManager
from pathlib import Path
from ky_client.models import (
    AfbrydType,
    Indtægter,
    IndtægterType,
    RedigerOpgave,
    Ydelsesarter,
)


def test_hent_borgersag(ky_manager: KYClientManager, test_cpr: str):
    result = ky_manager.borgere.hent_borgersag(test_cpr)
    assert isinstance(result, dict)


def test_hent_ferie_oplysninger(ky_manager: KYClientManager, test_cpr: str):
    result = ky_manager.borgere.hent_ferie_oplysninger(test_cpr)
    assert isinstance(result, dict)


def test_upload_dokument(ky_manager: KYClientManager, test_cpr: str):
    sagsnøgle = "HENV-MJOML7"  # Erstat med en gyldig sagsnøgle for testen
    file_path = (
        Path(__file__).resolve().parents[1] / "Test Upload.txt"
    )  # Erstat med stien til den fil, du vil uploade
    ky_manager.borgere.upload_dokument(test_cpr, sagsnøgle, file_path)


def test_indtast_indtægter(ky_manager: KYClientManager, test_cpr: str):
    indtaegter = Indtægter(
        indtaegtstype=random.choice(list(IndtægterType)),
        beloeb=round(random.uniform(1000, 10000), 2),
        dispositionsdato="31-05-2026",
        periode_fra="01-05-2026",
        periode_til="31-05-2026",
        ydelsesarter=Ydelsesarter.HJAELP_TIL_FORSOERGGELSE,
    )
    ky_manager.borgere.indtast_indtægter(test_cpr, indtaegter)


def test_rediger_opgave(ky_manager: KYClientManager, test_cpr: str):
    ændringer = RedigerOpgave(
        prioritet="Høj",
        forfalds_dato="31-05-2026",
        opfølgningsopgavetype="x. Lars J.",
        sagsbehandler="larje",
        frekvens="Ugenligt",
    )
    ky_manager.borgere.rediger_opgave(
        test_cpr, "1acc834d-b4c5-47f7-a7c2-13b631b52e27", ændringer
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
