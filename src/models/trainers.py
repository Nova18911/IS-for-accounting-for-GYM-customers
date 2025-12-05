class Trainer:

    def __init__(self, trainer_id=None, last_name="", first_name="", middle_name="",
                 photo=None, phone="", trainer_type_id=None):
        self.trainer_id = trainer_id  # trainer_id (№_Карты)
        self.last_name = last_name  # last_name (Фамилия)
        self.first_name = first_name  # first_name (Имя)
        self.middle_name = middle_name  # middle_name (Отчество)
        self.photo = photo  # photo (Фото) - бинарные данные
        self.phone = phone  # phone (Телефон)
        self.trainer_type_id = trainer_type_id  # trainer_type_id (Idтипы_тренеров)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def has_photo(self):
        #Проверяет, есть ли фото у тренера
        return self.photo is not None and len(self.photo) > 0