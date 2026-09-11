import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch

from app.main import app


@pytest.mark.asyncio
async def test_health_check_healthy():
    """Verify /health returns 200 when database connection succeeds."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_check_unhealthy():
    """Verify /health returns 503 when database connection fails."""
    with patch("app.main.check_database_connection", return_value=(False, "Connection timeout")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"
            assert data["detail"] == "Connection timeout"
