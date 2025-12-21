from src.database.connector import db


def client_get_all():
    rows = db.execute_query(
        "SELECT client_id, last_name, first_name, middle_name, phone, email, photo, subscription_id FROM clients"
    )
    if not rows:
        return []
    return [
        {
            "client_id": r[0],
            "last_name": r[1],
            "first_name": r[2],
            "middle_name": r[3],
            "phone": r[4],
            "email": r[5],
            "photo": r[6],
            "subscription_id": r[7]
        }
        for r in rows
    ]


def client_get_by_id(client_id):
    rows = db.execute_query(
        "SELECT client_id, last_name, first_name, middle_name, phone, email, photo, subscription_id "
        "FROM clients WHERE client_id=%s",
        (client_id,)
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "client_id": r[0],
        "last_name": r[1],
        "first_name": r[2],
        "middle_name": r[3],
        "phone": r[4],
        "email": r[5],
        "photo": r[6],
        "subscription_id": r[7]
    }


def client_create(last_name, first_name, middle_name, phone, email, photo=None):
    query = """
        INSERT INTO clients (last_name, first_name, middle_name, phone, email, photo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return db.execute_query(query, (last_name, first_name, middle_name, phone, email, photo))


def client_update(client_id, last_name, first_name, middle_name, phone, email, photo=None):
    query = """
        UPDATE clients
        SET last_name=%s, first_name=%s, middle_name=%s, phone=%s, email=%s, photo=%s
        WHERE client_id=%s
    """
    return db.execute_query(query, (last_name, first_name, middle_name, phone, email, photo, client_id))


def client_delete(client_id):
    query = "DELETE FROM clients WHERE client_id=%s"
    return db.execute_query(query, (client_id,))


def client_search_by_last_name(last_name):
    rows = db.execute_query(
        "SELECT client_id, last_name, first_name, middle_name, phone, email, photo, subscription_id "
        "FROM clients WHERE last_name LIKE %s",
        (f"%{last_name}%",)
    )
    if not rows:
        return []
    return [
        {
            "client_id": r[0],
            "last_name": r[1],
            "first_name": r[2],
            "middle_name": r[3],
            "phone": r[4],
            "email": r[5],
            "photo": r[6],
            "subscription_id": r[7]
        }
        for r in rows
    ]


def client_search_by_phone(phone):
    rows = db.execute_query(
        "SELECT client_id, last_name, first_name, middle_name, phone, email, photo, subscription_id "
        "FROM clients WHERE phone LIKE %s",
        (f"%{phone}%",)
    )
    if not rows:
        return []
    return [
        {
            "client_id": r[0],
            "last_name": r[1],
            "first_name": r[2],
            "middle_name": r[3],
            "phone": r[4],
            "email": r[5],
            "photo": r[6],
            "subscription_id": r[7]
        }
        for r in rows
    ]