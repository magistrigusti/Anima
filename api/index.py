import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler
from typing import Any


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

_webhook_service: object | None = None


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._send_json(
            status_code=200,
            payload={
                "ok": True,
                "service": "Anima",
                "telegramWebhook": "/api/telegram",
            },
        )

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/api/telegram":
            self._send_json(
                status_code=404,
                payload={
                    "ok": False,
                    "error": "unknown route",
                },
            )
            return

        try:
            from config import Settings

            settings = Settings.from_env()

            if not self._is_valid_secret(settings.telegram_webhook_secret):
                self._send_json(
                    status_code=401,
                    payload={
                        "ok": False,
                        "error": "invalid webhook secret",
                    },
                )
                return

            update = self._read_update()
            service = _get_webhook_service(settings)

            asyncio.run(service.handle_update(update))

            self._send_json(
                status_code=200,
                payload={
                    "ok": True,
                },
            )
        except Exception:
            logger.exception("Ошибка обработки Telegram webhook.")
            self._send_json(
                status_code=500,
                payload={
                    "ok": False,
                    "error": "webhook processing failed",
                },
            )

    def _is_valid_secret(self, expected_secret: str) -> bool:
        if not expected_secret:
            return True

        incoming_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token")

        return incoming_secret == expected_secret

    def _read_update(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        data = json.loads(raw_body.decode("utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Telegram update должен быть JSON-объектом.")

        return data

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        response_body = json.dumps(payload).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)


def _get_webhook_service(settings: object) -> object:
    global _webhook_service

    if _webhook_service is None:
        from NeuroPsychoBot.services.webhook_dialogue import WebhookDialogueService

        _webhook_service = WebhookDialogueService.from_settings(settings)

    return _webhook_service
