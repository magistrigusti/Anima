import httpx


class TelegramGatewayError(Exception):
    """Ошибка отправки сообщения через Telegram Bot API."""


class TelegramGateway:
    def __init__(self, bot_token: str) -> None:
        self._bot_token = bot_token

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> None:
        payload: dict[str, object] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }

        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    self._send_message_endpoint,
                    json=payload,
                )
        except httpx.HTTPError as error:
            raise TelegramGatewayError(
                "Telegram API недоступен при отправке сообщения."
            ) from error

        if response.status_code >= 400:
            raise TelegramGatewayError(
                f"Telegram API вернул HTTP {response.status_code}."
            )

    @property
    def _send_message_endpoint(self) -> str:
        return f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
