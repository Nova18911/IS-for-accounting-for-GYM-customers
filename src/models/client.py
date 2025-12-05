from src.database.connector import db


class SimpleClient:
    """Упрощенная модель клиента с прямыми запросами к БД"""

    @staticmethod
    def get_all():
        """Получить всех клиентов"""
        query = "SELECT * FROM clients WHERE is_active = TRUE ORDER BY last_name"
        return db.execute_query(query)

    @staticmethod
    def create(data):
        """Создать нового клиента"""
        query = """
        INSERT INTO clients (last_name, first_name, phone, email)
        VALUES (%s, %s, %s, %s)
        """
        values = (data['last_name'], data['first_name'],
                  data['phone'], data['email'])
        return db.execute_query(query, values)

    @staticmethod
    def update(client_id, data):
        """Обновить клиента"""
        query = """
        UPDATE clients 
        SET last_name = %s, first_name = %s, phone = %s, email = %s
        WHERE id = %s
        """
        values = (data['last_name'], data['first_name'],
                  data['phone'], data['email'], client_id)
        return db.execute_query(query, values)