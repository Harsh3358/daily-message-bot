"""Tests for Problem API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_problem_with_topic_and_difficulty(client: AsyncClient):
    # 1. Create subject
    subject_res = await client.post(
        "/api/v1/subjects",
        json={"name": "Java Mastery", "slug": "java-mastery"},
    )
    assert subject_res.status_code == 201
    subject_id = subject_res.json()["id"]

    # 2. Create problem
    problem_payload = {
        "subject_id": subject_id,
        "title": "Reverse a Linked List",
        "topic": "Linked Lists",
        "difficulty": "EASY",
        "content": "Given the head of a singly linked list, reverse the list, and return the reversed list.",
        "scheduled_date": "2026-09-24",
        "reference_url": "https://leetcode.com/problems/reverse-linked-list",
        "is_active": True,
    }
    prob_res = await client.post("/api/v1/problems", json=problem_payload)
    assert prob_res.status_code == 201
    prob_data = prob_res.json()
    assert prob_data["title"] == problem_payload["title"]
    assert prob_data["topic"] == "Linked Lists"
    assert prob_data["difficulty"] == "EASY"
    assert prob_data["scheduled_date"] == "2026-09-24"


@pytest.mark.asyncio
async def test_duplicate_problem_on_same_date_rejected(client: AsyncClient):
    # 1. Create subject
    sub = await client.post("/api/v1/subjects", json={"name": "DSA", "slug": "dsa"})
    sub_id = sub.json()["id"]

    # 2. Create first problem on 2026-09-25
    p1 = {
        "subject_id": sub_id,
        "title": "Two Sum",
        "topic": "Arrays",
        "difficulty": "EASY",
        "content": "Given nums array and target integer...",
        "scheduled_date": "2026-09-25",
    }
    res1 = await client.post("/api/v1/problems", json=p1)
    assert res1.status_code == 201

    # 3. Create second problem for same subject on same date -> should be 409 Conflict
    p2 = {
        "subject_id": sub_id,
        "title": "3Sum",
        "topic": "Two Pointers",
        "difficulty": "MEDIUM",
        "content": "Given an integer array nums, return all the triplets...",
        "scheduled_date": "2026-09-25",
    }
    res2 = await client.post("/api/v1/problems", json=p2)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]
