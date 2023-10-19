from aiogram import F
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta
from loader import dp, scheduler, cursor, db_connection
from other_functions.notification import send_notification
from aiogram import Router
from state.states import Form
from aiogram.fsm.context import FSMContext


router = Router(name=__name__)


@router.callback_query()
async def process_callback(callback_query: CallbackQuery, state: FSMContext):
    print(callback_query.data)
    int_data = int(callback_query.data)
    current_time = datetime.now()
    scheduled_time = current_time + timedelta(minutes=int_data)
    cursor.execute("INSERT INTO reminders (scheduled_time, user_id) VALUES (%s,  %s)",
                   (scheduled_time, callback_query.from_user.id))
    # scheduler.add_job(send_notification, "interval",
    #                   minutes=int_data,
    #                   args=[callback_query.from_user.id,
    #                         "Время для уведомления"
    #                         ]
    #
    #                   )
    cursor.execute("SELECT scheduled_time FROM reminders WHERE условие_выборки")
    db_connection.commit()
    cursor.close()
    db_connection.close()

    await callback_query.answer("Напоминание поставлено")

