from src.database.connector import db


# -----------------------------
# Типы тренеров
# -----------------------------

def trainer_type_get_all():
    """Возвращает список всех типов тренеров как list[dict]."""
    rows = db.execute_query(
        "SELECT trainer_type_id, trainer_type_name, rate FROM trainer_types ORDER BY trainer_type_name"
    )
    if not rows:
        return []
    return [
        {
            "trainer_type_id": r[0],
            "trainer_type_name": r[1],
            "rate": r[2]
        }
        for r in rows
    ]


def trainer_type_get_by_id(type_id: int):
    """Возвращает один тип тренера по ID (dict) или None."""
    rows = db.execute_query(
        "SELECT trainer_type_id, trainer_type_name, rate FROM trainer_types WHERE trainer_type_id=%s",
        (type_id,)
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "trainer_type_id": r[0],
        "trainer_type_name": r[1],
        "rate": r[2]
    }


# -----------------------------
# Тренеры
# -----------------------------

def trainer_get_all():
    """Возвращает список всех тренеров с типом и ставкой."""
    query = """
    SELECT t.trainer_id, t.last_name, t.first_name, t.middle_name,
           t.phone, t.email, t.photo,
           t.trainer_type_id, tt.trainer_type_name, tt.rate
    FROM trainers t
    JOIN trainer_types tt ON t.trainer_type_id = tt.trainer_type_id
    ORDER BY t.last_name, t.first_name
    """
    rows = db.execute_query(query)
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
            "photo": r[6],
            "trainer_type_id": r[7],
            "trainer_type_name": r[8],
            "rate": r[9]
        }
        for r in rows
    ]


def trainer_get_by_id(trainer_id):
    """Возвращает одного тренера с типом и ставкой по ID."""
    query = """
    SELECT t.trainer_id, t.last_name, t.first_name, t.middle_name,
           t.phone, t.email, t.photo,
           t.trainer_type_id, tt.trainer_type_name, tt.rate
    FROM trainers t
    JOIN trainer_types tt ON t.trainer_type_id = tt.trainer_type_id
    WHERE t.trainer_id=%s
    """
    rows = db.execute_query(query, (trainer_id,))
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
        "photo": r[6],
        "trainer_type_id": r[7],
        "trainer_type_name": r[8],
        "rate": r[9]
    }
