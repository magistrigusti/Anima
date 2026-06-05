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
WAITING_TEXT = "Анима готовит ответ."


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
            return WAITING_TEXT

        return self._prepare_for_telegram(answer)

    def _prepare_for_telegram(self, answer: str) -> str:
        clean_answer = answer.strip()

        if not clean_answer:
            return WAITING_TEXT

        if len(clean_answer) <= TELEGRAM_TEXT_LIMIT:
            return clean_answer

        return f"{clean_answer[:TELEGRAM_TEXT_LIMIT].rstrip()}..."
