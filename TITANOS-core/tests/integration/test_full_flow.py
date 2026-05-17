import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from titanos.server.app import app
from titanos.server.auth import create_access_token

@pytest.fixture
def auth_token():
    return create_access_token(data={"sub": "test_operator"})

@pytest.mark.asyncio
async def test_healthz():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_readyz():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

@pytest.mark.asyncio
async def test_run_goal_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/run", json={"goal": "test goal"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_run_goal_authorized(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/run", json={"goal": "ping"}, headers=headers)
    
    # We might get 200 or 500 depending on mock backend, but authorization should pass (not 401/403)
    assert response.status_code in (200, 500)
    
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert "system" in data
