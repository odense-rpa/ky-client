from ky_client import KYClientManager


def test_login(ky_manager: KYClientManager):
    assert "JSESSIONID" in ky_manager._client._client.cookies, (
        "Login failed - JSESSIONID cookie not set"
    )
