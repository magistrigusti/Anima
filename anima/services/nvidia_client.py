from typing import Literal, Sequence, TypedDict

from openai import AsyncOpenAI, OpenAIError

from config import Settings


ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


class NvidiaClientError(Exception):
    """Ошибка обращения к NVIDIA NIM API."""


class NvidiaClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            base_url=settings.nvidia_base_url,
            api_key=settings.nvidia_api_key or "missing-nvidia-api-key",
            timeout=settings.nvidia_timeout_seconds,
        )

    @property
    def is_configured(self) -> bool:
        return bool(self._settings.nvidia_api_key)

    async def create_chat_completion(
        self,
        messages: Sequence[ChatMessage],
    ) -> str:
        if not self.is_configured:
            raise NvidiaClientError("NVIDIA_API_KEY не задан.")

        request_body: dict[str, object] = {
            "model": self._settings.nvidia_model,
            "messages": list(messages),
            "temperature": self._settings.nvidia_temperature,
            "top_p": self._settings.nvidia_top_p,
            "max_tokens": self._settings.nvidia_max_tokens,
        }

        extra_body = self._build_extra_body()

        if extra_body:
            request_body["extra_body"] = extra_body

        try:
            response = await self._client.chat.completions.create(**request_body)
        except OpenAIError as error:
            raise NvidiaClientError(f"NVIDIA API вернул ошибку: {error}") from error

        if not response.choices:
            raise NvidiaClientError("NVIDIA API вернул ответ без choices.")

        content = response.choices[0].message.content

        if not isinstance(content, str) or not content.strip():
            raise NvidiaClientError("NVIDIA API вернул пустой текст.")

        return content.strip()

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