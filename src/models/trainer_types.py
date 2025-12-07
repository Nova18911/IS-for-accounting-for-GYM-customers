# model/trainer_types.py
from src.database.connector import db

class TrainerType:
    def __init__(self, trainer_type_id=None, trainer_type_name="", rate=0):
        self.trainer_type_id = trainer_type_id
        self.trainer_type_name = trainer_type_name
        self.rate = rate

    def __str__(self):
        return f"{self.trainer_type_name} ({self.rate} руб.)"

    @staticmethod
    def get_all():
        """Получить все типы тренеров из БД"""
        query = "SELECT trainer_type_id, trainer_type_name, rate FROM trainer_types ORDER BY trainer_type_name"
        result = db.execute_query(query)

        types = []
        if result:
            for row in result:
                trainer_type = TrainerType(
                    trainer_type_id=row[0],
                    trainer_type_name=row[1],
                    rate=row[2]
                )
                types.append(trainer_type)
        return types

    @staticmethod
    def get_by_id(trainer_type_id):
        """Получить тип тренера по ID"""
        query = "SELECT trainer_type_name, rate FROM trainer_types WHERE trainer_type_id = %s"
        result = db.execute_query(query, (trainer_type_id,))

        if result and len(result) > 0:
            trainer_type_name, rate = result[0]
            return TrainerType(trainer_type_id, trainer_type_name, rate)
        return None

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'trainer_type_id': self.trainer_type_id,
            'trainer_type_name': self.trainer_type_name,
            'rate': self.rate
        }

    @classmethod
    def from_dict(cls, data):
        """Создать объект из словаря"""
        return cls(
            trainer_type_id=data.get('trainer_type_id'),
            trainer_type_name=data.get('trainer_type_name', ''),
            rate=data.get('rate', 0)
        )