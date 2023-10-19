users = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT,
    username TEXT,
    created_at TIMESTAMP DEFAULT current_timestamp
);
"""
habits = """
    CREATE TABLE habits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    habit_name TEXT NOT NULL
);
"""

reminders = """
    CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    habit_id INTEGER REFERENCES habits(id) NOT NULL,
    reminder_text TEXT NOT NULL,
    scheduled_time TIMESTAMP NOT NULL
);

"""
progress_entries = """
    CREATE TABLE progress_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    habit_id INTEGER REFERENCES habits(id) NOT NULL,
    entry_date DATE NOT NULL,
    progress_text TEXT NOT NULL
);

"""
alter = """
    ALTER TABLE название_таблицы
    ADD COLUMN название_нового_столбца тип_нового_столбца;
"""