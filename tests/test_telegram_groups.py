"""Tests for TelegramGroup API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_list_telegram_group(client: AsyncClient):
    # 1. Create subject
    subject_res = await client.post(
        "/api/v1/subjects",
        json={"name": "System Design", "slug": "system-design"},
    )
    assert subject_res.status_code == 201
    subject_id = subject_res.json()["id"]

    # 2. Register group
    group_payload = {
        "subject_id": subject_id,
        "chat_id": -1001122334455,
        "group_title": "Distributed Systems Enthusiasts",
        "is_active": True,
    }
    group_res = await client.post("/api/v1/telegram-groups", json=group_payload)
    assert group_res.status_code == 201
    group_data = group_res.json()
    assert group_data["chat_id"] == group_payload["chat_id"]
    assert group_data["group_title"] == group_payload["group_title"]
    assert group_data["subject_id"] == subject_id

    # 3. List groups
    list_res = await client.get("/api/v1/telegram-groups")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_duplicate_chat_id_rejected(client: AsyncClient):
    subject_res = await client.post(
        "/api/v1/subjects",
        json={"name": "DevOps", "slug": "devops"},
    )
    subject_id = subject_res.json()["id"]

    group_payload = {
        "subject_id": subject_id,
        "chat_id": -1009999999999,
        "group_title": "Kubernetes Club",
        "is_active": True,
    }
    res1 = await client.post("/api/v1/telegram-groups", json=group_payload)
    assert res1.status_code == 201

    # Attempt to register duplicate chat_id
    res2 = await client.post("/api/v1/telegram-groups", json=group_payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]
