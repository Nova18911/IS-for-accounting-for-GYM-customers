from src.database.connector import db
from datetime import datetime, timedelta

DURATION_MAP = {
    '1 месяц': 30,
    '3 месяца': 90,
    'полгода': 180,
    'год': 365
}

def subscription_get_by_id(subscription_id):
    rows = db.execute_query(
        "SELECT subscription_id, start_date, subscription_price_id FROM subscriptions WHERE subscription_id=%s",
        (subscription_id,)
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "subscription_id": r[0],
        "start_date": r[1],
        "subscription_price_id": r[2]
    }

def subscription_create(start_date, price_id):
    sql = "INSERT INTO subscriptions (start_date, subscription_price_id) VALUES (%s, %s)"
    db.execute_query(sql, (start_date, price_id))
    return db.get_last_insert_id()

def subscription_update(subscription_id, start_date, price_id):
    sql = "UPDATE subscriptions SET start_date=%s, subscription_price_id=%s WHERE subscription_id=%s"
    db.execute_query(sql, (start_date, price_id, subscription_id))
    return True

def subscription_delete(subscription_id):
    db.execute_query("DELETE FROM subscriptions WHERE subscription_id=%s", (subscription_id,))
    return True

def subscription_attach_to_client(subscription_id, client_id):
    sql = "UPDATE clients SET subscription_id=%s WHERE client_id=%s"
    db.execute_query(sql, (subscription_id, client_id))
    return True

def subscription_detach_client(client_id):
    db.execute_query("UPDATE clients SET subscription_id=NULL WHERE client_id=%s", (client_id,))
    return True

def subscription_calculate_end(start_date, duration):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    days = DURATION_MAP.get(duration, 30)
    return start_date + timedelta(days=days)
