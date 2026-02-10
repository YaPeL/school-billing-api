import pytest

from app.api.health import health
from app.main import app


@pytest.mark.smoke
@pytest.mark.anyio
async def test_health_ok() -> None:
    assert await health() == {"status": "ok"}


@pytest.mark.smoke
def test_fastapi_skeleton_wired() -> None:
    paths = {route.path for route in app.routes}
    assert app.title == "Mattilda Backend"
    assert "/health" in paths
    assert "/auth/login" in paths
