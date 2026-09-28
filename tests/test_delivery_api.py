"""Tests for Deliveries API endpoints."""
from unittest.mock import AsyncMock
import pytest
from httpx import AsyncClient
from src.api.dependencies import get_telegram_client
from src.integrations.telegram.client import TelegramClient
from src.main import app


@pytest.mark.asyncio
async def test_trigger_delivery_api(client: AsyncClient):
    # Setup mock telegram client for FastAPI dependency override
    mock_telegram = AsyncMock(spec=TelegramClient)
    mock_telegram.send_message.return_value = 54321
    app.dependency_overrides[get_telegram_client] = lambda: mock_telegram

    try:
        # 1. Create subject
        sub_res = await client.post("/api/v1/subjects", json={"name": "Cloud", "slug": "cloud"})
        sub_id = sub_res.json()["id"]

        # 2. Register group
        await client.post(
            "/api/v1/telegram-groups",
            json={"subject_id": sub_id, "chat_id": -1008888888888, "group_title": "Cloud Devs"},
        )

        # 3. Create problem for today
        import datetime
        today_str = datetime.date.today().isoformat()
        await client.post(
            "/api/v1/problems",
            json={
                "subject_id": sub_id,
                "title": "S3 Consistency Model",
                "topic": "Storage",
                "difficulty": "EASY",
                "content": "Explain strong read-after-write consistency in S3.",
                "scheduled_date": today_str,
            },
        )

        # 4. Trigger delivery via API
        trigger_res = await client.post("/api/v1/deliveries/trigger", json={})
        assert trigger_res.status_code == 200
        summary = trigger_res.json()
        assert summary["successful_count"] == 1
        assert summary["skipped_count"] == 0

        # 5. Query delivery logs via API
        logs_res = await client.get("/api/v1/deliveries/logs")
        assert logs_res.status_code == 200
        logs_data = logs_res.json()
        assert logs_data["total"] == 1
        assert logs_data["items"][0]["status"] == "SUCCESS"
        assert logs_data["items"][0]["telegram_message_id"] == 54321

        # 6. Re-trigger delivery -> should be skipped (idempotency!)
        retrigger_res = await client.post("/api/v1/deliveries/trigger", json={})
        assert retrigger_res.status_code == 200
        re_summary = retrigger_res.json()
        assert re_summary["successful_count"] == 0
        assert re_summary["skipped_count"] == 1

    finally:
        app.dependency_overrides.pop(get_telegram_client, None)
