# models/subscription_prices.py
from src.database.connector import db

def subscription_price_get_all():
    rows = db.execute_query("""
        SELECT subscription_price_id, duration, price
        FROM subscription_prices
        ORDER BY subscription_price_id
    """)
    return [{"id": r[0], "duration": r[1], "price": r[2]} for r in rows] if rows else []


def subscription_price_get_by_id(price_id):
    rows = db.execute_query("""
        SELECT duration, price
        FROM subscription_prices
        WHERE subscription_price_id=%s
    """, (price_id,))
    return {"id": price_id, "duration": rows[0][0], "price": rows[0][1]} if rows else None
