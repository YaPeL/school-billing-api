import pytest

from app.api.health import health


@pytest.mark.smoke
@pytest.mark.anyio
async def test_health_ok() -> None:
    assert await health() == {"status": "ok"}
