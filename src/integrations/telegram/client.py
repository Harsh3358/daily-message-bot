"""Async Telegram Bot API Client.

Async HTTP Concepts:
- `httpx.AsyncClient`: Unlike `requests` (which is synchronous and halts the entire
  Python process during socket read/write), `httpx.AsyncClient` uses non-blocking
  async socket operations. When awaiting `client.post()`, control is yielded back
  to the event loop so that incoming HTTP requests and other tasks continue executing.
"""
import logging
from typing import Any, Dict, Optional
import httpx
from src.core.config import get_settings
from src.integrations.telegram.exceptions import (
    TelegramAPIException,
    TelegramBadRequestException,
    TelegramForbiddenException,
    TelegramRateLimitException,
)

logger = logging.getLogger(__name__)


class TelegramClient:
    """Asynchronous client for interacting with the Telegram Bot API."""

    def __init__(self, bot_token: Optional[str] = None, timeout: float = 15.0) -> None:
        settings = get_settings()
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily initialize an AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False,
    ) -> int:
        """Send a text message to a Telegram chat/group.

        Returns:
            The message_id (int) assigned by Telegram.
        """
        client = await self._get_client()
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        try:
            response = await client.post(url, json=payload)
            data = response.json()
        except httpx.RequestError as exc:
            logger.error("Network error communicating with Telegram API: %s", exc)
            raise TelegramAPIException(f"Network error communicating with Telegram: {exc}") from exc
        except Exception as exc:
            logger.error("Unexpected error calling Telegram API: %s", exc)
            raise TelegramAPIException(f"Unexpected error calling Telegram API: {exc}") from exc

        if not response.is_success or not data.get("ok"):
            status_code = response.status_code
            error_code = data.get("error_code", status_code)
            description = data.get("description", "Unknown Telegram API error")

            logger.warning(
                "Telegram API error: status=%s, code=%s, description=%s",
                status_code,
                error_code,
                description,
            )

            if status_code == 403 or error_code == 403:
                raise TelegramForbiddenException(
                    f"Bot was blocked, kicked, or lacks permission in chat {chat_id}: {description}",
                    status_code=403,
                    error_code=403,
                    description=description,
                )
            elif status_code == 429 or error_code == 429:
                retry_after = data.get("parameters", {}).get("retry_after", 5)
                raise TelegramRateLimitException(
                    f"Telegram rate limit exceeded: retry after {retry_after}s",
                    retry_after=retry_after,
                    status_code=429,
                    description=description,
                )
            elif status_code == 400 or error_code == 400:
                raise TelegramBadRequestException(
                    f"Bad request to Telegram API: {description}",
                    status_code=400,
                    error_code=400,
                    description=description,
                )
            else:
                raise TelegramAPIException(
                    f"Telegram API request failed: {description}",
                    status_code=status_code,
                    error_code=error_code,
                    description=description,
                )

        return data["result"]["message_id"]

    async def get_me(self) -> Dict[str, Any]:
        """Fetch bot info to verify credentials."""
        client = await self._get_client()
        url = f"{self.base_url}/getMe"
        try:
            response = await client.get(url)
            data = response.json()
            if not data.get("ok"):
                raise TelegramAPIException(f"Invalid bot token: {data.get('description')}")
            return data["result"]
        except httpx.RequestError as exc:
            raise TelegramAPIException(f"Network error calling getMe: {exc}") from exc

    async def get_chat(self, chat_id: int) -> Dict[str, Any]:
        """Fetch chat details to verify group access."""
        client = await self._get_client()
        url = f"{self.base_url}/getChat"
        try:
            response = await client.post(url, json={"chat_id": chat_id})
            data = response.json()
            if not data.get("ok"):
                raise TelegramAPIException(f"Failed to get chat info: {data.get('description')}")
            return data["result"]
        except httpx.RequestError as exc:
            raise TelegramAPIException(f"Network error calling getChat: {exc}") from exc
