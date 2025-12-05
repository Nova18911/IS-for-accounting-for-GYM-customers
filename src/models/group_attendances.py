class GroupAttendance:

    def __init__(self, attendance_id=None, group_training_id=None, client_id=None,
                 attendance_date=None):
        self.attendance_id = attendance_id  # attendance_id (№_посещения)
        self.group_training_id = group_training_id  # group_training_id (Групповая_тренировка)
        self.client_id = client_id  # client_id (клиент)
        self.attendance_date = attendance_date  # attendance_date

    def __str__(self):
        return f"Посещение {self.attendance_date}"