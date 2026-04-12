"""Integration tests for API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from search_angel.api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestRootEndpoint:
    async def test_root(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Search Angel"
        assert "version" in data
        assert data["status"] == "running"


class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient):
        """Health endpoint should return even if backends are unavailable."""
        response = await client.get("/api/v1/health")
        # May be 200 with degraded status if backends are down
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "components" in data
        assert "uptime_seconds" in data


class TestSearchEndpoint:
    async def test_search_requires_query(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/search",
            json={"query": ""},
        )
        assert response.status_code == 422  # Validation error

    async def test_search_validates_limit(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/search",
            json={"query": "test", "limit": 0},
        )
        assert response.status_code == 422

    async def test_search_validates_mode(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/search",
            json={"query": "test", "mode": "invalid_mode"},
        )
        assert response.status_code == 422


class TestIngestionEndpoint:
    async def test_ingestion_requires_api_key(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/index",
            json={
                "url": "https://example.com",
                "title": "Test",
                "content": "Test content",
            },
        )
        assert response.status_code == 422  # Missing X-API-Key header

    async def test_ingestion_rejects_invalid_key(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/index",
            json={
                "url": "https://example.com",
                "title": "Test",
                "content": "Test content",
            },
            headers={"X-API-Key": "invalid_key"},
        )
        # Will be 401 or 503 depending on config
        assert response.status_code in (401, 503)


class TestPrivacyHeaders:
    async def test_no_tracking_header(self, client: AsyncClient):
        response = await client.get("/")
        assert response.headers.get("x-privacy") == "no-tracking"

    async def test_no_cache_header(self, client: AsyncClient):
        response = await client.get("/")
        cache_control = response.headers.get("cache-control", "")
        assert "no-store" in cache_control

    async def test_request_id_present(self, client: AsyncClient):
        response = await client.get("/")
        assert "x-request-id" in response.headers

    async def test_no_set_cookie(self, client: AsyncClient):
        response = await client.get("/")
        assert "set-cookie" not in response.headers
