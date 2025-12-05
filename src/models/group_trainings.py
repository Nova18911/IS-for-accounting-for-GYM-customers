class GroupTraining:

    def __init__(self, group_training_id=None, training_date=None, start_time=None,
                 trainer_id=None, service_id=None):
        self.group_training_id = group_training_id  # group_training_id (№_тренировки)
        self.training_date = training_date  # training_date (Дата_тренировки)
        self.start_time = start_time  # start_time (время_начала)
        self.trainer_id = trainer_id  # trainer_id (тренер)
        self.service_id = service_id  # service_id (тренировка)

    def __str__(self):
        return f"Групповая тренировка {self.training_date} {self.start_time}"