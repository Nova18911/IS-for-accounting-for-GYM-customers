from src.database.connector import db


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
