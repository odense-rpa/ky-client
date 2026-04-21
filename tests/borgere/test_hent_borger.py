from ky_client import KYClientManager


def test_hent_borgersag(ky_manager: KYClientManager, test_cpr: str):
    result = ky_manager.borgere.hent_borgersag(test_cpr)

    assert isinstance(result, dict)
    assert "Navn" in result["person_oplysninger"], "Personoplysninger mangler 'Navn'"
    assert "CPR" in result["person_oplysninger"], "Personoplysninger mangler 'CPR'"
    assert "ubehandlede_opgaver" in result, "Resultat mangler 'ubehandlede_opgaver'"
    assert isinstance(result["ubehandlede_opgaver"], list), (
        "ubehandlede_opgaver skal være en liste"
    )
