# models/client.py
from src.database.connector import db
from datetime import datetime, timedelta

DURATION_MAP = {
    '1 месяц': 30,
    '3 месяца': 90,
    'полгода': 180,
    'год': 365
}

# -----------------------------
# Helpers
# -----------------------------
def calc_subscription_status(start_date, duration):
    if not start_date or not duration:
        return None, False

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    days = DURATION_MAP.get(duration, 30)
    end_date = start_date + timedelta(days=days)
    return end_date, end_date >= datetime.now().date()


# -----------------------------
# CRUD
# -----------------------------
def client_create(last_name, first_name, middle_name, photo, phone, email, subscription_id=None):
    sql = """
        INSERT INTO clients (last_name, first_name, middle_name, photo, phone, email, subscription_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    db.execute_query(sql, (last_name, first_name, middle_name, photo, phone, email, subscription_id))
    return db.get_last_insert_id()


def client_update(client_id, last_name, first_name, middle_name, photo, phone, email, subscription_id):
    sql = """
        UPDATE clients 
        SET last_name=%s, first_name=%s, middle_name=%s, photo=%s,
            phone=%s, email=%s, subscription_id=%s
        WHERE client_id=%s
    """
    db.execute_query(sql, (last_name, first_name, middle_name, photo,
                           phone, email, subscription_id, client_id))
    return True


def client_delete(client_id):
    sql = "DELETE FROM clients WHERE client_id=%s"
    db.execute_query(sql, (client_id,))
    return True


# -----------------------------
# SELECT
# -----------------------------
BASE_QUERY = """
SELECT 
    c.client_id, c.last_name, c.first_name, c.middle_name,
    c.photo, c.phone, c.email, c.subscription_id,
    s.start_date, sp.duration, sp.price, sp.subscription_price_id
FROM clients c
LEFT JOIN subscriptions s ON c.subscription_id = s.subscription_id
LEFT JOIN subscription_prices sp ON s.subscription_price_id = sp.subscription_price_id
"""


def _map_client_row(row):
    if not row:
        return None
    client = {
        "client_id": row[0],
        "last_name": row[1],
        "first_name": row[2],
        "middle_name": row[3],
        "photo": row[4],
        "phone": row[5],
        "email": row[6],
        "subscription_id": row[7],
        "subscription_start_date": row[8],
        "subscription_duration": row[9],
        "subscription_price": row[10],
        "subscription_price_id": row[11]
    }

    # computed fields
    end_date, is_active = calc_subscription_status(
        client["subscription_start_date"],
        client["subscription_duration"]
    )

    client["subscription_end_date"] = end_date
    client["is_active_subscription"] = is_active

    return client


def client_get_all():
    rows = db.execute_query(BASE_QUERY + " ORDER BY c.last_name, c.first_name")
    return [_map_client_row(r) for r in rows] if rows else []


def client_get_by_id(client_id):
    rows = db.execute_query(BASE_QUERY + " WHERE c.client_id=%s", (client_id,))
    return _map_client_row(rows[0]) if rows else None


def client_search_by_last_name(text):
    rows = db.execute_query(BASE_QUERY + " WHERE c.last_name LIKE %s", (f"%{text}%",))
    return [_map_client_row(r) for r in rows] if rows else []


def client_search_by_phone(text):
    rows = db.execute_query(BASE_QUERY + " WHERE c.phone LIKE %s", (f"%{text}%",))
    return [_map_client_row(r) for r in rows] if rows else []
