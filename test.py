import logging
import asyncio
import time
from aiogram import Router, F
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
import psycopg2
import schedule
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from keybords import builder

db_connection = psycopg2.connect(
    user="postgres",
    password="123",
    dbname="bot",
    host="localhost",
    port=5432
)
user_settings = {}
cursor = db_connection.cursor()
# Инициализация бота
API_TOKEN = "6599994909:AAEvTLRW6QzXeZjm07Zzr8Bpjjnm0ERYbfE"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot)
my_router = Router(name=__name__)


# Функция для отправки уведомления
async def send_notification(user_id, text):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    user_username = message.from_user.username
    data = (
        user_id,
        user_first_name,
        user_last_name,
        user_username,
    )
    # # sql_query = """
    # #    INSERT INTO users (user_id, first_name, last_name, username, created_at)
    # #    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
    # #    """
    # cursor.execute(sql_query, data)
    # db_connection.commit())
    await message.answer("Привет! Отправьте текст для напоминания")

    # Запускаем календарь
    # await send_notification(message.from_user.id, "Текст уведомления")


@dp.message()
async def handle_text(message: Message):
    user_id = message.from_user.id
    text = message.text
    user_settings[user_id] = {"text": text}
    await message.answer(
        "Выберите интервал напоминания",
        reply_markup=builder.as_markup()
    )

    #     if not user_settings[user_id]["time"]:
    #         user_settings[user_id]["time"] = text
    #         await bot.send_message(user_id, "Отлично! Теперь укажите интервал в минутах.")
    #     elif not user_settings[user_id]["interval"]:
    #         try:
    #             user_settings[user_id]["interval"] = int(text)
    #             await bot.send_message(user_id, f"Уведомления будут отправляться в {user_settings[user_id]['time']} с интервалом {user_settings[user_id]['interval']} минут.")
    #             schedule.every(user_settings[user_id]["interval"]).minutes.do(send_notification, user_id, "Время для уведомления!")
    #         except ValueError:
    #             await bot.send_message(user_id, "Пожалуйста, укажите корректный интервал в минутах.")
    # else:
    #     await bot.send_message(user_id, text="Чтобы начать, отправьте /start.")


@dp.callback_query(F.data == "60")
async def process_callback(callback_query: CallbackQuery, callback_data="60"):
    print(callback_query.data)
    await callback_query.answer("Напоминание поставлено")
    int_data = int(callback_data)
    schedule.every(int_data).minutes.do(
        send_notification, callback_query.from_user.id, "Время для уведомления!")


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


async def on_start(dp):
    await dp.start_polling(bot)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(on_start(dp))
    loop.run_forever()
