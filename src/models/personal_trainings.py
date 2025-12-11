# models/personal_training.py
from src.database.connector import db
from datetime import datetime


class PersonalTraining:
    """Модель персональной тренировки"""

    def __init__(self, training_id=None, client_id=None, trainer_id=None,
                 training_date=None, start_time=None, price=None):
        self.personal_training_id = training_id
        self.client_id = client_id
        self.trainer_id = trainer_id
        self.training_date = training_date
        self.start_time = start_time
        self.price = price

    def save(self):
        """Сохранить тренировку в БД"""
        try:
            if self.personal_training_id:  # Обновление
                query = """
                UPDATE personal_trainings 
                SET client_id=%s, trainer_id=%s, training_date=%s, 
                    start_time=%s, price=%s
                WHERE personal_training_id=%s
                """
                params = (self.client_id, self.trainer_id, self.training_date,
                          self.start_time, self.price, self.personal_training_id)
            else:  # Добавление
                query = """
                INSERT INTO personal_trainings 
                (client_id, trainer_id, training_date, start_time, price)
                VALUES (%s, %s, %s, %s, %s)
                """
                params = (self.client_id, self.trainer_id, self.training_date,
                          self.start_time, self.price)

            result = db.execute_query(query, params)
            return result is not None

        except Exception as e:
            print(f"Ошибка сохранения тренировки: {e}")
            return False

    def delete(self):
        """Удалить тренировку из БД"""
        if not self.personal_training_id:
            return False

        try:
            query = "DELETE FROM personal_trainings WHERE personal_training_id = %s"
            result = db.execute_query(query, (self.personal_training_id,))
            return result is not None
        except Exception as e:
            print(f"Ошибка удаления тренировки: {e}")
            return False

    @staticmethod
    def get_by_id(training_id):
        """Получить тренировку по ID"""
        query = """
        SELECT client_id, trainer_id, training_date, start_time, price
        FROM personal_trainings 
        WHERE personal_training_id = %s
        """
        result = db.execute_query(query, (training_id,))

        if result and len(result) > 0:
            row = result[0]
            return PersonalTraining(
                training_id=training_id,
                client_id=row[0],
                trainer_id=row[1],
                training_date=row[2],
                start_time=row[3],
                price=row[4]
            )
        return None