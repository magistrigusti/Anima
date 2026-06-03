import logging
from types import ModuleType

from config import Settings
from NeuroPsychoBot.services.anima_coach import AnimaCoach
from NeuroPsychoBot.services.dialogue_memory import DialogueMemory
from NeuroPsychoBot.services.nvidia_client import NvidiaClient
from NeuroPsychoBot.services.telegram_gateway import TelegramGateway
from NeuroPsychoBot.texts.catalog import get_texts


logger = logging.getLogger(__name__)


class WebhookDialogueService:
    def __init__(
        self,
        coach: AnimaCoach,
        memory: DialogueMemory,
        telegram: TelegramGateway,
        texts: ModuleType,
    ) -> None:
        self._coach = coach
        self._memory = memory
        self._telegram = telegram
        self._texts = texts

    @classmethod
    def from_settings(cls, settings: Settings) -> "WebhookDialogueService":
        settings.validate_for_webhook()

        texts = get_texts(settings.anima_language)
        nvidia_client = NvidiaClient(settings)
        coach = AnimaCoach(nvidia_client=nvidia_client, texts=texts)
        memory = DialogueMemory(max_messages=settings.history_messages_limit)
        telegram = TelegramGateway(bot_token=settings.telegram_bot_token)

        return cls(
            coach=coach,
            memory=memory,
            telegram=telegram,
            texts=texts,
        )

    async def handle_update(self, update: dict[str, object]) -> None:
        message = self._extract_message(update)

        if message is None:
            return

        text = self._extract_text(message)

        if not text:
            return

        chat_id = self._extract_chat_id(message)
        user_id = self._extract_user_id(message)
        message_id = self._extract_message_id(message)

        if chat_id is None or user_id is None:
            logger.warning("Telegram update без chat_id или user_id.")
            return

        answer = await self._build_answer(
            user_id=user_id,
            user_text=text,
            first_name=self._extract_first_name(message),
        )

        await self._telegram.send_message(
            chat_id=chat_id,
            text=answer,
            reply_to_message_id=message_id,
        )

    async def _build_answer(
        self,
        user_id: int,
        user_text: str,
        first_name: str,
    ) -> str:
        command = self._extract_command(user_text)

        if command == "start":
            return self._texts.START_TEXT.format(name=first_name or "друг")

        if command == "help":
            return self._texts.HELP_TEXT

        if command == "privacy":
            return self._texts.PRIVACY_TEXT

        if command == "reset":
            self._memory.clear(user_id)
            return self._texts.RESET_TEXT

        history = self._memory.get_history(user_id)
        answer = await self._coach.answer(user_text=user_text, history=history)

        self._memory.remember_user_message(user_id=user_id, text=user_text)
        self._memory.remember_assistant_message(user_id=user_id, text=answer)

        return answer

    def _extract_message(
        self,
        update: dict[str, object],
    ) -> dict[str, object] | None:
        message = update.get("message")

        if isinstance(message, dict):
            return message

        return None

    def _extract_text(self, message: dict[str, object]) -> str:
        text = message.get("text")

        if isinstance(text, str):
            return text.strip()

        return ""

    def _extract_chat_id(self, message: dict[str, object]) -> int | None:
        chat = message.get("chat")

        if not isinstance(chat, dict):
            return None

        chat_id = chat.get("id")

        if isinstance(chat_id, int):
            return chat_id

        return None

    def _extract_user_id(self, message: dict[str, object]) -> int | None:
        user = message.get("from")

        if not isinstance(user, dict):
            return None

        user_id = user.get("id")

        if isinstance(user_id, int):
            return user_id

        return None

    def _extract_message_id(self, message: dict[str, object]) -> int | None:
        message_id = message.get("message_id")

        if isinstance(message_id, int):
            return message_id

        return None

    def _extract_first_name(self, message: dict[str, object]) -> str:
        user = message.get("from")

        if not isinstance(user, dict):
            return "друг"

        first_name = user.get("first_name")

        if isinstance(first_name, str) and first_name.strip():
            return first_name.strip()

        return "друг"

    def _extract_command(self, user_text: str) -> str:
        first_part = user_text.strip().split(maxsplit=1)[0].lower()

        if not first_part.startswith("/"):
            return ""

        command = first_part[1:].split("@", maxsplit=1)[0]

        return command
