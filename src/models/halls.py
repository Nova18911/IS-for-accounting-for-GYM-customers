# src/models/halls.py
from typing import Optional, List
from src.database.connector import db


class Hall:
    def __init__(self, hall_id: Optional[int] = None, hall_name: str = "", capacity: int = 0):
        self.hall_id = hall_id
        self.hall_name = hall_name
        self.capacity = capacity

    # -------------------------
    # Преобразование строки из БД в объект
    # -------------------------
    @staticmethod
    def _row_to_obj(row: tuple) -> "Hall":
        return Hall(hall_id=row[0], hall_name=row[1], capacity=row[2])

    # -------------------------
    # CRUD
    # -------------------------
    @classmethod
    def get_all(cls) -> List["Hall"]:
        sql = "SELECT hall_id, hall_name, capacity FROM halls ORDER BY hall_name"
        rows = db.execute_query(sql)
        return [cls._row_to_obj(r) for r in rows] if rows else []

    @classmethod
    def get_by_id(cls, hall_id: int) -> Optional["Hall"]:
        sql = "SELECT hall_id, hall_name, capacity FROM halls WHERE hall_id=%s"
        rows = db.execute_query(sql, (hall_id,))
        return cls._row_to_obj(rows[0]) if rows else None

    @classmethod
    def name_exists(cls, hall_name: str, exclude_id: Optional[int] = None) -> bool:
        if exclude_id:
            sql = "SELECT COUNT(*) FROM halls WHERE hall_name=%s AND hall_id != %s"
            rows = db.execute_query(sql, (hall_name, exclude_id))
        else:
            sql = "SELECT COUNT(*) FROM halls WHERE hall_name=%s"
            rows = db.execute_query(sql, (hall_name,))
        return bool(rows and rows[0][0] > 0)

    def save(self) -> bool:
        """Создание или обновление зала"""
        if self.hall_id:
            # обновление
            sql = "UPDATE halls SET hall_name=%s, capacity=%s WHERE hall_id=%s"
            res = db.execute_query(sql, (self.hall_name, self.capacity, self.hall_id))
            return res is not None
        else:
            # создание
            sql = "INSERT INTO halls (hall_name, capacity) VALUES (%s, %s)"
            res = db.execute_query(sql, (self.hall_name, self.capacity))
            if res is None:
                return False
            last_id = db.execute_query("SELECT LAST_INSERT_ID()")
            if last_id:
                self.hall_id = last_id[0][0]
                return True
            return False

    def delete(self) -> bool:
        if not self.hall_id:
            return False
        sql = "DELETE FROM halls WHERE hall_id=%s"
        res = db.execute_query(sql, (self.hall_id,))
        return res is not None

    # -------------------------
    # Обёртки для UI
    # -------------------------
    @staticmethod
    def create(hall_name: str, capacity: int) -> Optional["Hall"]:
        hall = Hall(hall_name=hall_name, capacity=capacity)
        if hall.save():
            return hall
        return None
