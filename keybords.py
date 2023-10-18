from aiogram.utils.keyboard import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardBuilder,
    ReplyKeyboardMarkup,
    KeyboardButton
)

interval_hour = InlineKeyboardButton(text="Интервал час", callback_data="60")
interval_day = InlineKeyboardButton(text="Интервал сутки",
                                    callback_data="1440")
user_config = InlineKeyboardButton(text="Ввести вручную",
                                   callback_data="user_config")
builder = InlineKeyboardBuilder()

builder.add(interval_day, interval_hour, user_config)
