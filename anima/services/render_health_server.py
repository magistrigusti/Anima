import asyncio
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from urllib.parse import urlsplit

from config import Settings
from anima.services.webhook_dialogue import WebhookDialogueService


logger = logging.getLogger(__name__)

DEFAULT_RENDER_PORT = 10000
HEALTH_PATHS = {"/", "/health"}
TELEGRAM_WEBHOOK_PATH = "/api/telegram"

_webhook_service: WebhookDialogueService | None = None
_webhook_service_lock = Lock()


class RenderHealthHandler(BaseHTTPRequestHandler):
    server_version = "AnimaRender/1.0"

    def do_GET(self) -> None:
        if self._request_path not in HEALTH_PATHS:
            self._send_json(
                status_code=404,
                payload={
                    "ok": False,
                    "error": "unknown route",
                },
            )
            return

        self._send_json(
            status_code=200,
            payload={
                "ok": True,
                "status": "ok",
                "service": "anima",
            },
        )

    def do_POST(self) -> None:
        if self._request_path != TELEGRAM_WEBHOOK_PATH:
            self._send_json(
                status_code=404,
                payload={
                    "ok": False,
                    "error": "unknown route",
                },
            )
            return

        try:
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
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
            self._send_json(
                status_code=400,
                payload={
                    "ok": False,
                    "error": "invalid telegram update",
                },
            )
            return

        self._send_json(
            status_code=200,
            payload={
                "ok": True,
            },
        )

        Thread(
            target=_process_telegram_update,
            args=(settings, update),
            name="telegram-webhook-update",
            daemon=True,
        ).start()

    @property
    def _request_path(self) -> str:
        return urlsplit(self.path).path.rstrip("/") or "/"

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

    def _send_json(
        self,
        status_code: int,
        payload: dict[str, object],
    ) -> None:
        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: object) -> None:
        logger.info("Render HTTP: " + message_format, *args)


def start_render_health_server() -> None:
    port = _read_render_port()

    if port is None:
        return

    server = ThreadingHTTPServer(("0.0.0.0", port), RenderHealthHandler)
    thread = Thread(
        target=server.serve_forever,
        name="render-health-server",
        daemon=True,
    )
    thread.start()

    logger.info("Render HTTP server слушает 0.0.0.0:%s", port)


def _process_telegram_update(
    settings: Settings,
    update: dict[str, object],
) -> None:
    try:
        asyncio.run(_get_webhook_service(settings).handle_update(update))
    except Exception:
        logger.exception("Ошибка фоновой обработки Telegram webhook.")


def _get_webhook_service(settings: Settings) -> WebhookDialogueService:
    global _webhook_service

    with _webhook_service_lock:
        if _webhook_service is None:
            _webhook_service = WebhookDialogueService.from_settings(settings)

    return _webhook_service


def _read_render_port() -> int | None:
    raw_port = os.getenv("PORT")

    if raw_port is None:
        return None

    try:
        port = int(raw_port)
    except ValueError:
        logger.warning(
            "Некорректный PORT для Render: %s. Использую порт %s.",
            raw_port,
            DEFAULT_RENDER_PORT,
        )
        return DEFAULT_RENDER_PORT

    if 1 <= port <= 65535:
        return port

    logger.warning(
        "PORT для Render вне допустимого диапазона: %s. Использую порт %s.",
        raw_port,
        DEFAULT_RENDER_PORT,
    )

    return DEFAULT_RENDER_PORT
