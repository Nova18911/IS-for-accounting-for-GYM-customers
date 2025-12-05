class Service:

    def __init__(self, service_id=None, service_name="", price=0, hall_id=None):
        self.service_id = service_id  # service_id
        self.service_name = service_name  # service_name (Вид_услуги)
        self.price = price  # price (Стоимость)
        self.hall_id = hall_id  # hall_id (Залы_№_зала)

    def __str__(self):
        return f"{self.service_name} - {self.price} руб."