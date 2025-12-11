# src/models/group_trainings.py
from src.database.connector import db
from datetime import datetime, date, time

class GroupTraining:
    """Упрощённая модель групповой тренировки."""

    def __init__(self, group_training_id=None, training_date=None, start_time=None,
                 trainer_id=None, service_id=None):
        self.group_training_id = group_training_id
        self.training_date = training_date
        self.start_time = start_time
        self.trainer_id = trainer_id
        self.service_id = service_id

        # доп. поля (удобно для UI)
        self.trainer_name = None
        self.service_name = None
        self.hall_id = None
        self.hall_name = None
        self.capacity = None

    def __str__(self):
        return f"GroupTraining({self.group_training_id}) {self.training_date} {self.start_time}"

    # -------------------
    # CRUD
    # -------------------
    def save(self):
        try:
            if self.group_training_id:
                query = """
                UPDATE group_trainings
                SET training_date=%s, start_time=%s, trainer_id=%s, service_id=%s
                WHERE group_training_id=%s
                """
                params = (self.training_date, self.start_time, self.trainer_id, self.service_id, self.group_training_id)
                return db.execute_query(query, params) is not None
            else:
                query = """
                INSERT INTO group_trainings (training_date, start_time, trainer_id, service_id)
                VALUES (%s, %s, %s, %s)
                """
                params = (self.training_date, self.start_time, self.trainer_id, self.service_id)
                res = db.execute_query(query, params)
                if res is None:
                    return False
                # получить id
                self.group_training_id = db.get_last_insert_id()
                return True
        except Exception as e:
            print("Ошибка GroupTraining.save:", e)
            return False

    def delete(self):
        if not self.group_training_id:
            return False
        try:
            return db.execute_query("DELETE FROM group_trainings WHERE group_training_id=%s", (self.group_training_id,)) is not None
        except Exception as e:
            print("Ошибка GroupTraining.delete:", e)
            return False

    # -------------------
    # SELECT / HELPERS
    # -------------------
    @staticmethod
    def _map_row_to_obj(row):
        # row expected: group_training_id, training_date, start_time, trainer_id, service_id,
        # t.last_name, t.first_name, t.middle_name, s.service_name, h.hall_name, h.capacity, h.hall_id
        gt = GroupTraining(
            group_training_id=row[0],
            training_date=row[1],
            start_time=row[2],
            trainer_id=row[3],
            service_id=row[4]
        )

        # trainer name
        try:
            if row[5] or row[6]:
                name_parts = []
                if row[5]:
                    name_parts.append(row[5])
                if row[6]:
                    name_parts.append(row[6])
                if row[7]:
                    name_parts.append(row[7])
                gt.trainer_name = " ".join(name_parts)
            else:
                gt.trainer_name = "Не указан"
        except Exception:
            gt.trainer_name = "Не указан"

        # service / hall
        try:
            gt.service_name = row[8] or "Не указана"
            gt.hall_name = row[9] or "Не указан"
            gt.capacity = row[10] or 0
            # hall_id might be placed last (if selected)
            # some SQL variants may return hall_id earlier/later; try to get it
            gt.hall_id = row[11] if len(row) > 11 else None
        except Exception:
            gt.service_name = gt.service_name or "Не указана"
            gt.hall_name = gt.hall_name or "Не указан"
        return gt

    @staticmethod
    def get_all_in_week(start_date, end_date):
        """
        Возвращает список GroupTraining между start_date и end_date (включительно).
        start_date/end_date — объекты date или строки 'YYYY-MM-DD'.
        """
        try:
            query = """
            SELECT gt.group_training_id, gt.training_date, gt.start_time, gt.trainer_id, gt.service_id,
                   t.last_name, t.first_name, t.middle_name,
                   s.service_name, h.hall_name, h.capacity, h.hall_id
            FROM group_trainings gt
            LEFT JOIN trainers t ON gt.trainer_id = t.trainer_id
            LEFT JOIN services s ON gt.service_id = s.service_id
            LEFT JOIN halls h ON s.hall_id = h.hall_id
            WHERE gt.training_date BETWEEN %s AND %s
            ORDER BY gt.training_date, gt.start_time
            """
            rows = db.execute_query(query, (start_date, end_date))
            return [GroupTraining._map_row_to_obj(r) for r in rows] if rows else []
        except Exception as e:
            print("Ошибка GroupTraining.get_all_in_week:", e)
            return []

    @staticmethod
    def get_by_id(group_training_id):
        try:
            query = """
            SELECT gt.group_training_id, gt.training_date, gt.start_time, gt.trainer_id, gt.service_id,
                   t.last_name, t.first_name, t.middle_name,
                   s.service_name, h.hall_name, h.capacity, h.hall_id
            FROM group_trainings gt
            LEFT JOIN trainers t ON gt.trainer_id = t.trainer_id
            LEFT JOIN services s ON gt.service_id = s.service_id
            LEFT JOIN halls h ON s.hall_id = h.hall_id
            WHERE gt.group_training_id = %s
            """
            rows = db.execute_query(query, (group_training_id,))
            if not rows:
                return None
            return GroupTraining._map_row_to_obj(rows[0])
        except Exception as e:
            print("Ошибка GroupTraining.get_by_id:", e)
            return None

    @staticmethod
    def check_trainer_availability(trainer_id, training_date, start_time, exclude_id=None):
        """Возвращает True если тренер свободен"""
        try:
            if exclude_id:
                query = """
                SELECT COUNT(*) FROM group_trainings
                WHERE trainer_id=%s AND training_date=%s AND start_time=%s AND group_training_id != %s
                """
                rows = db.execute_query(query, (trainer_id, training_date, start_time, exclude_id))
            else:
                query = """
                SELECT COUNT(*) FROM group_trainings
                WHERE trainer_id=%s AND training_date=%s AND start_time=%s
                """
                rows = db.execute_query(query, (trainer_id, training_date, start_time))
            return (rows and rows[0][0] == 0) or (not rows)
        except Exception as e:
            print("Ошибка check_trainer_availability:", e)
            return True

    @staticmethod
    def check_hall_availability(hall_id, training_date, start_time, exclude_id=None):
        """Возвращает True если зал свободен (hall_id — id из таблицы halls)"""
        try:
            if exclude_id:
                query = """
                SELECT COUNT(*) FROM group_trainings gt
                JOIN services s ON gt.service_id = s.service_id
                WHERE s.hall_id=%s AND gt.training_date=%s AND gt.start_time=%s AND gt.group_training_id != %s
                """
                rows = db.execute_query(query, (hall_id, training_date, start_time, exclude_id))
            else:
                query = """
                SELECT COUNT(*) FROM group_trainings gt
                JOIN services s ON gt.service_id = s.service_id
                WHERE s.hall_id=%s AND gt.training_date=%s AND gt.start_time=%s
                """
                rows = db.execute_query(query, (hall_id, training_date, start_time))
            return (rows and rows[0][0] == 0) or (not rows)
        except Exception as e:
            print("Ошибка check_hall_availability:", e)
            return True

    def to_dict(self):
        return {
            'group_training_id': self.group_training_id,
            'training_date': self.training_date,
            'start_time': self.start_time,
            'trainer_id': self.trainer_id,
            'service_id': self.service_id,
            'trainer_name': self.trainer_name,
            'service_name': self.service_name,
            'hall_id': self.hall_id,
            'hall_name': self.hall_name,
            'capacity': self.capacity
        }

    @classmethod
    def from_dict(cls, data):
        gt = cls(
            group_training_id=data.get('group_training_id'),
            training_date=data.get('training_date'),
            start_time=data.get('start_time'),
            trainer_id=data.get('trainer_id'),
            service_id=data.get('service_id'),
        )
        gt.trainer_name = data.get('trainer_name')
        gt.service_name = data.get('service_name')
        gt.hall_id = data.get('hall_id')
        gt.hall_name = data.get('hall_name')
        gt.capacity = data.get('capacity')
        return gt
