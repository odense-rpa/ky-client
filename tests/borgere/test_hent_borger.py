from ky_client import KYClientManager


def test_hent_borgersag(ky_manager: KYClientManager, test_cpr: str):
    result = ky_manager.borgere.hent_borgersag(test_cpr)

    assert result is not None, "Ingen data returneret"
    assert isinstance(result, dict), "Resultat skal være en dict"
    assert "Navn" in result, "Personoplysninger mangler 'Navn'"
    assert "CPR" in result, "Personoplysninger mangler 'CPR'"
