"""Tests for Subject API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_subject(client: AsyncClient):
    payload = {
        "name": "Data Structures & Algorithms",
        "slug": "dsa-core",
        "description": "Essential algorithmic patterns",
        "is_active": True,
    }
    response = await client.post("/api/v1/subjects", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["slug"] == payload["slug"]
    assert "id" in data

    subject_id = data["id"]
    get_res = await client.get(f"/api/v1/subjects/{subject_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == subject_id


@pytest.mark.asyncio
async def test_duplicate_subject_name_rejected(client: AsyncClient):
    payload = {"name": "Java Core", "slug": "java-1"}
    res1 = await client.post("/api/v1/subjects", json=payload)
    assert res1.status_code == 201

    duplicate_name_payload = {"name": "Java Core", "slug": "java-2"}
    res2 = await client.post("/api/v1/subjects", json=duplicate_name_payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_subject_slug_rejected(client: AsyncClient):
    payload = {"name": "DBMS Track", "slug": "dbms-core"}
    res1 = await client.post("/api/v1/subjects", json=payload)
    assert res1.status_code == 201

    duplicate_slug_payload = {"name": "Database Systems", "slug": "dbms-core"}
    res2 = await client.post("/api/v1/subjects", json=duplicate_slug_payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]
