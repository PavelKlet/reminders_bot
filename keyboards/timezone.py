from aiogram.utils.keyboard import (
    InlineKeyboardButton,
    InlineKeyboardBuilder,
)


def timezone_keyboard():
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

    keyboard_time_zones = InlineKeyboardBuilder()

    for time_zone in time_zones:
        name, zone = time_zone.split(":")
        keyboard_time_zones.row(
            InlineKeyboardButton(
                text=name,
                callback_data=zone
            )
        )

    return keyboard_time_zones
