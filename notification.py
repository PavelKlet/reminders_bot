import schedule
import time


def my_reminder():
    print("Пора выполнять задачу!")


# Определяем расписание: напоминание каждый день в 10:00
schedule.every().day.at("10:00").do(my_reminder)


# Запускаем планировщик
while True:
    schedule.run_pending()
    time.sleep(1)
