from aiogram.utils.keyboard import (
    InlineKeyboardButton,
    InlineKeyboardBuilder,
)


interval = InlineKeyboardButton(text="С заданным промежутком",
                                callback_data="С заданным промежутком")
cron = InlineKeyboardButton(text="Каждый день в это время",
                            callback_data="Каждый день в это время")
date = InlineKeyboardButton(text="Только в эту дату",
                            callback_data="Только в эту дату")
type_reminder = InlineKeyboardBuilder()

for i_type in [date, cron, interval]:
    type_reminder.row(i_type)

builder = InlineKeyboardBuilder()
keyboard_time_zones = InlineKeyboardBuilder()
time_zones = [
    "Калининградское время:Europe/Kaliningrad",
    "Московское стандартное:Europe/Moscow",
    "Самарское время:Europe/Samara",
    "Екатеринбургское время:Asia/Yekaterinburg",
    "Омское время:Asia/Omsk",
    "Красноярское время:Asia/Krasnoyarsk",
    "Иркутское время:Asia/Irkutsk",
    "Якутское время:Asia/Yakutsk",
    "Владивостокское время:Asia/Vladivostok",
    "Магаданское время:Asia/Magadan",
    "Камчатское время:Asia/Kamchatka",
    "Чукотское время:Asia/Anadyr",
]
for time_zone in time_zones:
    name, zone = time_zone.split(":")
    keyboard_time_zones.row(
        InlineKeyboardButton(
            text=f"{name}",
            callback_data=f"{zone}"
        )
    )
