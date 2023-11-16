import asyncio
import logging
from logging.handlers import RotatingFileHandler

from loader import bot, dp
from handlers.message_handlers import message_handlers
from handlers.callback_handlers import callback_handlers
from database.database import db


async def on_start():
    db.start_up()
    dp.include_router(message_handlers.router)
    dp.include_router(callback_handlers.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # handler = RotatingFileHandler("app.log", maxBytes=100000, backupCount=3)
    # logging.basicConfig(handlers=[handler], level=logging.INFO,
    #                     format="%(asctime)s - %(name)s -"
    #                            " %(levelname)s - %(message)s")
    loop = asyncio.get_event_loop()
    bot_task = loop.create_task(on_start())
    loop.run_forever()
