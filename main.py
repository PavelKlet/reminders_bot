import asyncio

from loader import bot, scheduler, dp, cursor
from other_functions import notification
from handlers.message_handlers import message_handlers
from handlers.callback_handlers import callback_handlers
from apscheduler.triggers.date import DateTrigger


async def on_start():
    cursor.execute("SELECT scheduled_time, user_id FROM reminders WHERE LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    dp.include_router(message_handlers.router)
    dp.include_router(callback_handlers.router)
    trigger = DateTrigger(run_date=result[0])
    scheduler.add_job(notification, trigger=trigger,
                      args=[result[0], result[1],
                            "Время для уведомления"])

    scheduler.start()

    await dp.start_polling(bot)

if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    bot_task = loop.create_task(on_start())
    loop.run_forever()
