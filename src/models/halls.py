# model/halls.py
from src.database.connector import db


class Hall:
    def __init__(self, hall_id=None, hall_name="", capacity=0):
        self.hall_id = hall_id
        self.hall_name = hall_name
        self.capacity = capacity

    # ---------- CRUD ----------
    @staticmethod
    def create(hall_name, capacity):
        query = """INSERT INTO halls (hall_name, capacity) VALUES (%s, %s)"""
        db.execute_query(query, (hall_name, capacity))
        new_id = db.execute_query("SELECT LAST_INSERT_ID()")
        return Hall(hall_id=new_id[0][0], hall_name=hall_name, capacity=capacity)

    def update(self):
        query = """UPDATE halls SET hall_name=%s, capacity=%s WHERE hall_id=%s"""
        db.execute_query(query, (self.hall_name, self.capacity, self.hall_id))
        return True

    def delete(self):
        if not self.hall_id:
            return False
        db.execute_query("DELETE FROM halls WHERE hall_id=%s", (self.hall_id,))
        return True

    # ---------- READ ----------
    @staticmethod
    def get_all():
        result = db.execute_query(
            "SELECT hall_id, hall_name, capacity FROM halls ORDER BY hall_name"
        )
        return [Hall(*row) for row in result] if result else []

    @staticmethod
    def get_by_id(hall_id):
        result = db.execute_query(
            "SELECT hall_name, capacity FROM halls WHERE hall_id=%s",
            (hall_id,)
        )
        if not result:
            return None
        return Hall(hall_id, result[0][0], result[0][1])

    # ---------- VALIDATION ----------
    @staticmethod
    def name_exists(hall_name, exclude_id=None):
        if exclude_id:
            res = db.execute_query(
                "SELECT COUNT(*) FROM halls WHERE hall_name=%s AND hall_id!=%s",
                (hall_name, exclude_id)
            )
        else:
            res = db.execute_query(
                "SELECT COUNT(*) FROM halls WHERE hall_name=%s",
                (hall_name,)
            )
        return res[0][0] > 0

