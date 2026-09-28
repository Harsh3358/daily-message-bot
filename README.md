# DailyProblemBot 🤖

A production-style backend service built with **FastAPI**, **SQLAlchemy 2.x (Async)**, **PostgreSQL**, **Pydantic v2**, **APScheduler**, and the **Telegram Bot API**.

The application automates delivering daily subject-specific technical problems (e.g., Java, DSA, DBMS) to designated Telegram groups every morning, with strict delivery idempotency and full audit logging.

---

## 🏗️ Architectural Overview

The project adheres to a clean, **Layered Architecture**:

```
[ FastAPI Controller ] ──▶ [ Service Layer ] ──▶ [ Repository Layer ] ──▶ [ PostgreSQL DB ]
                                  │
[ APScheduler Job ]    ───────────┘
                                  │
                                  ▼
                         [ Telegram Client ] ──▶ [ Telegram Bot API ]
```

### Architectural Principles:
- **Controller Layer (`src/api/`)**: Manages HTTP request parsing, Pydantic validation, status codes, and delegates directly to Services.
- **Service Layer (`src/services/`)**: Orchestrates business rules, ensures domain integrity, calls Repositories for data persistence, and invokes the Telegram client.
- **Repository Layer (`src/repositories/`)**: Encapsulates data access using SQLAlchemy 2.x `AsyncSession` and ORM models.
- **Telegram Client (`src/integrations/telegram/`)**: Async non-blocking HTTP client (`httpx.AsyncClient`) for posting messages to Telegram and handling Telegram-specific status codes (e.g., 403 Forbidden, 429 Too Many Requests).
- **Background Automation (`src/scheduler/`)**: Embedded `AsyncIOScheduler` executing the morning problem dispatch directly via `DeliveryService`.
- **Separation of Concerns**: Database models (`src/models/`) and Pydantic DTO schemas (`src/schemas/`) are kept in separate packages with zero circular dependencies.

---

## ⚡ Asynchronous Architecture

This application is built from the ground up on Python's **`asyncio` event loop**:
- **Non-blocking Database I/O**: Queries are dispatched via `asyncpg` and SQLAlchemy 2.0 async sessions (`await session.execute(...)`), freeing the worker thread while waiting on PostgreSQL.
- **Non-blocking Outbound HTTP**: Telegram messages are posted using `httpx.AsyncClient` (`await client.post(...)`), ensuring multiple group dispatches do not stall HTTP request handling.
- **APScheduler in the Event Loop**: `AsyncIOScheduler` runs jobs natively inside the event loop without spawning unnecessary OS threads.

---

## 🗄️ Database Entities & Idempotency

### Entities
1. **Subject**: Track/topic category (e.g., Java, DSA, DBMS) with unique `name` and `slug`.
2. **Problem**: Scheduled daily problem containing `title`, `topic`, `difficulty` (`EASY`, `MEDIUM`, `HARD`), `content`, `scheduled_date`, and optional `reference_url`.
   - Constrained by `UNIQUE (subject_id, scheduled_date)`.
3. **TelegramGroup**: Registered Telegram group with 64-bit `chat_id`, display title, and `is_active` status.
4. **DeliveryLog**: Audit log recording every delivery attempt (`PENDING`, `SUCCESS`, `FAILED`, `SKIPPED`), `telegram_message_id`, and `sent_at`.

### Idempotency Guarantee
The delivery uniqueness rule is strictly:
$$\text{problem\_id} + \text{telegram\_group\_id} + \text{delivery\_date}$$

- **No Duplicates**: A group will never receive the same problem more than once on the same date.
- **No Daily Restriction**: A Telegram group is **NOT** restricted to only one problem per day. If multiple different problems are dispatched on the same date, each will be delivered.
- **Enforced at Database & Service Level**:
  - Service pre-flight check skips already-delivered problems.
  - Partial unique index guarantees database integrity:
    ```sql
    CREATE UNIQUE INDEX uq_successful_problem_delivery
    ON delivery_logs (problem_id, telegram_group_id, delivery_date)
    WHERE status = 'SUCCESS';
    ```

