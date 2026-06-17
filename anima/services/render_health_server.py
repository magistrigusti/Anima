import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


logger = logging.getLogger(__name__)

DEFAULT_RENDER_PORT = 10000
HEALTH_PATHS = {"/", "/health"}


class RenderHealthHandler(BaseHTTPRequestHandler):
    server_version = "AnimaHealth/1.0"

    def do_GET(self) -> None:
        if self.path not in HEALTH_PATHS:
            self.send_error(404)
            return

        body = json.dumps(
            {
                "status": "ok",
                "service": "anima",
            },
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: object) -> None:
        logger.info("Render health: " + message_format, *args)


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

    logger.info("Render health server слушает 0.0.0.0:%s", port)


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
