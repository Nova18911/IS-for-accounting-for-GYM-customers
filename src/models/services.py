# src/models/services.py
from typing import Optional, List, Dict, Any
from src.database.connector import db

class Service:
    def __init__(self, service_id: Optional[int], service_name: str, price: Optional[int], hall_id: Optional[int]):
        self.service_id = service_id
        self.service_name = service_name
        self.price = price
        self.hall_id = hall_id

    @staticmethod
    def _row_to_obj(row: tuple) -> "Service":
        raw_price = row[2]
        clean_price = int(float(raw_price)) if raw_price is not None else 0

        return Service(
            service_id=row[0],
            service_name=row[1],
            price=clean_price,
            hall_id=row[3]
        )

    @classmethod
    def get_all(cls) -> List["Service"]:
        sql = """
        SELECT service_id, service_name, price, hall_id
        FROM services
        ORDER BY service_name
        """
        rows = db.execute_query(sql)
        return [cls._row_to_obj(r) for r in rows] if rows else []

    @classmethod
    def get_by_id(cls, service_id: int) -> Optional["Service"]:
        sql = """
        SELECT service_id, service_name, price, hall_id
        FROM services
        WHERE service_id = %s
        """
        rows = db.execute_query(sql, (service_id,))
        return cls._row_to_obj(rows[0]) if rows else None

    @classmethod
    def name_exists(cls, service_name: str, exclude_id: Optional[int] = None) -> bool:
        if exclude_id is None:
            sql = "SELECT COUNT(*) FROM services WHERE service_name = %s"
            rows = db.execute_query(sql, (service_name,))
        else:
            sql = "SELECT COUNT(*) FROM services WHERE service_name = %s AND service_id != %s"
            rows = db.execute_query(sql, (service_name, exclude_id))
        return bool(rows and rows[0][0] > 0)

    def save(self) -> bool:
        """Создание или обновление услуги."""
        if getattr(self, 'service_id', None):
            # обновление
            sql = """
            UPDATE services
            SET service_name = %s, price = %s, hall_id = %s
            WHERE service_id = %s
            """
            res = db.execute_query(sql, (self.service_name, self.price, self.hall_id, self.service_id))
            return res is not None
        else:
            # создание
            sql = """
            INSERT INTO services (service_name, price, hall_id)
            VALUES (%s, %s, %s)
            """
            res = db.execute_query(sql, (self.service_name, self.price, self.hall_id))
            if res is None:
                return False
            self.service_id = db.get_last_insert_id()
            return True

    def delete(self) -> bool:
        if not getattr(self, 'service_id', None):
            return False
        sql = "DELETE FROM services WHERE service_id = %s"
        res = db.execute_query(sql, (self.service_id,))
        return res is not None


# -------------------------
# Functional API expected by views (wrappers)
# -------------------------
def _service_obj_to_dict(svc: Service) -> Dict[str, Any]:
    return {
        "service_id": svc.service_id,
        "service_name": svc.service_name,
        "price": svc.price,
        "hall_id": svc.hall_id
    }

def get_all_services() -> List[Dict[str, Any]]:
    """Возвращает список словарей (для совместимости с views)."""
    objs = Service.get_all()
    return [_service_obj_to_dict(s) for s in objs]

def get_service_by_id(service_id: int) -> Optional[Dict[str, Any]]:
    svc = Service.get_by_id(service_id)
    return _service_obj_to_dict(svc) if svc else None

def name_exists(service_name: str, exclude_id: Optional[int] = None) -> bool:
    return Service.name_exists(service_name, exclude_id)

def create_service(service_name: str, price: int, hall_id: Optional[int]) -> Optional[int]:
    s = Service(service_id=None, service_name=service_name, price=price, hall_id=hall_id)
    ok = s.save()
    return s.service_id if ok else None

def update_service(service_id: int, service_name: str, price: int, hall_id: Optional[int]) -> bool:
    s = Service.get_by_id(service_id)
    if not s:
        return False
    s.service_name = service_name
    s.price = price
    s.hall_id = hall_id
    return s.save()

def delete_service(service_id: int) -> bool:
    s = Service.get_by_id(service_id)
    if not s:
        return False
    return s.delete()
