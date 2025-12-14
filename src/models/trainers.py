from src.database.connector import db


def trainer_get_all(only_personal=False):
    """
    Возвращает всех тренеров как list[dict].
    Если only_personal=True — возвращает только тех тренеров,
    которые могут проводить персональные тренировки (Персональный + Общий).
    """
    query = """
        SELECT t.trainer_id, t.last_name, t.first_name, t.middle_name,
               t.phone, t.email, t.trainer_type_id, t.photo, tt.trainer_type_name
        FROM trainers t
        JOIN trainer_types tt ON t.trainer_type_id = tt.trainer_type_id
        ORDER BY t.last_name, t.first_name
    """
    rows = db.execute_query(query)
    trainers = [
        {
            "trainer_id": r[0],
            "last_name": r[1],
            "first_name": r[2],
            "middle_name": r[3],
            "phone": r[4],
            "email": r[5],
            "trainer_type_id": r[6],
            "photo": r[7],
            "trainer_type_name": r[8]
        }
        for r in rows or []
    ]

    if only_personal:
        trainers = [
            t for t in trainers
            if t['trainer_type_name'] in ('Персональный тренер', 'Общий тренер')
        ]

    return trainers



def trainer_get_by_id(trainer_id: int):
    rows = db.execute_query("""
        SELECT trainer_id, last_name, first_name, middle_name,
               phone, email, trainer_type_id, photo
        FROM trainers
        WHERE trainer_id = %s
    """, (trainer_id,))
    if not rows:
        return None
    r = rows[0]
    return {
        "trainer_id": r[0],
        "last_name": r[1],
        "first_name": r[2],
        "middle_name": r[3],
        "phone": r[4],
        "email": r[5],
        "trainer_type_id": r[6],
        "photo": r[7]
    }


def trainer_create(last, first, middle, photo, phone, trainer_type_id, email):
    db.execute_query("""
        INSERT INTO trainers (last_name, first_name, middle_name, photo, phone, trainer_type_id, email)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (last, first, middle, photo, phone, trainer_type_id, email))
    return db.get_last_insert_id()


def trainer_update(trainer_id, last, first, middle, photo, phone, trainer_type_id, email):
    cnt = db.execute_query("""
        UPDATE trainers
        SET last_name=%s, first_name=%s, middle_name=%s,
            photo=%s, phone=%s, trainer_type_id=%s, email=%s
        WHERE trainer_id=%s
    """, (last, first, middle, photo, phone, trainer_type_id, email, trainer_id))
    return bool(cnt)


def trainer_delete(trainer_id):
    cnt = db.execute_query("DELETE FROM trainers WHERE trainer_id=%s", (trainer_id,))
    return bool(cnt)


def trainer_search_by_last_name(text: str):
    rows = db.execute_query("""
        SELECT trainer_id, last_name, first_name, middle_name, phone, email, trainer_type_id, photo
        FROM trainers
        WHERE last_name LIKE %s
        ORDER BY last_name
    """, (f"%{text}%",))
    if not rows:
        return []
    return [
        {
            "trainer_id": r[0],
            "last_name": r[1],
            "first_name": r[2],
            "middle_name": r[3],
            "phone": r[4],
            "email": r[5],
            "trainer_type_id": r[6],
            "photo": r[7]
        }
        for r in rows
    ]


def trainer_search_by_phone(text: str):
    rows = db.execute_query("""
        SELECT trainer_id, last_name, first_name, middle_name, phone, email, trainer_type_id, photo
        FROM trainers
        WHERE phone LIKE %s
        ORDER BY last_name
    """, (f"%{text}%",))
    if not rows:
        return []
    return [
        {
            "trainer_id": r[0],
            "last_name": r[1],
            "first_name": r[2],
            "middle_name": r[3],
            "phone": r[4],
            "email": r[5],
            "trainer_type_id": r[6],
            "photo": r[7]
        }
        for r in rows
    ]
