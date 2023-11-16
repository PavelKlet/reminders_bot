from aiogram import types
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram import Router
from state.states import Form
from database.database import db
from keyboards.keyboards import type_reminder, keyboard_time_zones
from pytz import timezone
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardBuilder

router = Router(name=__name__)


class DateError(Exception):
    pass


@router.message(Command("help"))
async def cmd_delete(message: types.Message, state: FSMContext):

    """Хендлер команды /help"""

    await message.answer("/start - начать работу бота\n/delete - "
                         "удалить напоминание")


@router.message(Command("delete"))
async def cmd_delete(message: types.Message, state: FSMContext):

    """Хендлер команды /delete"""

    full_reminders = db.get_reminders(message.from_user.id)
    if full_reminders:
        builder = InlineKeyboardBuilder()
        for reminder, uniq_code, cron in full_reminders:
            if not cron:
                builder.row(
                    InlineKeyboardButton(
                        callback_data=f"{uniq_code}:date",
                        text=reminder
                    )
                )
            else:
                builder.row(
                    InlineKeyboardButton(
                        callback_data=f"{uniq_code}:cron",
                        text=reminder
                    )
                )
        await message.answer(f"Выберите ваше напоминание для отмены:\n",
                             reply_markup=builder.as_markup())
        del builder
        await state.set_state(Form.delete_reminder)
    else:
        await message.answer("У вас ещё нет напоминаний.")


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):

    """Хендлер команды /start"""

    user_id = message.from_user.id
    user = db.check_user(user_id)
    if not user:
        await message.answer(
            "Привет! Для начала нужно определить ваш часовой пояс, "
            "выберите один из вариантов:",
            reply_markup=keyboard_time_zones.as_markup()
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
        user_timezone = db.select_time_zone(message.from_user.id)
        local_tz = timezone(user_timezone)
        date_and_time = local_tz.localize(
            datetime.strptime(message.text, "%d.%m.%Y %H %M"))
        current_date = datetime.now(timezone(user_timezone))
        await message.answer("Выберите вид напоминания.",
                             reply_markup=type_reminder.as_markup()
                             )
        if current_date >= date_and_time:
            raise DateError("Дата раньше настоящего времени.")
        interval = date_and_time - current_date
        await state.update_data(date_and_time=date_and_time, interval=interval)
        await state.set_state(Form.type_reminder)
    except Exception:
        await message.answer("Что-то пошло не так, "
                             "проверьте правильность введённых"
                             " вами данных и попробуйте ещё раз.")

