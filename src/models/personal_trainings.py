from datetime import date, time
from src.database.connector import db

# -------------------- Personal Trainings --------------------

def personal_training_get_by_id(personal_training_id):
    rows = db.execute_query(
        "SELECT personal_training_id, client_id, trainer_id, training_date, start_time, price "
        "FROM personal_trainings WHERE personal_training_id=%s",
        (personal_training_id,)
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "personal_training_id": r[0],
        "client_id": r[1],
        "trainer_id": r[2],
        "training_date": r[3],
        "start_time": r[4],
        "price": r[5]
    }

def personal_training_get_by_client(client_id):
    query = """
        SELECT personal_training_id, training_date, start_time, price, trainer_id
        FROM personal_trainings
        WHERE client_id=%s
        ORDER BY training_date, start_time
    """
    rows = db.execute_query(query, (client_id,))
    return [
        {
            "personal_training_id": r[0],
            "training_date": r[1],
            "start_time": r[2],
            "price": r[3],
            "trainer_id": r[4]
        }
        for r in rows or []
    ]

def personal_training_get_by_trainer_and_date(trainer_id, training_date):
    query = """
        SELECT start_time
        FROM personal_trainings
        WHERE trainer_id=%s AND training_date=%s
    """
    rows = db.execute_query(query, (trainer_id, training_date))
    return [{"start_time": r[0]} for r in rows or []]

def personal_training_create(client_id, trainer_id, training_date, start_time, price):
    query = """
        INSERT INTO personal_trainings (client_id, trainer_id, training_date, start_time, price)
        VALUES (%s, %s, %s, %s, %s)
    """
    return db.execute_query(query, (client_id, trainer_id, training_date, start_time, price))

def personal_training_update(personal_training_id, client_id, trainer_id, training_date, start_time, price):
    query = """
        UPDATE personal_trainings
        SET client_id=%s, trainer_id=%s, training_date=%s, start_time=%s, price=%s
        WHERE personal_training_id=%s
    """
    return db.execute_query(query, (client_id, trainer_id, training_date, start_time, price, personal_training_id))

def personal_training_delete(training_id):
    query = "DELETE FROM personal_trainings WHERE personal_training_id=%s"
    return db.execute_query(query, (training_id,))


