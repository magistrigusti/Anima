import logging
from types import ModuleType
from typing import Sequence

from anima.services.nvidia_client import (
    ChatMessage,
    NvidiaClient,
    NvidiaClientError,
)
from anima.services.safety import has_crisis_signal


logger = logging.getLogger(__name__)

TELEGRAM_TEXT_LIMIT = 3600
NVIDIA_ERROR_TEXT = "Нейросеть NVIDIA сейчас не вернула ответ."


class AnimaCoach:
    def __init__(self, nvidia_client: NvidiaClient, texts: ModuleType) -> None:
        self._nvidia_client = nvidia_client
        self._texts = texts

    async def answer(
        self,
        user_text: str,
        history: Sequence[ChatMessage],
    ) -> str:
        clean_text = user_text.strip()

        if has_crisis_signal(clean_text):
            return self._texts.CRISIS_TEXT

        messages: list[ChatMessage] = [
            {
                "role": "system",
                "content": self._texts.SYSTEM_PROMPT,
            },
            *history,
            {
                "role": "user",
                "content": clean_text,
            },
        ]

        try:
            answer = await self._nvidia_client.create_chat_completion(messages)
        except NvidiaClientError as error:
            logger.warning("NVIDIA ответ недоступен: %s", error)

            return self._prepare_error_for_telegram(error)

        return self._prepare_for_telegram(answer)

    def _prepare_for_telegram(self, answer: str) -> str:
        clean_answer = answer.strip()

        if not clean_answer:
            return NVIDIA_ERROR_TEXT

        if len(clean_answer) <= TELEGRAM_TEXT_LIMIT:
            return clean_answer

        return f"{clean_answer[:TELEGRAM_TEXT_LIMIT].rstrip()}..."

    def _prepare_error_for_telegram(self, error: NvidiaClientError) -> str:
        clean_error = str(error).strip()

        if not clean_error:
            return NVIDIA_ERROR_TEXT

        return (
            f"{NVIDIA_ERROR_TEXT}\n\n"
            f"Техническая причина: {clean_error[:900]}"
        )