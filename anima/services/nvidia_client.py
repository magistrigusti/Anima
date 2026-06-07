from dataclasses import dataclass
from typing import Literal, Sequence, TypedDict

import httpx

from config import Settings


ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


class NvidiaClientError(Exception):
    """Ошибка обращения к NVIDIA NIM API."""


@dataclass(frozen=True)
class NvidiaRequestTarget:
    label: str
    api_key: str
    model: str


class NvidiaClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self._build_targets())

    async def create_chat_completion(
        self,
        messages: Sequence[ChatMessage],
    ) -> str:
        targets = self._build_targets()

        if not targets:
            raise NvidiaClientError("NVIDIA_API_KEY не задан.")

        errors: list[str] = []

        for target in targets:
            try:
                return await self._send_chat_completion(
                    messages=messages,
                    target=target,
                )
            except NvidiaClientError as error:
                errors.append(str(error))

        raise NvidiaClientError(" | ".join(errors))

    async def _send_chat_completion(
        self,
        messages: Sequence[ChatMessage],
        target: NvidiaRequestTarget,
    ) -> str:
        payload = self._build_payload(messages, target.model)
        headers = self._build_headers(target.api_key)
        endpoint = self._build_endpoint()

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.nvidia_timeout_seconds,
            ) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as error:
            error_text = str(error).strip() or error.__class__.__name__

            raise NvidiaClientError(
                f"{target.label} {target.model}: "
                f"NVIDIA API недоступен: {error_text}"
            ) from error

        if response.status_code >= 400:
            raise NvidiaClientError(
                f"{target.label} {target.model}: "
                f"NVIDIA API вернул HTTP {response.status_code}: "
                f"{response.text[:900]}"
            )

        return self._extract_answer(response.json())

    def _build_targets(self) -> list[NvidiaRequestTarget]:
        targets: list[NvidiaRequestTarget] = []

        if self._settings.nvidia_api_key:
            targets.append(
                NvidiaRequestTarget(
                    label="primary",
                    api_key=self._settings.nvidia_api_key,
                    model=self._settings.nvidia_model,
                )
            )

        if self._settings.nvidia_fallback_api_key:
            fallback_target = NvidiaRequestTarget(
                label="fallback",
                api_key=self._settings.nvidia_fallback_api_key,
                model=self._settings.nvidia_fallback_model,
            )

            if not self._has_same_target(targets, fallback_target):
                targets.append(fallback_target)

        return targets

    def _has_same_target(
        self,
        targets: Sequence[NvidiaRequestTarget],
        candidate: NvidiaRequestTarget,
    ) -> bool:
        for target in targets:
            if (
                target.api_key == candidate.api_key
                and target.model == candidate.model
            ):
                return True

        return False

    def _build_payload(
        self,
        messages: Sequence[ChatMessage],
        model: str,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": model,
            "messages": list(messages),
            "temperature": self._settings.nvidia_temperature,
            "top_p": self._settings.nvidia_top_p,
            "max_tokens": self._settings.nvidia_max_tokens,
        }

        extra_body = self._build_extra_body()

        if extra_body:
            payload.update(extra_body)

        return payload

    def _build_extra_body(self) -> dict[str, object]:
        if not self._settings.nvidia_enable_thinking:
            return {}

        if self._settings.nvidia_reasoning_budget <= 0:
            return {}

        return {
            "chat_template_kwargs": {
                "enable_thinking": True,
            },
            "reasoning_budget": self._settings.nvidia_reasoning_budget,
        }

    def _build_headers(self, api_key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _build_endpoint(self) -> str:
        base_url = self._settings.nvidia_base_url.rstrip("/")

        return f"{base_url}/chat/completions"

    def _extract_answer(self, data: object) -> str:
        if not isinstance(data, dict):
            raise NvidiaClientError("NVIDIA API вернул не JSON-объект.")

        choices = data.get("choices")

        if not isinstance(choices, list) or not choices:
            raise NvidiaClientError("NVIDIA API вернул ответ без choices.")

        first_choice = choices[0]

        if not isinstance(first_choice, dict):
            raise NvidiaClientError("NVIDIA API вернул неправильный choice.")

        message = first_choice.get("message")

        if not isinstance(message, dict):
            raise NvidiaClientError("NVIDIA API вернул choice без message.")

        content = message.get("content")

        if not isinstance(content, str) or not content.strip():
            raise NvidiaClientError("NVIDIA API вернул пустой текст.")

        return content.strip()
