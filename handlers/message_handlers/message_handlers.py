from aiogram import types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from loader import dp, user_settings
from keyboards.keyboards import builder
from aiogram import Router
from state.states import Form

router = Router(name=__name__)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
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
    await state.set_state(Form.test)
    # # sql_query = """
    # #    INSERT INTO users (user_id, first_name, last_name, username, created_at)
    # #    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
    # #    """
    # cursor.execute(sql_query, data)
    # db_connection.commit())
    await message.answer("Привет! Отправьте текст для напоминания")

    # Запускаем календарь
    # await send_notification(message.from_user.id, "Текст уведомления")


@router.message()
async def handle_text(message: types.Message):
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