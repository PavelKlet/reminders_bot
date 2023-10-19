import psycopg2
from aiogram import Bot, Dispatcher

from config_data.config import TOKEN, USER, DBNAME, HOST, PASSWORD, PORT
from apscheduler.schedulers.asyncio import AsyncIOScheduler


scheduler = AsyncIOScheduler()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
user_settings = {}

db_connection = psycopg2.connect(
    user=USER,
    password=PASSWORD,
    dbname=DBNAME,
    host=HOST,
    port=PORT
)
cursor = db_connection.cursor()
