class Client:

    def __init__(self, client_id=None, last_name="", first_name="", middle_name="",
                 phone="", email="", photo=None, subscription_id=None):
        self.client_id = client_id  # client_id (код_клиента)
        self.last_name = last_name  # last_name (Фамилия)
        self.first_name = first_name  # first_name (Имя)
        self.middle_name = middle_name  # middle_name (Отчество)
        self.phone = phone  # phone (телефон)
        self.email = email  # email (Email)
        self.photo = photo  # photo (Фото) - бинарные данные
        self.subscription_id = subscription_id  # subscription_id (Код_абонемента)

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.phone}"

    def has_photo(self):
        #Проверяет, есть ли фото у клиента
        return self.photo is not None and len(self.photo) > 0