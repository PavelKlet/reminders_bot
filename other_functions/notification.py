import logging

from loader import bot


async def send_notification(user_id, text):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")