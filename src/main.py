import sys
import os

# Ensure the root directory is in sys.path so 'src' can be imported when running `python src/main.py`
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from src.config import TELEGRAM_BOT_TOKEN
from src.handlers import form as handlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Setup Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", handlers.show_menu),
            CommandHandler("input_event", handlers.start_event_form)
        ],
        states={
            handlers.SELECTING_BRANCH: [
                CallbackQueryHandler(handlers.cancel, pattern="^cancel$"),
                CallbackQueryHandler(handlers.branch_selected)
            ],
            handlers.SELECTING_WOK: [
                CallbackQueryHandler(handlers.cancel, pattern="^cancel$"),
                CallbackQueryHandler(handlers.start_event_form, pattern="^back_start$"),
                CallbackQueryHandler(handlers.wok_selected)
            ],
            handlers.TYPING_EVENT_NAME: [
                CallbackQueryHandler(handlers.cancel, pattern="^cancel$"),
                CallbackQueryHandler(handlers.back_to_woks, pattern="^back_to_woks$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.event_name_received),
                MessageHandler(~filters.TEXT & ~filters.COMMAND, handlers.invalid_event_name)
            ],
            handlers.CHOOSING_DEVICE: [
                CallbackQueryHandler(handlers.cancel, pattern="^cancel$"),
                CallbackQueryHandler(handlers.back_to_event_name, pattern="^back_to_event_name$"),
                CallbackQueryHandler(handlers.device_selected, pattern="^device_")
            ],
            handlers.SENDING_LOCATION: [
                CallbackQueryHandler(handlers.cancel, pattern="^cancel$"),
                CallbackQueryHandler(handlers.back_to_device, pattern="^back_to_device$"),
                MessageHandler(filters.Regex("^⬅️ Kembali$"), handlers.back_to_device),
                MessageHandler(filters.Regex("^❌ Batal$"), handlers.cancel),
                MessageHandler(filters.LOCATION, handlers.location_received),
                MessageHandler(~filters.LOCATION & ~filters.COMMAND & ~filters.Regex("^(⬅️ Kembali|❌ Batal)$"), handlers.invalid_location)
            ],
            handlers.CONFIRMING: [
                CallbackQueryHandler(handlers.cancel, pattern="^cancel$"),
                CallbackQueryHandler(handlers.back_to_device, pattern="^back_to_device$"),
                CallbackQueryHandler(handlers.submit_data, pattern="^submit_data$")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", handlers.cancel),
            MessageHandler(filters.Regex("^❌ Batal$"), handlers.cancel)
        ],
    )

    application.add_handler(conv_handler)

    logger.info("Starting bot...")
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
