# Anima

Anima — Telegram-помощница психолог и коуч.

Она принимает сообщения пользователя в Telegram, держит короткую память диалога
и обращается к NVIDIA NIM API через OpenAI-compatible endpoint.

## Переменные окружения

Заполни файл `.env`:

```env
TELEGRAM_BOT_TOKEN=
NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
NVIDIA_TEMPERATURE=1
NVIDIA_TOP_P=0.95
NVIDIA_MAX_TOKENS=16384
NVIDIA_TIMEOUT_SECONDS=45
NVIDIA_ENABLE_THINKING=true
NVIDIA_REASONING_BUDGET=16384
ANIMA_HISTORY_MESSAGES_LIMIT=10
ANIMA_LANGUAGE=ru
```

## Локальный запуск

```bash
pip install -r requirements.txt
python bot.py
```

## Telegram-команды

- `/start` — начать разговор.
- `/help` — показать подсказки.
- `/privacy` — коротко о приватности.
- `/reset` — очистить память текущего диалога.

## Архитектура

- `bot.py` — точка входа.
- `config.py` — чтение `.env`.
- `NeuroPsychoBot/app.py` — сборка Telegram-приложения.
- `NeuroPsychoBot/handlers/dialog.py` — Telegram-ручки.
- `NeuroPsychoBot/services/nvidia_client.py` — клиент NVIDIA API через `openai`.
- `NeuroPsychoBot/services/anima_coach.py` — психологический слой Anima.
- `NeuroPsychoBot/services/dialogue_memory.py` — короткая память диалога.
- `NeuroPsychoBot/services/safety.py` — кризисные сигналы.
- `NeuroPsychoBot/texts/ru.py` и `NeuroPsychoBot/texts/en.py` — тексты интерфейса.
