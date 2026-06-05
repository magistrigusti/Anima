import argparse
import sys
from pathlib import Path
from urllib.parse import urljoin

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import Settings


TELEGRAM_API_BASE_URL = "https://api.telegram.org"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Управление Telegram webhook для Anima.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set")
    set_parser.add_argument(
        "base_url",
        help="https://anima-couch.vercel.app/api/telegram/",
    )

    subparsers.add_parser("delete")
    subparsers.add_parser("info")

    args = parser.parse_args()
    settings = Settings.from_env()
    settings.validate_for_bot()

    if args.command == "set":
        set_webhook(settings=settings, base_url=args.base_url)
        return

    if args.command == "delete":
        delete_webhook(settings=settings)
        return

    if args.command == "info":
        show_webhook_info(settings=settings)


def set_webhook(settings: Settings, base_url: str) -> None:
    webhook_url = build_webhook_url(base_url)
    payload: dict[str, object] = {
        "url": webhook_url,
        "allowed_updates": ["message"],
        "drop_pending_updates": True,
    }

    if settings.telegram_webhook_secret:
        payload["secret_token"] = settings.telegram_webhook_secret

    response = call_telegram(
        settings=settings,
        method="setWebhook",
        payload=payload,
    )

    print(f"Webhook установлен: {webhook_url}")
    print(response)


def delete_webhook(settings: Settings) -> None:
    response = call_telegram(
        settings=settings,
        method="deleteWebhook",
        payload={
            "drop_pending_updates": False,
        },
    )

    print("Webhook удален.")
    print(response)


def show_webhook_info(settings: Settings) -> None:
    response = call_telegram(
        settings=settings,
        method="getWebhookInfo",
        payload={},
    )

    print(response)


def call_telegram(
    settings: Settings,
    method: str,
    payload: dict[str, object],
) -> dict[str, object]:
    endpoint = f"{TELEGRAM_API_BASE_URL}/bot{settings.telegram_bot_token}/{method}"

    with httpx.Client(timeout=20.0) as client:
        response = client.post(endpoint, json=payload)

    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError("Telegram API вернул неожиданный формат.")

    return data


def build_webhook_url(base_url: str) -> str:
    normalized_base_url = base_url.strip().rstrip("/") + "/"

    return urljoin(normalized_base_url, "api/telegram")


if __name__ == "__main__":
    main()
