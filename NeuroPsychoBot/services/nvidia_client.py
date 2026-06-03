from typing import Literal, Sequence, TypedDict

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

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

        try:
            stream = await self._client.chat.completions.create(
                model=self._settings.nvidia_model,
                messages=list(messages),
                temperature=self._settings.nvidia_temperature,
                top_p=self._settings.nvidia_top_p,
                max_tokens=self._settings.nvidia_max_tokens,
                extra_body=self._build_extra_body(),
                stream=True,
            )
        except (APIConnectionError, APIStatusError, APITimeoutError) as error:
            raise NvidiaClientError(f"NVIDIA API недоступен: {error}") from error

        answer_parts: list[str] = []

        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content

                if content:
                    answer_parts.append(content)
        except (APIConnectionError, APIStatusError, APITimeoutError) as error:
            raise NvidiaClientError(f"NVIDIA stream оборвался: {error}") from error

        answer = "".join(answer_parts).strip()

        if not answer:
            raise NvidiaClientError("NVIDIA API вернул пустой ответ.")

        return answer

    def _build_extra_body(self) -> dict[str, object]:
        if not self._settings.nvidia_enable_thinking:
            return {}

        return {
            "chat_template_kwargs": {
                "enable_thinking": True,
            },
            "reasoning_budget": self._settings.nvidia_reasoning_budget,
        }
