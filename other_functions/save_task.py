from loader import cursor, db_connection


def save_task(name, trigger, callback):
    # Сохранение задачи в базе данных
    cursor.execute(
        "INSERT INTO tasks (name, trigger, callback) VALUES (?,?,?)",
        (name, trigger, callback))
    db_connection.commit()
