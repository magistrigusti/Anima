from telegram import Update

from anima.app import create_application
from anima.services.render_health_server import start_render_health_server


def main() -> None:
    application = create_application()

    start_render_health_server()

    print("Anima запущена. Telegram polling активен.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
