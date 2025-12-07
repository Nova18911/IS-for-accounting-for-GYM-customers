# model/group_training.py
from src.database.connector import db
from datetime import datetime


class GroupTraining:
    def __init__(self, group_training_id=None, training_date=None, start_time=None,
                 trainer_id=None, service_id=None):
        self.group_training_id = group_training_id
        self.training_date = training_date
        self.start_time = start_time
        self.trainer_id = trainer_id
        self.service_id = service_id

    def __str__(self):
        return f"Групповая тренировка {self.training_date} {self.start_time}"

    def save(self):
        """Сохранить групповую тренировку в БД"""
        if self.group_training_id:  # Обновление
            query = """
            UPDATE group_trainings 
            SET training_date = %s, start_time = %s, trainer_id = %s, service_id = %s
            WHERE group_training_id = %s
            """
            params = (self.training_date, self.start_time, self.trainer_id,
                      self.service_id, self.group_training_id)
            result = db.execute_query(query, params)
            return result is not None
        else:  # Добавление
            query = """
            INSERT INTO group_trainings (training_date, start_time, trainer_id, service_id)
            VALUES (%s, %s, %s, %s)
            """
            params = (self.training_date, self.start_time, self.trainer_id, self.service_id)
            result = db.execute_query(query, params)

            if result:
                # Получаем ID новой записи
                query = "SELECT LAST_INSERT_ID()"
                result = db.execute_query(query)
                if result:
                    self.group_training_id = result[0][0]
            return result is not None

    def delete(self):
        """Удалить групповую тренировку из БД"""
        if not self.group_training_id:
            return False

        query = "DELETE FROM group_trainings WHERE group_training_id = %s"
        result = db.execute_query(query, (self.group_training_id,))
        return result is not None

    @staticmethod
    def get_all_in_week(start_date, end_date):
        """Получить все групповые тренировки за неделю"""
        query = """
        SELECT gt.group_training_id, gt.training_date, gt.start_time, 
               gt.trainer_id, gt.service_id,
               t.last_name, t.first_name, t.middle_name,
               s.service_name, h.hall_name, h.capacity
        FROM group_trainings gt
        LEFT JOIN trainers t ON gt.trainer_id = t.trainer_id
        LEFT JOIN services s ON gt.service_id = s.service_id
        LEFT JOIN halls h ON s.hall_id = h.hall_id
        WHERE gt.training_date BETWEEN %s AND %s
        ORDER BY gt.training_date, gt.start_time
        """
        result = db.execute_query(query, (start_date, end_date))

        trainings = []
        if result:
            for row in result:
                training = GroupTraining(
                    group_training_id=row[0],
                    training_date=row[1],
                    start_time=row[2],
                    trainer_id=row[3],
                    service_id=row[4]
                )
                # Добавляем дополнительную информацию
                if row[5] and row[6]:
                    training.trainer_name = f"{row[5]} {row[6]}"
                    if row[7]:
                        training.trainer_name += f" {row[7]}"
                else:
                    training.trainer_name = "Не указан"

                training.service_name = row[8] if row[8] else "Не указана"
                training.hall_name = row[9] if row[9] else "Не указан"
                training.capacity = row[10] if row[10] else 0

                trainings.append(training)
        return trainings

    @staticmethod
    def get_by_id(group_training_id):
        """Получить групповую тренировку по ID"""
        query = """
        SELECT training_date, start_time, trainer_id, service_id
        FROM group_trainings 
        WHERE group_training_id = %s
        """
        result = db.execute_query(query, (group_training_id,))

        if result and len(result) > 0:
            training_date, start_time, trainer_id, service_id = result[0]
            return GroupTraining(group_training_id, training_date, start_time, trainer_id, service_id)
        return None

    @staticmethod
    def get_by_datetime(training_date, start_time):
        """Получить тренировки по дате и времени"""
        query = """
        SELECT gt.group_training_id, gt.trainer_id, gt.service_id,
               t.last_name, t.first_name, s.service_name
        FROM group_trainings gt
        LEFT JOIN trainers t ON gt.trainer_id = t.trainer_id
        LEFT JOIN services s ON gt.service_id = s.service_id
        WHERE gt.training_date = %s AND gt.start_time = %s
        ORDER BY gt.start_time
        """
        result = db.execute_query(query, (training_date, start_time))

        trainings = []
        if result:
            for row in result:
                training = GroupTraining(
                    group_training_id=row[0],
                    training_date=training_date,
                    start_time=start_time,
                    trainer_id=row[1],
                    service_id=row[2]
                )
                if row[3] and row[4]:
                    training.trainer_name = f"{row[3]} {row[4]}"
                else:
                    training.trainer_name = "Не указан"

                training.service_name = row[5] if row[5] else "Не указана"
                trainings.append(training)
        return trainings

    @staticmethod
    def check_trainer_availability(trainer_id, training_date, start_time, exclude_id=None):
        """Проверить, свободен ли тренер в указанное время"""
        if exclude_id:
            query = """
            SELECT COUNT(*) FROM group_trainings 
            WHERE trainer_id = %s AND training_date = %s AND start_time = %s 
            AND group_training_id != %s
            """
            result = db.execute_query(query, (trainer_id, training_date, start_time, exclude_id))
        else:
            query = """
            SELECT COUNT(*) FROM group_trainings 
            WHERE trainer_id = %s AND training_date = %s AND start_time = %s
            """
            result = db.execute_query(query, (trainer_id, training_date, start_time))

        if result:
            return result[0][0] == 0
        return True

    @staticmethod
    def check_hall_availability(hall_id, training_date, start_time, exclude_id=None):
        """Проверить, свободен ли зал в указанное время"""
        if exclude_id:
            query = """
            SELECT COUNT(*) FROM group_trainings gt
            JOIN services s ON gt.service_id = s.service_id
            WHERE s.hall_id = %s AND gt.training_date = %s AND gt.start_time = %s
            AND gt.group_training_id != %s
            """
            result = db.execute_query(query, (hall_id, training_date, start_time, exclude_id))
        else:
            query = """
            SELECT COUNT(*) FROM group_trainings gt
            JOIN services s ON gt.service_id = s.service_id
            WHERE s.hall_id = %s AND gt.training_date = %s AND gt.start_time = %s
            """
            result = db.execute_query(query, (hall_id, training_date, start_time))

        if result:
            return result[0][0] == 0
        return True

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'group_training_id': self.group_training_id,
            'training_date': self.training_date,
            'start_time': self.start_time,
            'trainer_id': self.trainer_id,
            'service_id': self.service_id
        }

    @classmethod
    def from_dict(cls, data):
        """Создать объект из словаря"""
        return cls(
            group_training_id=data.get('group_training_id'),
            training_date=data.get('training_date'),
            start_time=data.get('start_time'),
            trainer_id=data.get('trainer_id'),
            service_id=data.get('service_id')
        )