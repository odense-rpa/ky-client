import pytest
import os

from ky_client import KYClientManager


@pytest.fixture(scope="session")
def ky_manager() -> KYClientManager:
    """Fixture that provides a logged-in KYClientManager for tests."""
    username = os.getenv("KY_USER") or ""
    password = os.getenv("KY_PASSWORD") or ""
    idp = os.getenv("KY_IDP") or ""

    assert username

    manager = KYClientManager(username, password, idp)
    assert manager._client._client.cookies.get("JSESSIONID"), (
        "Login failed - JSESSIONID cookie not set"
    )
    return manager


@pytest.fixture(scope="session")
def test_cpr() -> str:
    cpr = os.getenv("TEST_CPR") or ""
    assert cpr, "TEST_CPR environment variable not set"
    return cpr
