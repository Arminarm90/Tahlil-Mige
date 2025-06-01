# main.py
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import asyncio
import nest_asyncio

from config import BOT_TOKEN
from handlers.menu import (
    start, handle_contact, handle_day_selection, main_message_handler,
    begin_command, steps_command, support_command, channel_command,
    homework_command, subscription_status
)
from services.tasks import check_and_notify_steps

async def main():
    """
    Main function to set up and run the Telegram bot.
    """
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("begin", begin_command))
    app.add_handler(CommandHandler("steps", steps_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("channel", channel_command))
    app.add_handler(CommandHandler("homework", homework_command))
    app.add_handler(CommandHandler("subscription", subscription_status))

    # Message Handlers
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, main_message_handler))

    # Callback Query Handler
    app.add_handler(CallbackQueryHandler(handle_day_selection))

    # Start the background task for step notifications
    asyncio.create_task(check_and_notify_steps(app))
    
    print("🤖 Bot is running...")
    await app.run_polling()
       
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())