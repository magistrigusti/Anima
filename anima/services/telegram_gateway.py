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

        await self._call_method(
            method="sendMessage",
            payload=payload,
        )

    async def send_chat_action(
        self,
        chat_id: int,
        action: str = "typing",
    ) -> None:
        await self._call_method(
            method="sendChatAction",
            payload={
                "chat_id": chat_id,
                "action": action,
            },
        )

    async def _call_method(
        self,
        method: str,
        payload: dict[str, object],
    ) -> None:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    self._build_endpoint(method),
                    json=payload,
                )
        except httpx.HTTPError as error:
            raise TelegramGatewayError(
                f"Telegram API недоступен при вызове {method}."
            ) from error

        if response.status_code >= 400:
            raise TelegramGatewayError(
                f"Telegram API вернул HTTP {response.status_code} "
                f"при вызове {method}."
            )

    def _build_endpoint(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self._bot_token}/{method}"
