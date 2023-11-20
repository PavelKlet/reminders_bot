from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram import Router
from aiogram.fsm.context import FSMContext
from database.database import db
from state.states import Form

router = Router(name=__name__)


@router.callback_query(StateFilter(Form.switch_timezone))
async def process_switch_timezone(
        callback_query: CallbackQuery,
        state: FSMContext
):
    db.update_timezone(callback_query.from_user.id, callback_query.data)
    await callback_query.answer("Часовой пояс изменён", show_alert=True)
    await callback_query.message.delete()
    await state.clear()


@router.callback_query(StateFilter(Form.delete_reminder))
async def process_delete_reminder(callback_query: CallbackQuery):

    """Хендлер удаления напоминания"""

    uniq_code, type_reminder = callback_query.data.split(":")
    if type_reminder == "cron":
        db.delete_reminder(uniq_code, cron=False)
    else:
        db.delete_reminder(uniq_code)
    await callback_query.answer("Напоминание удалено", show_alert=True)
    await callback_query.message.delete()


@router.callback_query(StateFilter(Form.time_zone))
async def process_timezone(callback_query: CallbackQuery,
                           state: FSMContext):

    """Хендлер выбора часового пояса"""

    print(callback_query.data)
    data = (
        callback_query.from_user.id,
        callback_query.from_user.first_name,
        callback_query.from_user.last_name,
        callback_query.from_user.username,
        callback_query.data
    )
    db.create_user(data)
    await callback_query.message.delete()
    await callback_query.message.answer("Вы можете оставить текст, дату "
                                        "и время для напоминания. "
                                        "Сначала отправьте текст.")
    await state.set_state(Form.reminder_text)


@router.callback_query(StateFilter(Form.type_reminder))
async def process_callback(callback_query: CallbackQuery, state: FSMContext):

    """Хендлер выбора типа напоминания"""

    data = await state.get_data()
    if callback_query.data == "С заданным промежутком":
        replay = True
    else:
        replay = False
    if callback_query.data == "Каждый день в это время":
        cron = True
    else:
        cron = False
    db.scheduler_add_job(callback_query.from_user.id,
                         data["reminder_text"],
                         data["date_and_time"],
                         data["interval"],
                         replay,
                         cron
                         )
    await callback_query.message.answer("Напоминание поставлено.")
    await callback_query.message.delete()
    await state.clear()



