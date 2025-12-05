class TrainerType:

    def __init__(self, trainer_type_id=None, trainer_type_name=""):
        self.trainer_type_id = trainer_type_id  # trainer_type_id (Idтипы_тренеров)
        self.trainer_type_name = trainer_type_name  # trainer_type_name (тип_тренера)

    def __str__(self):
        return self.trainer_type_name