from src.database.connector import db


def group_attendance_create(group_training_id, client_id):
    if not db.reconnect_if_needed():
        raise ConnectionError("Не удалось подключиться к БД")

    cur = db.cursor
    cur.execute("""
        INSERT INTO group_attendances (group_training_id, client_id)
        VALUES (%s, %s)
    """, (group_training_id, client_id))
    return db.get_last_insert_id()


def group_attendance_get_by_id(attendance_id):
    if not db.reconnect_if_needed():
        return None

    cur = db.cursor
    cur.execute("""
        SELECT attendance_id, group_training_id, client_id
        FROM group_attendances
        WHERE attendance_id=%s
    """, (attendance_id,))
    row = cur.fetchone()
    if row:
        return {
            'attendance_id': row[0],
            'group_training_id': row[1],
            'client_id': row[2]
        }
    return None


def group_attendance_get_by_client(client_id):
    if not db.reconnect_if_needed():
        return []

    cur = db.cursor
    cur.execute("""
        SELECT attendance_id, group_training_id, client_id
        FROM group_attendances
        WHERE client_id=%s
    """, (client_id,))
    rows = cur.fetchall()
    return [
        {
            'attendance_id': r[0],
            'group_training_id': r[1],
            'client_id': r[2]
        } for r in rows
    ]


def group_attendance_get_by_training(group_training_id):
    """Все посещения по конкретной групповой тренировке"""
    if not db.reconnect_if_needed():
        return []

    cur = db.cursor
    cur.execute("""
        SELECT attendance_id, group_training_id, client_id, attendance_date
        FROM group_attendances
        WHERE group_training_id=%s
    """, (group_training_id,))
    rows = cur.fetchall()
    return [
        {
            'attendance_id': r[0],
            'group_training_id': r[1],
            'client_id': r[2],
            'attendance_date': r[3]
        } for r in rows
    ]


def group_attendance_delete(attendance_id):
    """Удалить запись о посещении"""
    if not db.reconnect_if_needed():
        return False

    cur = db.cursor
    cur.execute("DELETE FROM group_attendances WHERE attendance_id=%s", (attendance_id,))
    return True


def group_attendance_get_count_by_training(group_training_id):
    """Сколько человек записано на тренировку"""
    if not db.reconnect_if_needed():
        return 0

    cur = db.cursor
    cur.execute("SELECT COUNT(*) FROM group_attendances WHERE group_training_id=%s", (group_training_id,))
    return cur.fetchone()[0]


def group_attendance_check_client_on_training(group_training_id, client_id):
    """Проверка, записан ли клиент на тренировку"""
    if not db.reconnect_if_needed():
        return False

    cur = db.cursor
    cur.execute("""
        SELECT 1 FROM group_attendances 
        WHERE group_training_id=%s AND client_id=%s
        LIMIT 1
    """, (group_training_id, client_id))
    return cur.fetchone() is not None
