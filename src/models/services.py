from src.database.connector import db


class Service:
    def __init__(self, service_id=None, service_name="", price=0, hall_id=None):
        self.service_id = service_id
        self.service_name = service_name
        self.price = price
        self.hall_id = hall_id

    def __str__(self):
        return f"{self.service_name} - {self.price} руб."

    def save(self):
        """Сохранить услугу в БД (добавить или обновить)"""
        if self.service_id:  # Обновление
            query = """
            UPDATE services 
            SET service_name = %s, price = %s, hall_id = %s
            WHERE service_id = %s
            """
            params = (self.service_name, self.price, self.hall_id, self.service_id)
            result = db.execute_query(query, params)
            return result is not None
        else:  # Добавление
            query = """
            INSERT INTO services (service_name, price, hall_id)
            VALUES (%s, %s, %s)
            """
            params = (self.service_name, self.price, self.hall_id)
            result = db.execute_query(query, params)

            if result:
                # Получаем ID новой записи
                query = "SELECT LAST_INSERT_ID()"
                result = db.execute_query(query)
                if result:
                    self.service_id = result[0][0]
            return result is not None

    def delete(self):
        """Удалить услугу из БД"""
        if not self.service_id:
            return False

        query = "DELETE FROM services WHERE service_id = %s"
        result = db.execute_query(query, (self.service_id,))
        return result is not None

    @staticmethod
    def get_all():
        """Получить все услуги из БД"""
        query = """
        SELECT s.service_id, s.service_name, s.price, s.hall_id, 
               h.hall_name, h.capacity
        FROM services s 
        LEFT JOIN halls h ON s.hall_id = h.hall_id
        ORDER BY s.service_name
        """
        result = db.execute_query(query)

        services = []
        if result:
            for row in result:
                service = Service(
                    service_id=row[0],
                    service_name=row[1],
                    price=row[2],
                    hall_id=row[3]
                )
                services.append(service)
        return services

    @staticmethod
    def get_by_id(service_id):
        """Получить услугу по ID"""
        query = """
        SELECT service_name, price, hall_id
        FROM services 
        WHERE service_id = %s
        """
        result = db.execute_query(query, (service_id,))

        if result and len(result) > 0:
            service_name, price, hall_id = result[0]
            return Service(service_id, service_name, price, hall_id)
        return None

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'service_id': self.service_id,
            'service_name': self.service_name,
            'price': self.price,
            'hall_id': self.hall_id
        }

    @classmethod
    def from_dict(cls, data):
        """Создать объект из словаря"""
        return cls(
            service_id=data.get('service_id'),
            service_name=data.get('service_name', ''),
            price=data.get('price', 0),
            hall_id=data.get('hall_id')
        )