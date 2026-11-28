"""Transactional email abstraction backed by Cloudflare Email Sending (send_email)."""

from dataclasses import dataclass
import logging
from typing import Any, Protocol

from fastapi import Request

from config import get_settings

logger = logging.getLogger("email_service")


@dataclass(frozen=True)
class EmailMessage:
    """Transactional email payload with both plain-text and HTML bodies."""

    to: str
    subject: str
    text: str
    html: str


class EmailSender(Protocol):
    """Interface for sending transactional emails."""

    async def send(self, message: EmailMessage) -> None:
        """Deliver `message` to its recipient."""
        ...


class CloudflareEmailSender:
    """Adapter over Cloudflare Workers `send_email` binding (`env.EMAIL`)."""

    def __init__(self, binding: Any, sender_email: str, sender_name: str) -> None:
        self._binding = binding
        self._sender_email = sender_email
        self._sender_name = sender_name

    async def send(self, message: EmailMessage) -> None:
        payload: dict[str, Any] = {
            "to": message.to,
            "from": {"email": self._sender_email, "name": self._sender_name},
            "subject": message.subject,
            "text": message.text,
            "html": message.html,
        }
        try:
            import js
            from pyodide.ffi import to_js

            js_payload = to_js(payload, dict_converter=js.Object.fromEntries)
            await self._binding.send(js_payload)
        except ImportError:
            await self._binding.send(payload)


class ConsoleEmailSender:
    """Fallback sender for local development when `env.EMAIL` is not bound."""

    async def send(self, message: EmailMessage) -> None:
        logger.warning(
            "[DEV EMAIL] To=%s | Subject=%s\n%s",
            message.to,
            message.subject,
            message.text,
        )


class InMemoryEmailSender:
    """In-memory email capture used in automated tests."""

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> None:
        self.sent.append(message)


async def get_email_sender(request: Request) -> EmailSender:
    """Resolve Cloudflare `env.EMAIL` binding in Workers, else ConsoleEmailSender."""
    env = request.scope.get("env")
    email_binding = getattr(env, "EMAIL", None) if env is not None else None
    if email_binding is not None:
        settings = get_settings(request)
        return CloudflareEmailSender(
            binding=email_binding,
            sender_email=settings.email_from,
            sender_name=settings.email_from_name,
        )
    return ConsoleEmailSender()
