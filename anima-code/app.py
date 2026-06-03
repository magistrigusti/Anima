import logging

from telegram.ext import Application, ApplicationBuilder

from config import Settings
from NeuroPsychoBot.handlers.dialog import handle_error, register_dialog_handlers
from NeuroPsychoBot.services.anima_coach import AnimaCoach
from NeuroPsychoBot.services.dialogue_memory import DialogueMemory
from NeuroPsychoBot.services.nvidia_client import NvidiaClient
from NeuroPsychoBot.texts.catalog import get_texts


def create_application() -> Application:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    settings = Settings.from_env()
    settings.validate_for_bot()

    text_pack = get_texts(settings.anima_language)
    nvidia_client = NvidiaClient(settings)
    coach = AnimaCoach(nvidia_client=nvidia_client, texts=text_pack)
    memory = DialogueMemory(max_messages=settings.history_messages_limit)

    application = ApplicationBuilder().token(settings.telegram_bot_token).build()

    register_dialog_handlers(
        application=application,
        coach=coach,
        memory=memory,
        texts=text_pack,
    )
    application.add_error_handler(handle_error)

    return application
