import datetime
import logging

import asyncpg
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from config_data.config import USER, DBNAME, HOST, PASSWORD, PORT
from loader import scheduler, bot
import uuid

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
    def __init__(self):
        self.pool = None

    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            user=USER,
            password=PASSWORD,
            database=DBNAME,
            host=HOST,
            port=PORT
        )

    async def send_notification(
            self,
            user_id,
            text,
            reminder_code,
            replay,
            cron,
            u_timezone
    ):

        """Метод отправки уведомлений пользователю"""

        try:

            await bot.send_message(user_id, text)

            if replay:
                (pk, user_pk, reminder_text,
                 reminder_date, interval,
                 uniq_code, replay, cron) = await self.get_reminder(reminder_code)
                date_and_time = (
                        datetime.datetime.now(timezone(u_timezone)) + interval
                )
                await self.scheduler_add_job(
                    user_id, reminder_text,
                    date_and_time,
                    interval,
                    replay,
                    cron
                )
            await self.delete_reminder(reminder_code, cron=cron)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")

    async def start_up(self):

        """Метод для запуска всех напоминаний при запуске бота"""

        async with self.pool.acquire() as connection:
            query = """
                    SELECT r.scheduled_time, r.interval_data, r.reminder_text,
                    u.user_id, u.timezone, r.uniq_code, r.replay, r.cron
                    FROM reminders r
                    JOIN users u ON r.user_id = u.id
                    ORDER BY r.scheduled_time DESC
                """
            result = await connection.fetch(query)

            for row in result:

                reminder_date = row["scheduled_time"]
                reminder_text = row["reminder_text"]
                user_id = row["user_id"]
                u_timezone = row["timezone"]
                uniq_code = row["uniq_code"]
                replay = row["replay"]
                cron = row["cron"]
                local_tz = timezone(u_timezone)
                date_and_time = local_tz.localize(reminder_date)

                if (datetime.datetime.now(
                        timezone(u_timezone)) >= date_and_time) and not cron:
                    await connection.execute("DELETE FROM reminders "
                                             "WHERE uniq_code=$1",
                                             uniq_code)
                else:
                    if cron:
                        trigger = CronTrigger(
                            hour=reminder_date.hour,
                            minute=reminder_date.minute,
                            timezone=local_tz
                        )
                    else:
                        trigger = DateTrigger(run_date=date_and_time)

                    scheduler.add_job(
                        self.send_notification,
                        trigger=trigger,
                        args=[
                            user_id,
                            reminder_text,
                            uniq_code,
                            replay,
                            cron,
                            u_timezone
                        ],
                        id=uniq_code
                    )

        scheduler.start()

    async def scheduler_add_job(
            self,
            user_id,
            text,
            scheduled_time,
            interval,
            replay,
            cron
    ):

        """Метод добавления задач в scheduler"""

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
                RETURNING scheduled_time, user_id,
                interval_data, reminder_text, replay, cron
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

            (scheduled_time, user_pk,
             interval_data, reminder_text, replay, cron) = row.values()

            if cron:
                trigger = CronTrigger(
                    hour=scheduled_time.hour,
                    minute=scheduled_time.minute,
                    timezone=local_tz
                )
            else:
                date_and_time = local_tz.localize(scheduled_time)
                trigger = DateTrigger(run_date=date_and_time)
            scheduler.add_job(
                self.send_notification,
                trigger=trigger,
                args=[
                    user_id,
                    text,
                    new_uuid,
                    replay,
                    cron,
                    u_timezone
                ],
                id=new_uuid
            )

    async def create_user(self, data):

        """Метод создания пользователя"""

        async with self.pool.acquire() as connection:
            query = """
                INSERT INTO users 
                (user_id, first_name, last_name, username, timezone)
                VALUES ($1, $2, $3, $4, $5)
            """
            await connection.execute(query, *data)

    async def check_user(self, user_id):

        """Метод проверки пользователя"""

        async with self.pool.acquire() as connection:
            query = """
                SELECT * FROM users WHERE user_id = $1
            """
            return await connection.fetchrow(query, user_id)

    async def get_reminders(self, user_id):

        """Метод получения напоминаний из базы данных"""

        async with self.pool.acquire() as connection:
            query = """
                SELECT reminders.reminder_text, 
                reminders.uniq_code, 
                reminders.cron
                FROM reminders
                JOIN users ON reminders.user_id = users.id
                WHERE users.user_id = $1
            """
            return await connection.fetch(query, user_id)

    async def get_reminder(self, reminder_code):

        """Метод получения напоминания из базы данных"""

        async with self.pool.acquire() as connection:
            query = "SELECT * FROM reminders WHERE uniq_code = $1"
            return await connection.fetchrow(query, reminder_code)

    async def delete_reminder(self, reminder_code, cron=False):

        """Метод удаления напоминаний из базы данных"""

        async with self.pool.acquire() as connection:
            if not cron:
                async with connection.transaction():
                    query = "DELETE FROM reminders WHERE uniq_code = $1"
                    await connection.execute(query, reminder_code)
                try:
                    scheduler.remove_job(reminder_code)
                except JobLookupError:
                    pass

    async def select_time_zone(self, user_id):

        """Метод получения часового пояса из базы данных"""

        async with self.pool.acquire() as connection:
            query = "SELECT timezone FROM users WHERE user_id = $1"
            row = await connection.fetchrow(query, user_id)
            return row[0] if row else None

    async def update_timezone(self, user_id, u_timezone):

        """Метод обновления часового пояса в базе данных"""

        async with self.pool.acquire() as connection:
            query = """
                UPDATE users
                SET timezone = $1
                WHERE user_id = $2
            """
            await connection.execute(query, u_timezone, user_id)


db = Database()
