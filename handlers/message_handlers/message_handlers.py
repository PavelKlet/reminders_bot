import logging
from datetime import datetime
from pytz import timezone

from aiogram import types
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardBuilder

from state.states import Form
from database.database import db
from keyboards.timezone import timezone_keyboard
from keyboards.type import type_keyboard

router = Router(name=__name__)


class DateError(Exception):
    pass


@router.message(Command("timezone"), StateFilter(None))
async def cmd_timezone(message: types.Message, state: FSMContext):
    if await db.check_user(message.from_user.id):
        await message.answer(
            "Выберите один из вариантов:",
            reply_markup=timezone_keyboard().as_markup()
        )
        await state.set_state(Form.switch_timezone)


@router.message(Command("help"), StateFilter(None))
async def cmd_help(message: types.Message):

    """Хендлер команды /help"""

    await message.answer("/start - начать работу бота\n/delete - "
                         "удалить напоминание\n/timezone - "
                         "поменять часовой пояс")


@router.message(Command("delete"), StateFilter(None))
async def cmd_delete(message: types.Message, state: FSMContext):

    """Хендлер команды /delete"""

    full_reminders = await db.get_reminders(message.from_user.id)

    if full_reminders:

        builder = InlineKeyboardBuilder()

        for reminder, uniq_code in full_reminders:
            builder.row(
                InlineKeyboardButton(
                    callback_data=uniq_code,
                    text=reminder
                )
            )

        await message.answer(f"Выберите ваше напоминание для отмены:\n",
                             reply_markup=builder.as_markup())
        await state.set_state(Form.delete_reminder)
    else:
        await message.answer("У вас ещё нет напоминаний.")


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):

    """Хендлер команды /start"""

    await state.set_data({})

    user_id = message.from_user.id
    user = await db.check_user(user_id)

    if not user:
        await message.answer(
            "Привет! Для начала нужно определить ваш часовой пояс, "
            "выберите один из вариантов:",
            reply_markup=timezone_keyboard().as_markup()
        )
        await state.set_state(Form.time_zone)
    else:
        await message.answer(f"Привет, {message.from_user.first_name}! "
                             f"Вы можете оставить текст, дату "
                             f"и время для напоминания. "
                             f"Сначала отправьте текст.")
        await state.set_state(Form.reminder_text)


@router.message(StateFilter(Form.reminder_text))
async def handle_text(message: types.Message, state: FSMContext):

    """Хендлер текста напоминания"""

    if message.text:
        await state.update_data(reminder_text=message.text)
        await state.set_state(Form.date_selection)
        await message.answer(
            "Теперь напишите дату и время "
            "для напоминания.\n"
            "Пример: 14.02.2025 16 00"
        )
    else:
        await message.answer("Что-то пошло не так, "
                             "проверьте правильность введённых"
                             " вами данных и попробуйте ещё раз. "
                             "Отправить нужно именно текстовое сообщение.")


@router.message(StateFilter(Form.date_selection))
async def handle_date(message: types.Message, state: FSMContext):

    """Хендлер полученной даты"""

    try:

        user_timezone = await db.select_time_zone(message.from_user.id)
        local_tz = timezone(user_timezone)
        date_and_time = local_tz.localize(
            datetime.strptime(message.text, "%d.%m.%Y %H %M"))
        current_date = datetime.now(timezone(user_timezone))

        if current_date >= date_and_time:
            raise DateError("Дата раньше настоящего времени.")
        await message.answer("Выберите вид напоминания.",
                             reply_markup=type_keyboard().as_markup()
                             )
        interval = date_and_time - current_date

        await state.update_data(date_and_time=date_and_time, interval=interval)
        await state.set_state(Form.type_reminder)
    except Exception as ex:
        await message.answer("Что-то пошло не так, "
                             "проверьте правильность введённых"
                             " вами данных и попробуйте ещё раз.")
        logging.error(ex)
