class TrainerType:

    def __init__(self, trainer_type_id=None, trainer_type_name="", rate=0):
        self.trainer_type_id = trainer_type_id  # trainer_type_id (Idтипы_тренеров)
        self.trainer_type_name = trainer_type_name  # trainer_type_name (тип_тренера)
        self.rate = rate  # Одна ставка

    def __str__(self):
        return self.trainer_type_name