---

## 🚀 Quickstart & Setup

### Option 1: Run with Docker Compose (Recommended)

1. Clone repository and copy environment settings:
   ```bash
   cp .env.example .env
   ```
2. Configure `TELEGRAM_BOT_TOKEN` in `.env`.
3. Start the application and PostgreSQL database:
   ```bash
   docker-compose up --build -d
   ```
4. Access the API documentation at:
   - **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option 2: Local Development Setup

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and configure your database credentials and Telegram bot token:
   ```ini
   DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/daily_problem_bot"
   TELEGRAM_BOT_TOKEN="your_token_from_botfather"
   SCHEDULER_CRON_HOUR=8
   SCHEDULER_CRON_MINUTE=0
   APP_TIMEZONE="Asia/Kolkata"
   ```

4. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start the FastAPI application**:
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

---

## 🧪 Running the Test Suite

The test suite runs against an isolated async in-memory SQLite database (`aiosqlite`):

```bash
python -m pytest -v
```

All 13 integration and unit tests cover:
- Idempotency checks (skipping duplicates for the same problem + group + date).
- Multi-problem delivery to the same group on the same date.
- Auto-deactivation of groups when the bot is kicked (HTTP 403).
- HTML escaping and safe length formatting for Telegram messages.
- Full CRUD APIs with validation rules and unique constraints.

---

## 📡 API Reference & Examples

### 1. Create a Subject
```bash
curl -X POST http://localhost:8000/api/v1/subjects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Structures & Algorithms",
    "slug": "dsa",
    "description": "Essential computer science algorithms and data structures"
  }'
```

### 2. Create a Daily Problem
```bash
curl -X POST http://localhost:8000/api/v1/problems \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "<SUBJECT_UUID>",
    "title": "Two Sum",
    "topic": "Arrays & Hash Maps",
    "difficulty": "EASY",
    "content": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
    "scheduled_date": "2026-09-24",
    "reference_url": "https://leetcode.com/problems/two-sum"
  }'
```

### 3. Register a Telegram Group
```bash
curl -X POST http://localhost:8000/api/v1/telegram-groups \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "<SUBJECT_UUID>",
    "chat_id": -1001234567890,
    "group_title": "Daily DSA Practice Group"
  }'
```

### 4. Trigger Delivery On-Demand (Manual / Admin)
```bash
curl -X POST http://localhost:8000/api/v1/deliveries/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_date": "2026-09-24",
    "force": false
  }'
```

### 5. Inspect Delivery Audit Logs
```bash
curl -X GET "http://localhost:8000/api/v1/deliveries/logs?page=1&page_size=20"
```

### 6. Health Check
```bash
curl -X GET http://localhost:8000/api/v1/health
```

---

## 🛡️ Edge Cases Handled

| Edge Case | Solution |
| :--- | :--- |
| **Bot Kicked from Group (HTTP 403)** | Caught by `TelegramClient`; `DeliveryService` immediately marks `telegram_groups.is_active = FALSE` and records a `FAILED` log. |
| **Telegram HTML Entity Parsing** | `src/integrations/telegram/formatter.py` escapes `<`, `>`, and `&` in titles and content using `html.escape`. |
| **Message Exceeding 4096 Characters** | Automatically truncated at safe boundary (`3200` chars) with an indicator directing the user to the reference URL. |
| **Duplicate Delivery Attempts** | Checked via `exists_successful_delivery` query and guaranteed by partial unique index `uq_successful_problem_delivery`. |
| **Missing Content for Scheduled Date** | Safely logged with informative warnings; scheduler continues to other subjects without failing. |
| **Rate Limit Pacing** | Async pacing (`asyncio.sleep(0.05)`) between consecutive group deliveries. |
