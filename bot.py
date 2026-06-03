from telegram import Update

from NeuroPsychoBot.app import create_application


def main() -> None:
    application = create_application()

    print("Anima запущена. Telegram polling активен.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
