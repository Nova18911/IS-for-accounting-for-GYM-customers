class PersonalTraining:

    def __init__(self, personal_training_id=None, training_date=None, start_time=None,
                 price=0, trainer_id=None, client_id=None):
        self.personal_training_id = personal_training_id  # personal_training_id (№_Тренировки)
        self.training_date = training_date  # training_date (Дата)
        self.start_time = start_time  # start_time (Время)
        self.price = price  # price (Стоимость)
        self.trainer_id = trainer_id  # trainer_id (тренер)
        self.client_id = client_id  # client_id (клиент)

    def __str__(self):
        return f"Персональная тренировка {self.training_date} - {self.price} руб."