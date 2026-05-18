from ky_client import KYClientManager


def test_hent_opgaver(ky_manager: KYClientManager):
    result = ky_manager.opgaveindbakke.hent_opgaver("KH - 07. Feriepenge")
    assert isinstance(result, list)
    assert len(result) > 10, f"Expected more than 10 tasks, got {len(result)}"
