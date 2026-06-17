# Anima

Anima — Telegram-помощница психолог и коуч.

Она принимает сообщения пользователя в Telegram, держит короткую память диалога
и обращается к NVIDIA NIM API через OpenAI-compatible endpoint.

## Переменные окружения

Заполни файл `.env`:

```env
TELEGRAM_BOT_TOKEN=
NVIDIA_API_KEY=
API_KEY_NVIDIA=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
NVIDIA_FALLBACK_MODEL=nvidia/nemotron-3-ultra-550b-a55b
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

Этот режим использует polling и подходит для разработки на компьютере.

## Render

Render запускает Anima как Web Service через команду:

```bash
python bot.py
```

Так как текущий сервис в Render создан именно как Web Service, `bot.py`
дополнительно запускает легкий HTTP health-server на `0.0.0.0:$PORT`.
Он отвечает на `/` и `/health`, а основной Telegram-бот продолжает работать
через polling.

В корне проекта лежит `.python-version` со значением `3.12`.
Этот файл фиксирует стабильную ветку Python для Render и защищает старую связку
`python-telegram-bot==20.3`, `httpx==0.24.1`, `httpcore==0.17.3`
от запуска на Python 3.14.

## Vercel webhook

Для постоянной работы без включенного компьютера Anima использует Vercel Function:

- `api/telegram.py` — Telegram webhook.
- `api/health.py` — простая проверка жизни API.
- `scripts/telegram_webhook.py` — установка, удаление и проверка webhook.

В Vercel нужно добавить переменные окружения:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
NVIDIA_API_KEY=
API_KEY_NVIDIA=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
NVIDIA_FALLBACK_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NVIDIA_TEMPERATURE=1
NVIDIA_TOP_P=0.95
NVIDIA_MAX_TOKENS=16384
NVIDIA_TIMEOUT_SECONDS=45
NVIDIA_ENABLE_THINKING=true
NVIDIA_REASONING_BUDGET=16384
ANIMA_HISTORY_MESSAGES_LIMIT=10
ANIMA_LANGUAGE=ru
```

После деплоя нужно переключить Telegram на webhook:

```bash
python scripts/telegram_webhook.py set https://your-project.vercel.app
```

Проверить webhook:

```bash
python scripts/telegram_webhook.py info
```

Вернуться к локальному polling:

```bash
python scripts/telegram_webhook.py delete
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
- `NeuroPsychoBot/services/telegram_gateway.py` — отправка сообщений в Telegram.
- `NeuroPsychoBot/services/webhook_dialogue.py` — логика webhook-диалога.
- `NeuroPsychoBot/services/safety.py` — кризисные сигналы.
- `NeuroPsychoBot/texts/ru.py` и `NeuroPsychoBot/texts/en.py` — тексты интерфейса.
