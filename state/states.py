from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    time_zone = State()
    reminder_text = State()
    date_selection = State()
    type_reminder = State()
    delete_reminder = State()
    switch_timezone = State()


