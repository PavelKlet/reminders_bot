from aiogram.utils.keyboard import (
    InlineKeyboardButton,
    InlineKeyboardBuilder,
)


def type_keyboard():
    interval = InlineKeyboardButton(text="С заданным промежутком",
                                    callback_data="С заданным промежутком")
    cron = InlineKeyboardButton(text="Каждый день в это время",
                                callback_data="Каждый день в это время")
    date = InlineKeyboardButton(text="Только в эту дату",
                                callback_data="Только в эту дату")
    type_reminder = InlineKeyboardBuilder()

    for i_type in [date, cron, interval]:
        type_reminder.row(i_type)

    return type_reminder
