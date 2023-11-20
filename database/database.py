import datetime

import psycopg2
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from config_data.config import USER, DBNAME, HOST, PASSWORD, PORT
import logging
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
        self.connection_db = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            dbname=DBNAME,
            host=HOST,
            port=PORT
        )
        self.cursor = self.connection_db.cursor()

    async def send_notification(
            self,
            user_id,
            text,
            reminder_code,
            replay,
            cron,
    ):

        """Метод отправки уведомлений пользователю"""

        try:
            await bot.send_message(user_id, text)
            if replay:
                current_date = datetime.datetime.now()
                (pk, user_pk, reminder_text,
                 reminder_date, interval,
                 uniq_code, replay, cron) = self.get_reminder(reminder_code)
                self.scheduler_add_job(
                    user_id, reminder_text,
                    current_date + interval,
                    interval,
                    replay,
                    cron
                )
            self.delete_reminder(reminder_code, cron=cron)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")

    def start_up(self):

        """Метод для запуска всех напоминаний при запуске бота"""

        with self.connection_db:
            query = """
                    SELECT r.scheduled_time, r.interval_data, r.reminder_text,
                    u.user_id, u.timezone, r.uniq_code, r.replay, r.cron
                    FROM reminders r
                    JOIN users u ON r.user_id = u.id
                    ORDER BY r.scheduled_time DESC
                """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            for (reminder_date,
                 interval,
                 reminder_text,
                 user_id,
                 u_timezone,
                 uniq_code,
                 replay,
                 cron
                 ) in result:
                local_tz = timezone(u_timezone)
                date_and_time = local_tz.localize(reminder_date)
                if (datetime.datetime.now(timezone(u_timezone))
                        >= date_and_time) and not cron:
                    self.cursor.execute("DELETE FROM reminders "
                                        "WHERE uniq_code=%s",
                                        (uniq_code,))
                else:
                    if cron:
                        trigger = CronTrigger(
                            hour=reminder_date.hour,
                            minute=reminder_date.minute,
                            timezone=local_tz
                        )
                    else:
                        trigger = DateTrigger(run_date=reminder_date)
                    scheduler.add_job(
                        self.send_notification,
                        trigger=trigger,
                        args=[
                            user_id,
                            reminder_text,
                            uniq_code,
                            replay,
                            cron
                        ],
                        id=uniq_code
                    )
            scheduler.start()

    def scheduler_add_job(
            self,
            user_id,
            text,
            scheduled_time,
            interval,
            replay,
            cron
    ):

        """Метод добавления задач в scheduler"""

        with self.connection_db:
            user_pk_query = "SELECT id, timezone FROM users WHERE user_id = %s"
            self.cursor.execute(user_pk_query, (user_id,))
            pk_user, u_timezone = self.cursor.fetchone()
            local_tz = timezone(u_timezone)
            new_uuid = str(uuid.uuid4())
            self.cursor.execute(f"INSERT INTO reminders "
                                f"(scheduled_time, user_id, "
                                f"interval_data, reminder_text, "
                                f"uniq_code, replay, cron) "
                                f"VALUES (timezone({u_timezone}), %s),"
                                f" %s, %s, %s, %s, %s, %s) "
                                f"RETURNING "
                                f"scheduled_time, user_id, "
                                f"interval_data, reminder_text, replay, cron",
                                (scheduled_time, pk_user,
                                 interval, text, new_uuid, replay, cron))
            (scheduled_time, current_id_user,
             interval_timedelta, text, replay, cron) = self.cursor.fetchone()
            if cron:
                trigger = CronTrigger(
                    hour=scheduled_time.hour,
                    minute=scheduled_time.minute,
                    timezone=local_tz
                )
            else:
                trigger = DateTrigger(run_date=scheduled_time)
            scheduler.add_job(
                self.send_notification,
                trigger=trigger,
                args=[
                    user_id,
                    text,
                    new_uuid,
                    replay,
                    cron
                ],
                id=new_uuid
            )
            self.connection_db.commit()

    def create_user(self, data):

        """Метод создания пользователя"""

        with self.connection_db:
            query = """
                INSERT INTO users 
                (user_id, first_name, last_name, username, timezone)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, data)
            self.connection_db.commit()

    def check_user(self, user_id):

        """Метод проверки пользователя"""

        with self.connection_db:
            self.cursor.execute(
                "SELECT * FROM users WHERE user_id = %s",
                (user_id,)
            )
            return self.cursor.fetchone()

    def get_reminders(self, user_id):

        """Метод получения напоминаний из бд"""

        with self.connection_db:
            self.cursor.execute(
                """
                SELECT reminders.reminder_text, 
                reminders.uniq_code, 
                reminders.cron
                FROM reminders
                JOIN users ON reminders.user_id = users.id
                WHERE users.user_id = %s
                """,
                (user_id,)
            )
        return self.cursor.fetchall()

    def get_reminder(self, reminder_code):

        """Метод получения напоминания из бд"""

        with self.connection_db:
            self.cursor.execute("SELECT * FROM reminders"
                                " WHERE uniq_code = %s", (reminder_code,))
            reminder = self.cursor.fetchone()
        return reminder

    def delete_reminder(self, reminder_code, cron=False):

        """Метод удаления напоминаний из бд"""

        if not cron:
            with self.connection_db:
                self.cursor.execute("DELETE FROM reminders "
                                    "WHERE uniq_code=%s",
                                    (reminder_code,))
                try:
                    scheduler.remove_job(reminder_code)
                except JobLookupError:
                    pass

    def select_time_zone(self, user_id):

        """Метод получения часового пояса из бд"""

        with self.connection_db:
            self.cursor.execute(
                "SELECT timezone FROM users WHERE user_id = %s",
                (user_id,)
            )
            return self.cursor.fetchone()[0]


db = Database()
