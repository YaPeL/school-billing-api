import pytest

from app.api.health import health


@pytest.mark.smoke
def test_health_ok() -> None:
    assert health() == {"status": "ok"}
