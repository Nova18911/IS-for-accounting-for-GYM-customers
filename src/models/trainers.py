# model/trainer.py
from src.database.connector import db


class Trainer:
    def __init__(self, trainer_id=None, last_name="", first_name="", middle_name="",
                 photo=None, phone="", trainer_type_id=None):
        self.trainer_id = trainer_id
        self.last_name = last_name
        self.first_name = first_name
        self.middle_name = middle_name
        self._photo = photo  # Используем приватный атрибут для фото
        self.phone = phone
        self.trainer_type_id = trainer_type_id
        # Дополнительные атрибуты для удобства
        self.trainer_type_name = None
        self.rate = None

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    def get_full_name(self):
        """Получить полное ФИО тренера"""
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
        # Принимаем как байты, так и None
        if value is None or isinstance(value, bytes):
            self._photo = value
        else:
            # Пытаемся преобразовать в байты если это не None и не bytes
            try:
                self._photo = bytes(value)
            except:
                self._photo = None

    def has_photo(self):
        """Проверяет, есть ли фото у тренера"""
        return self._photo is not None and len(self._photo) > 0

    def get_photo_size_kb(self):
        """Получить размер фото в килобайтах"""
        if self.has_photo():
            return len(self._photo) / 1024
        return 0

    def save(self):
        """Сохранить тренера в БД (добавить или обновить)"""
        try:
            if self.trainer_id:  # Обновление
                query = """
                UPDATE trainers 
                SET last_name = %s, first_name = %s, middle_name = %s, 
                    photo = %s, phone = %s, trainer_type_id = %s
                WHERE trainer_id = %s
                """
                params = (self.last_name, self.first_name, self.middle_name,
                          self._photo, self.phone, self.trainer_type_id, self.trainer_id)
                result = db.execute_query(query, params)
                return result is not None
            else:  # Добавление
                query = """
                INSERT INTO trainers (last_name, first_name, middle_name, photo, phone, trainer_type_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (self.last_name, self.first_name, self.middle_name,
                          self._photo, self.phone, self.trainer_type_id)
                result = db.execute_query(query, params)

                if result:
                    # Получаем ID новой записи
                    query = "SELECT LAST_INSERT_ID()"
                    result_id = db.execute_query(query)
                    if result_id:
                        self.trainer_id = result_id[0][0]
                return result is not None
        except Exception as e:
            print(f"Ошибка сохранения тренера: {e}")
            return False

    def delete(self):
        """Удалить тренера из БД"""
        if not self.trainer_id:
            return False

        try:
            query = "DELETE FROM trainers WHERE trainer_id = %s"
            result = db.execute_query(query, (self.trainer_id,))
            return result is not None
        except Exception as e:
            print(f"Ошибка удаления тренера: {e}")
            return False

    @staticmethod
    def get_all():
        """Получить всех тренеров из БД"""
        query = """
        SELECT t.trainer_id, t.last_name, t.first_name, t.middle_name, 
               t.photo, t.phone, t.trainer_type_id,
               tt.trainer_type_name, tt.rate
        FROM trainers t
        LEFT JOIN trainer_types tt ON t.trainer_type_id = tt.trainer_type_id
        ORDER BY t.last_name, t.first_name
        """
        result = db.execute_query(query)

        trainers = []
        if result:
            for row in result:
                trainer = Trainer(
                    trainer_id=row[0],
                    last_name=row[1],
                    first_name=row[2],
                    middle_name=row[3],
                    photo=row[4],  # Используем свойство сеттер
                    phone=row[5],
                    trainer_type_id=row[6]
                )
                # Добавляем информацию о типе тренера как дополнительные атрибуты
                trainer.trainer_type_name = row[7] if row[7] else "Не указан"
                trainer.rate = row[8] if row[8] else 0
                trainers.append(trainer)
        return trainers

    @staticmethod
    def get_by_id(trainer_id):
        """Получить тренера по ID"""
        query = """
        SELECT t.trainer_id, t.last_name, t.first_name, t.middle_name, 
               t.photo, t.phone, t.trainer_type_id,
               tt.trainer_type_name, tt.rate
        FROM trainers t
        LEFT JOIN trainer_types tt ON t.trainer_type_id = tt.trainer_type_id
        WHERE t.trainer_id = %s
        """
        result = db.execute_query(query, (trainer_id,))

        if result and len(result) > 0:
            row = result[0]
            trainer = Trainer(
                trainer_id=row[0],
                last_name=row[1],
                first_name=row[2],
                middle_name=row[3],
                photo=row[4],  # Используем свойство сеттер
                phone=row[5],
                trainer_type_id=row[6]
            )
            # Добавляем информацию о типе тренера
            trainer.trainer_type_name = row[7] if row[7] else "Не указан"
            trainer.rate = row[8] if row[8] else 0
            return trainer
        return None

    @staticmethod
    def search_by_last_name(last_name):
        """Поиск тренеров по фамилии"""
        query = """
        SELECT t.trainer_id, t.last_name, t.first_name, t.middle_name, 
               t.photo, t.phone, t.trainer_type_id,
               tt.trainer_type_name
        FROM trainers t
        LEFT JOIN trainer_types tt ON t.trainer_type_id = tt.trainer_type_id
        WHERE t.last_name LIKE %s
        ORDER BY t.last_name, t.first_name
        """
        result = db.execute_query(query, (f"%{last_name}%",))

        trainers = []
        if result:
            for row in result:
                trainer = Trainer(
                    trainer_id=row[0],
                    last_name=row[1],
                    first_name=row[2],
                    middle_name=row[3],
                    photo=row[4],  # Используем свойство сеттер
                    phone=row[5],
                    trainer_type_id=row[6]
                )
                trainer.trainer_type_name = row[7] if row[7] else "Не указан"
                trainers.append(trainer)
        return trainers

    @staticmethod
    def search_by_phone(phone):
        """Поиск тренеров по телефону"""
        query = """
        SELECT t.trainer_id, t.last_name, t.first_name, t.middle_name, 
               t.photo, t.phone, t.trainer_type_id,
               tt.trainer_type_name
        FROM trainers t
        LEFT JOIN trainer_types tt ON t.trainer_type_id = tt.trainer_type_id
        WHERE t.phone LIKE %s
        ORDER BY t.last_name, t.first_name
        """
        result = db.execute_query(query, (f"%{phone}%",))

        trainers = []
        if result:
            for row in result:
                trainer = Trainer(
                    trainer_id=row[0],
                    last_name=row[1],
                    first_name=row[2],
                    middle_name=row[3],
                    photo=row[4],  # Используем свойство сеттер
                    phone=row[5],
                    trainer_type_id=row[6]
                )
                trainer.trainer_type_name = row[7] if row[7] else "Не указан"
                trainers.append(trainer)
        return trainers

    @staticmethod
    def get_by_trainer_type(trainer_type_id):
        """Получить тренеров по типу тренера"""
        query = """
        SELECT t.trainer_id, t.last_name, t.first_name, t.middle_name, 
               t.photo, t.phone, t.trainer_type_id
        FROM trainers t
        WHERE t.trainer_type_id = %s
        ORDER BY t.last_name, t.first_name
        """
        result = db.execute_query(query, (trainer_type_id,))

        trainers = []
        if result:
            for row in result:
                trainer = Trainer(
                    trainer_id=row[0],
                    last_name=row[1],
                    first_name=row[2],
                    middle_name=row[3],
                    photo=row[4],  # Используем свойство сеттер
                    phone=row[5],
                    trainer_type_id=row[6]
                )
                trainers.append(trainer)
        return trainers

    def get_trainings_count(self, period_start=None, period_end=None):
        """Получить количество тренировок тренера за период"""
        try:
            query = """
            SELECT COUNT(*) FROM group_schedule 
            WHERE trainer_id = %s
            """
            params = [self.trainer_id]

            if period_start and period_end:
                query += " AND date BETWEEN %s AND %s"
                params.extend([period_start, period_end])

            result = db.execute_query(query, tuple(params))
            if result:
                return result[0][0]
            return 0
        except Exception as e:
            print(f"Ошибка получения количества тренировок: {e}")
            return 0

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'trainer_id': self.trainer_id,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'has_photo': self.has_photo(),
            'phone': self.phone,
            'trainer_type_id': self.trainer_type_id,
            'trainer_type_name': self.trainer_type_name,
            'rate': self.rate,
            'full_name': self.get_full_name()
        }

    @classmethod
    def from_dict(cls, data):
        """Создать объект из словаря"""
        trainer = cls(
            trainer_id=data.get('trainer_id'),
            last_name=data.get('last_name', ''),
            first_name=data.get('first_name', ''),
            middle_name=data.get('middle_name', ''),
            phone=data.get('phone', ''),
            trainer_type_id=data.get('trainer_type_id')
        )
        # Устанавливаем фото отдельно если оно есть
        if 'photo' in data:
            trainer.photo = data['photo']
        return trainer