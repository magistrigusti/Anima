import logging
from time import monotonic
from types import ModuleType
from typing import cast

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from anima.services.anima_coach import AnimaCoach, WAITING_TEXT
from anima.services.dialogue_memory import DialogueMemory


logger = logging.getLogger(__name__)

COACH_KEY = "anima_coach"
MEMORY_KEY = "anima_memory"
TEXTS_KEY = "anima_texts"
WAIT_NOTICE_KEY = "anima_wait_notice"
WAIT_NOTICE_INTERVAL_SECONDS = 120.0


def register_dialog_handlers(
    application: Application,
    coach: AnimaCoach,
    memory: DialogueMemory,
    texts: ModuleType,
) -> None:
    application.bot_data[COACH_KEY] = coach
    application.bot_data[MEMORY_KEY] = memory
    application.bot_data[TEXTS_KEY] = texts

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("privacy", privacy))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    user_name = "друг"

    if update.effective_user and update.effective_user.first_name:
        user_name = update.effective_user.first_name

    texts = _get_texts(context)

    await message.reply_text(texts.START_TEXT.format(name=user_name))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    await message.reply_text(_get_texts(context).HELP_TEXT)


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    await message.reply_text(_get_texts(context).PRIVACY_TEXT)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None or update.effective_user is None:
        return

    _get_memory(context).clear(update.effective_user.id)

    await message.reply_text(_get_texts(context).RESET_TEXT)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None or update.effective_user is None:
        return

    user_text = message.text.strip() if message.text else ""
    texts = _get_texts(context)

    if not user_text:
        await message.reply_text(texts.EMPTY_TEXT)
        return

    await context.bot.send_chat_action(
        chat_id=message.chat_id,
        action=ChatAction.TYPING,
    )

    user_id = update.effective_user.id
    memory = _get_memory(context)
    coach = _get_coach(context)
    history = memory.get_history(user_id)

    answer = await coach.answer(user_text=user_text, history=history)

    if _is_repeated_wait_notice(
        application=context.application,
        user_id=user_id,
        answer=answer,
    ):
        return

    memory.remember_user_message(user_id=user_id, text=user_text)
    memory.remember_assistant_message(user_id=user_id, text=answer)

    await message.reply_text(answer)


async def handle_error(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    logger.exception("Ошибка Telegram handler", exc_info=context.error)

    if not isinstance(update, Update) or update.effective_message is None:
        return

    await update.effective_message.reply_text(_get_texts(context).ERROR_TEXT)


def _get_coach(context: ContextTypes.DEFAULT_TYPE) -> AnimaCoach:
    return cast(AnimaCoach, context.application.bot_data[COACH_KEY])


def _get_memory(context: ContextTypes.DEFAULT_TYPE) -> DialogueMemory:
    return cast(DialogueMemory, context.application.bot_data[MEMORY_KEY])


def _get_texts(context: ContextTypes.DEFAULT_TYPE) -> ModuleType:
    return cast(ModuleType, context.application.bot_data[TEXTS_KEY])


def _is_repeated_wait_notice(
    application: Application,
    user_id: int,
    answer: str,
) -> bool:
    if answer != WAITING_TEXT:
        return False

    notices = application.bot_data.setdefault(WAIT_NOTICE_KEY, {})
    last_notice_at = notices.get(user_id)
    now = monotonic()

    if last_notice_at is not None and now - last_notice_at < WAIT_NOTICE_INTERVAL_SECONDS:
        return True

    notices[user_id] = now

    return False
