# models/client.py
from src.database.connector import db
from datetime import datetime, timedelta


class Client:
    def __init__(self, client_id=None, last_name="", first_name="", middle_name="",
                 photo=None, phone="", email="", card_number="", is_active=True):
        self.client_id = client_id
        self.last_name = last_name
        self.first_name = first_name
        self.middle_name = middle_name
        self._photo = photo  # Приватный атрибут для фото
        self.phone = phone
        self.email = email
        self.card_number = card_number
        self.is_active = is_active

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    def get_full_name(self):
        """Получить полное ФИО клиента"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    @property
    def photo(self):
        """Геттер для фото"""
        return self._photo

    @photo.setter
    def photo(self, value):
        """Сеттер для фото с проверкой типа"""
        if value is None or isinstance(value, bytes):
            self._photo = value
        else:
            try:
                self._photo = bytes(value)
            except:
                self._photo = None

    def has_photo(self):
        """Проверяет, есть ли фото у клиента"""
        return self._photo is not None and len(self._photo) > 0

    def get_photo_size_kb(self):
        """Получить размер фото в килобайтах"""
        if self.has_photo():
            return len(self._photo) / 1024
        return 0

    def save(self):
        """Сохранить клиента в БД (добавить или обновить)"""
        try:
            if self.client_id:  # Обновление
                query = """
                UPDATE clients 
                SET last_name = %s, first_name = %s, middle_name = %s, 
                    photo = %s, phone = %s, email = %s, 
                    card_number = %s, is_active = %s
                WHERE client_id = %s
                """
                params = (self.last_name, self.first_name, self.middle_name,
                          self._photo, self.phone, self.email,
                          self.card_number, self.is_active, self.client_id)
                result = db.execute_query(query, params)
                return result is not None
            else:  # Добавление
                query = """
                INSERT INTO clients (last_name, first_name, middle_name, 
                                    photo, phone, email, card_number, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (self.last_name, self.first_name, self.middle_name,
                          self._photo, self.phone, self.email,
                          self.card_number, self.is_active)
                result = db.execute_query(query, params)

                if result:
                    # Получаем ID новой записи
                    query = "SELECT LAST_INSERT_ID()"
                    result_id = db.execute_query(query)
                    if result_id:
                        self.client_id = result_id[0][0]
                return result is not None
        except Exception as e:
            print(f"Ошибка сохранения клиента: {e}")
            return False

    def delete(self):
        """Удалить клиента из БД"""
        if not self.client_id:
            return False

        try:
            query = "DELETE FROM clients WHERE client_id = %s"
            result = db.execute_query(query, (self.client_id,))
            return result is not None
        except Exception as e:
            print(f"Ошибка удаления клиента: {e}")
            return False

    @staticmethod
    def get_all():
        """Получить всех клиентов из БД"""
        query = """
        SELECT client_id, last_name, first_name, middle_name, 
               photo, phone, email, card_number, is_active
        FROM clients
        ORDER BY last_name, first_name
        """
        result = db.execute_query(query)

        clients = []
        if result:
            for row in result:
                client = Client(
                    client_id=row[0],
                    last_name=row[1],
                    first_name=row[2],
                    middle_name=row[3],
                    photo=row[4],
                    phone=row[5],
                    email=row[6],
                    card_number=row[7],
                    is_active=bool(row[8])
                )
                clients.append(client)
        return clients

    @staticmethod
    def get_by_id(client_id):
        """Получить клиента по ID"""
        query = """
        SELECT last_name, first_name, middle_name, photo, phone, 
               email, card_number, is_active
        FROM clients 
        WHERE client_id = %s
        """
        result = db.execute_query(query, (client_id,))

        if result and len(result) > 0:
            row = result[0]
            return Client(
                client_id=client_id,
                last_name=row[0],
                first_name=row[1],
                middle_name=row[2],
                photo=row[3],
                phone=row[4],
                email=row[5],
                card_number=row[6],
                is_active=bool(row[7])
            )
        return None

    @staticmethod
    def get_by_card_number(card_number):
        """Получить клиента по номеру карты"""
        query = """
        SELECT client_id, last_name, first_name, middle_name, 
               photo, phone, email, is_active
        FROM clients 
        WHERE card_number = %s
        """
        result = db.execute_query(query, (card_number,))

        if result and len(result) > 0:
            row = result[0]
            return Client(
                client_id=row[0],
                last_name=row[1],
                first_name=row[2],
                middle_name=row[3],
                photo=row[4],
                phone=row[5],
                email=row[6],
                card_number=card_number,
                is_active=bool(row[7])
            )
        return None

    @staticmethod
    def search_by_last_name(last_name):
        """Поиск клиентов по фамилии"""
        query = """
        SELECT client_id, last_name, first_name, middle_name, 
               phone, email, card_number, is_active
        FROM clients
        WHERE last_name LIKE %s
        ORDER BY last_name, first_name
        """
        result = db.execute_query(query, (f"%{last_name}%",))

        clients = []
        if result:
            for row in result:
                client = Client(
                    client_id=row[0],
                    last_name=row[1],
                    first_name=row[2],
                    middle_name=row[3],
                    phone=row[4],
                    email=row[5],
                    card_number=row[6],
                    is_active=bool(row[7])
                )
                clients.append(client)
        return clients

    @staticmethod
    def search_by_phone(phone):
        """Поиск клиентов по телефону"""
        query = """
        SELECT client_id, last_name, first_name, middle_name, 
               phone, email, card_number, is_active
        FROM clients
        WHERE phone LIKE %s
        ORDER BY last_name, first_name
        """
        result = db.execute_query(query, (f"%{phone}%",))

        clients = []
        if result:
            for row in result:
                client = Client(
                    client_id=row[0],
                    last_name=row[1],
                    first_name=row[2],
                    middle_name=row[3],
                    phone=row[4],
                    email=row[5],
                    card_number=row[6],
                    is_active=bool(row[7])
                )
                clients.append(client)
        return clients

    def get_active_subscription(self):
        """Получить активный абонемент клиента"""
        from src.models.subscriptions import Subscription
        return Subscription.get_active_by_client_id(self.client_id)

    def get_subscriptions_history(self):
        """Получить историю абонементов клиента"""
        from src.models.subscriptions import Subscription
        return Subscription.get_by_client_id(self.client_id)

    def get_group_trainings(self):
        """Получить групповые тренировки клиента"""
        try:
            query = """
            SELECT gs.id, gs.date, gs.time, s.name as service_name,
                   t.last_name, t.first_name, t.middle_name
            FROM group_registrations gr
            JOIN group_schedule gs ON gr.group_schedule_id = gs.id
            JOIN services s ON gs.service_id = s.id
            JOIN trainers t ON gs.trainer_id = t.trainer_id
            WHERE gr.client_id = %s
            ORDER BY gs.date DESC, gs.time DESC
            """
            result = db.execute_query(query, (self.client_id,))
            return result if result else []
        except Exception as e:
            print(f"Ошибка получения групповых тренировок: {e}")
            return []

    def get_personal_trainings(self):
        """Получить персональные тренировки клиента"""
        try:
            query = """
            SELECT ps.id, ps.date, ps.time, 
                   t.last_name, t.first_name, t.middle_name
            FROM personal_schedule ps
            JOIN trainers t ON ps.trainer_id = t.trainer_id
            WHERE ps.client_id = %s
            ORDER BY ps.date DESC, ps.time DESC
            """
            result = db.execute_query(query, (self.client_id,))
            return result if result else []
        except Exception as e:
            print(f"Ошибка получения персональных тренировок: {e}")
            return []

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'client_id': self.client_id,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'has_photo': self.has_photo(),
            'phone': self.phone,
            'email': self.email,
            'card_number': self.card_number,
            'is_active': self.is_active,
            'full_name': self.get_full_name()
        }

    @classmethod
    def from_dict(cls, data):
        """Создать объект из словаря"""
        client = cls(
            client_id=data.get('client_id'),
            last_name=data.get('last_name', ''),
            first_name=data.get('first_name', ''),
            middle_name=data.get('middle_name', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            card_number=data.get('card_number', ''),
            is_active=data.get('is_active', True)
        )
        if 'photo' in data:
            client.photo = data['photo']
        return client