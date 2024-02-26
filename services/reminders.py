import datetime
from pytz import timezone
import logging

from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

from loader import scheduler, bot
from database.database import db


class ReminderManager(object):

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
                 uniq_code, replay, cron) = await db.get_reminder(reminder_code)

                date_and_time = (
                        datetime.datetime.now(timezone(u_timezone)) + interval
                )

                reminder_data = await db.add_reminder(
                    user_id, reminder_text,
                    date_and_time,
                    interval,
                    replay,
                    cron
                )
                await self.scheduler_add_job(*reminder_data)

            await db.delete_reminder(reminder_code, cron=cron)
            await self.delete_job(reminder_code, cron=cron)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")

    async def scheduler_add_job(self, scheduled_time, local_tz, cron,
                                user_id, text, new_uuid, replay, u_timezone):

        """Метод добавления задач в scheduler"""

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

    async def start_up(self, reminders_info):

        """Метод запуска всех напоминаний из бд"""

        for row in reminders_info:

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
                await db.delete_reminder(uniq_code)
                await self.delete_job(uniq_code)
            else:
                await self.scheduler_add_job(reminder_date, local_tz,
                                             cron, user_id,
                                             reminder_text, uniq_code,
                                             replay, u_timezone)

        scheduler.start()

    @staticmethod
    async def delete_job(code, cron=False):

        """Удаление задач планировщика"""

        if not cron:
            try:
                scheduler.remove_job(code)
            except JobLookupError:
                pass


reminder_manager = ReminderManager()
