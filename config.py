import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


DEFAULT_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "nvidia/nemotron-3-super-120b-a12b"


def _read_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _read_float(name: str, default: float) -> float:
    value = _read_env(name)

    if not value:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def _read_int(name: str, default: int) -> int:
    value = _read_env(name)

    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _read_bool(name: str, default: bool) -> bool:
    value = _read_env(name).lower()

    if not value:
        return default

    return value in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_webhook_secret: str
    nvidia_api_key: str
    nvidia_base_url: str
    nvidia_model: str
    nvidia_temperature: float
    nvidia_top_p: float
    nvidia_max_tokens: int
    nvidia_timeout_seconds: float
    nvidia_enable_thinking: bool
    nvidia_reasoning_budget: int
    history_messages_limit: int
    anima_language: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_bot_token=_read_env("TELEGRAM_BOT_TOKEN"),
            telegram_webhook_secret=_read_env("TELEGRAM_WEBHOOK_SECRET"),
            nvidia_api_key=_read_env("NVIDIA_API_KEY"),
            nvidia_base_url=_read_env("NVIDIA_BASE_URL", DEFAULT_NVIDIA_BASE_URL),
            nvidia_model=_read_env("NVIDIA_MODEL", DEFAULT_NVIDIA_MODEL),
            nvidia_temperature=_read_float("NVIDIA_TEMPERATURE", 1.0),
            nvidia_top_p=_read_float("NVIDIA_TOP_P", 0.95),
            nvidia_max_tokens=_read_int("NVIDIA_MAX_TOKENS", 16384),
            nvidia_timeout_seconds=_read_float("NVIDIA_TIMEOUT_SECONDS", 45.0),
            nvidia_enable_thinking=_read_bool("NVIDIA_ENABLE_THINKING", True),
            nvidia_reasoning_budget=_read_int("NVIDIA_REASONING_BUDGET", 16384),
            history_messages_limit=_read_int("ANIMA_HISTORY_MESSAGES_LIMIT", 10),
            anima_language=_read_env("ANIMA_LANGUAGE", "ru").lower(),
        )

    def validate_for_bot(self) -> None:
        if not self.telegram_bot_token:
            raise RuntimeError(
                "Не найден TELEGRAM_BOT_TOKEN. "
                "Добавь токен Telegram-бота в файл .env."
            )

    def validate_for_webhook(self) -> None:
        self.validate_for_bot()

        if not self.nvidia_api_key:
            raise RuntimeError(
                "Не найден NVIDIA_API_KEY. "
                "Добавь ключ NVIDIA API в переменные окружения."
            )
