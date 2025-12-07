# model/halls.py
from src.database.connector import db


class Hall:
    def __init__(self, hall_id=None, hall_name="", capacity=0):
        self.hall_id = hall_id
        self.hall_name = hall_name
        self.capacity = capacity

    def __str__(self):
        return f"{self.hall_name} (вместимость: {self.capacity})"

    def save(self):
        """Сохранить зал в БД (добавить или обновить)"""
        if self.hall_id:  # Обновление существующего зала
            query = """
            UPDATE halls 
            SET hall_name = %s, capacity = %s
            WHERE hall_id = %s
            """
            params = (self.hall_name, self.capacity, self.hall_id)
            result = db.execute_query(query, params)
            return result is not None
        else:  # Добавление нового зала
            query = """
            INSERT INTO halls (hall_name, capacity)
            VALUES (%s, %s)
            """
            params = (self.hall_name, self.capacity)
            result = db.execute_query(query, params)

            if result:
                # Получаем ID новой записи
                query = "SELECT LAST_INSERT_ID()"
                result = db.execute_query(query)
                if result:
                    self.hall_id = result[0][0]
            return result is not None

    def delete(self):
        """Удалить зал из БД"""
        if not self.hall_id:
            return False

        query = "DELETE FROM halls WHERE hall_id = %s"
        result = db.execute_query(query, (self.hall_id,))
        return result is not None

    @staticmethod
    def get_all():
        """Получить все залы из БД"""
        query = "SELECT hall_id, hall_name, capacity FROM halls ORDER BY hall_name"
        result = db.execute_query(query)

        halls = []
        if result:
            for row in result:
                hall = Hall(hall_id=row[0], hall_name=row[1], capacity=row[2])
                halls.append(hall)
        return halls

    @staticmethod
    def get_by_id(hall_id):
        """Получить зал по ID"""
        query = "SELECT hall_name, capacity FROM halls WHERE hall_id = %s"
        result = db.execute_query(query, (hall_id,))

        if result and len(result) > 0:
            hall_name, capacity = result[0]
            return Hall(hall_id, hall_name, capacity)
        return None

    @staticmethod
    def check_name_exists(hall_name, exclude_id=None):
        """Проверить, существует ли зал с таким названием"""
        if exclude_id:
            query = "SELECT COUNT(*) FROM halls WHERE hall_name = %s AND hall_id != %s"
            result = db.execute_query(query, (hall_name, exclude_id))
        else:
            query = "SELECT COUNT(*) FROM halls WHERE hall_name = %s"
            result = db.execute_query(query, (hall_name,))

        if result:
            return result[0][0] > 0
        return False

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'hall_id': self.hall_id,
            'hall_name': self.hall_name,
            'capacity': self.capacity
        }

    @classmethod
    def from_dict(cls, data):
        """Создать объект из словаря"""
        return cls(
            hall_id=data.get('hall_id'),
            hall_name=data.get('hall_name', ''),
            capacity=data.get('capacity', 0)
        )