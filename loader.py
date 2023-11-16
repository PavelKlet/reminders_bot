from aiogram import Bot, Dispatcher

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config_data.config import TOKEN

scheduler = AsyncIOScheduler()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
