from typing import Optional, List, Tuple
from pytz import timezone
from datetime import datetime, timedelta

import asyncpg
import uuid

from config_data.config import USER, DBNAME, HOST, PASSWORD, PORT

users = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT,
    username TEXT,
    timezone TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp
);
"""

reminders = """
    CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    reminder_text TEXT NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    interval_data INTERVAL,
    uniq_code TEXT UNIQUE NOT NULL,
    replay BOOLEAN NOT NULL DEFAULT FALSE,
    cron BOOLEAN NOT NULL DEFAULT FALSE
);
"""


class Database:
    def __init__(self) -> None:
        self.pool = None

    async def initialize(self) -> None:
        self.pool = await asyncpg.create_pool(
            user=USER,
            password=PASSWORD,
            database=DBNAME,
            host=HOST,
            port=PORT
        )

    async def get_full_reminders(self) -> Optional[List[asyncpg.Record]]:

        """Метод получения всех напоминаний"""

        async with self.pool.acquire() as connection:
            query = """
                    SELECT r.scheduled_time, r.interval_data, r.reminder_text,
                    u.user_id, u.timezone, r.uniq_code, r.replay, r.cron
                    FROM reminders r
                    JOIN users u ON r.user_id = u.id
                    ORDER BY r.scheduled_time DESC
                """
            result = await connection.fetch(query)

            return result

    async def add_reminder(
            self,
            user_id: int,
            text: str,
            scheduled_time: datetime,
            interval: timedelta,
            replay: bool,
            cron: bool
    ) -> Tuple[datetime, timezone, bool, int, str, str, bool, str]:

        """Метод добавления напоминаний в бд"""

        async with self.pool.acquire() as connection:

            user_pk_query = "SELECT id, timezone FROM users WHERE user_id = $1"
            pk_user, u_timezone = await connection.fetchrow(user_pk_query,
                                                            user_id)
            local_tz = timezone(u_timezone)
            new_uuid = str(uuid.uuid4())

            insert_query = """
                INSERT INTO reminders 
                (scheduled_time, user_id,
                interval_data, reminder_text,
                uniq_code, replay, cron)
                VALUES (timezone($1, $2), $3, $4, $5, $6, $7, $8)
                RETURNING scheduled_time, replay, cron
            """

            params = (
                u_timezone,
                scheduled_time,
                pk_user,
                interval,
                text,
                new_uuid,
                replay,
                cron
            )

            row = await connection.fetchrow(insert_query, *params)

            (scheduled_time, replay, cron) = row.values()

            return (scheduled_time, local_tz, cron,
                    user_id, text, new_uuid, replay, u_timezone)

    async def create_user(self, data: tuple) -> None:

        """Метод создания пользователя"""

        async with self.pool.acquire() as connection:
            query = """
                INSERT INTO users 
                (user_id, first_name, last_name, username, timezone)
                VALUES ($1, $2, $3, $4, $5)
            """
            await connection.execute(query, *data)

    async def check_user(self, user_id) -> Optional[asyncpg.Record]:

        """Метод проверки пользователя"""

        async with self.pool.acquire() as connection:
            query = """
                SELECT * FROM users WHERE user_id = $1
            """
            return await connection.fetchrow(query, user_id)

    async def get_reminders(self,
                            user_id: int) -> Optional[List[asyncpg.Record]]:

        """Метод получения напоминаний из базы данных"""

        async with self.pool.acquire() as connection:
            query = """
                SELECT reminders.reminder_text, 
                reminders.uniq_code
                FROM reminders
                JOIN users ON reminders.user_id = users.id
                WHERE users.user_id = $1
            """
            return await connection.fetch(query, user_id)

    async def get_reminder(self,
                           reminder_code: str) -> Optional[asyncpg.Record]:

        """Метод получения напоминания из базы данных"""

        async with self.pool.acquire() as connection:
            query = "SELECT * FROM reminders WHERE uniq_code = $1"
            return await connection.fetchrow(query, reminder_code)

    async def delete_reminder(self, reminder_code: str,
                              cron: bool = False) -> None:

        """Метод удаления напоминаний из базы данных"""
        if not cron:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    query = "DELETE FROM reminders WHERE uniq_code = $1"
                    await connection.execute(query, reminder_code)

    async def select_time_zone(self,
                               user_id: int) -> str | None:

        """Метод получения часового пояса из базы данных"""

        async with self.pool.acquire() as connection:
            query = "SELECT timezone FROM users WHERE user_id = $1"
            row = await connection.fetchrow(query, user_id)
            return row[0] if row else None

    async def update_timezone(self, user_id: int, u_timezone: str) -> None:

        """Метод обновления часового пояса в базе данных"""

        async with self.pool.acquire() as connection:
            query = """
                UPDATE users
                SET timezone = $1
                WHERE user_id = $2
            """
            await connection.execute(query, u_timezone, user_id)


db = Database()
