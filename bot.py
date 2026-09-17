"""Основной файл бота с webhook режимом."""
import asyncio
import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from config import Config
from handlers import MessageHandlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def setup_handlers(application: Application) -> None:
    """Настройка обработчиков для бота."""
    # Команды
    application.add_handler(CommandHandler("start", MessageHandlers.start))
    application.add_handler(CommandHandler("help", MessageHandlers.help_command))
    
    # Текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, MessageHandlers.handle_message))
    
    # Фото
    application.add_handler(MessageHandler(filters.PHOTO, MessageHandlers.handle_photo))


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


async def main() -> None:
    """Главная функция запуска бота."""
    try:
        # Загрузка конфигурации
        config = Config.from_env()
        logger.info("Конфигурация загружена успешно")
        
        # Создание приложения
        application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Настройка обработчиков
        setup_handlers(application)
        
        # Добавление обработчика ошибок
        application.add_error_handler(error_handler)
        
        # Настройка webhook
        render_url = os.getenv('RENDER_EXTERNAL_URL', '').strip()
        webhook_url = config.WEBHOOK_URL or f"{render_url}/webhook"
        port = config.PORT
        
        logger.info(f"Запуск бота в webhook режиме на порту {port}")
        logger.info(f"Webhook URL: {webhook_url}")
        
        # Инициализация и запуск приложения
        await application.initialize()
        await application.start()
        
        # Запуск webhook
        await application.updater.start_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=webhook_url,
            drop_pending_updates=True
        )
        
        # Держим приложение запущенным
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
