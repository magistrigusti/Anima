from typing import Literal, Sequence, TypedDict

import httpx

from config import Settings


ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


class NvidiaClientError(Exception):
    """Ошибка обращения к внешней нейросети."""


class NvidiaClient:
    """
    Имя класса оставлено старым, чтобы не переписывать весь проект.
    Внутри теперь используется Anthropic Messages API.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self._settings.anthropic_api_key)

    async def create_chat_completion(
        self,
        messages: Sequence[ChatMessage],
    ) -> str:
        if not self.is_configured:
            raise NvidiaClientError("ANTHROPIC_API_KEY не задан.")

        system_prompt, dialogue_messages = self._split_messages(messages)

        payload: dict[str, object] = {
            "model": self._settings.anthropic_model,
            "max_tokens": self._settings.anthropic_max_tokens,
            "temperature": self._settings.nvidia_temperature,
            "system": system_prompt,
            "messages": dialogue_messages,
        }

        headers = {
            "x-api-key": self._settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        endpoint = f"{self._settings.anthropic_base_url.rstrip('/')}/v1/messages"

        try:
            async with httpx.AsyncClient(timeout=self._settings.anthropic_timeout_seconds) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as error:
            raise NvidiaClientError(f"Anthropic API недоступен: {error}") from error

        if response.status_code >= 400:
            raise NvidiaClientError(
                f"Anthropic API вернул HTTP {response.status_code}: {response.text[:900]}"
            )

        data = response.json()
        answer = self._extract_answer(data)

        if not answer:
            raise NvidiaClientError("Anthropic API вернул пустой ответ.")

        return answer

    def _split_messages(
        self,
        messages: Sequence[ChatMessage],
    ) -> tuple[str, list[dict[str, str]]]:
        system_parts: list[str] = []
        dialogue_messages: list[dict[str, str]] = []

        for message in messages:
            role = message["role"]
            content = message["content"]

            if role == "system":
                system_parts.append(content)
                continue

            dialogue_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return "\n\n".join(system_parts), dialogue_messages

    def _extract_answer(self, data: object) -> str:
        if not isinstance(data, dict):
            return ""

        content = data.get("content")

        if not isinstance(content, list):
            return ""

        answer_parts: list[str] = []

        for block in content:
            if not isinstance(block, dict):
                continue

            if block.get("type") != "text":
                continue

            text = block.get("text")

            if isinstance(text, str) and text.strip():
                answer_parts.append(text.strip())

        return "\n\n".join(answer_parts).strip()