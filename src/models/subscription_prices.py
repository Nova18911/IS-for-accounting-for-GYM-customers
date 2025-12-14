from src.database.connector import db

def subscription_price_get_all():
    rows = db.execute_query(
        "SELECT subscription_price_id, duration, price FROM subscription_prices ORDER BY subscription_price_id"
    )
    return [{"id": r[0], "duration": r[1], "price": r[2]} for r in rows] if rows else []

def subscription_price_get_by_id(price_id):
    rows = db.execute_query(
        "SELECT duration, price FROM subscription_prices WHERE subscription_price_id=%s",
        (price_id,)
    )
    if not rows:
        return None
    r = rows[0]
    return {"id": price_id, "duration": r[0], "price": r[1]}
