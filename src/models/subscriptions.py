class Subscription:

    def __init__(self, subscription_id=None, start_date=None, subscription_price_id=None):
        self.subscription_id = subscription_id  # subscription_id (Код_абонемента)
        self.start_date = start_date  # start_date (Дата_начала_действия)
        self.subscription_price_id = subscription_price_id  # subscription_price_id (idстоимость_абонемента)

    def __str__(self):
        return f"Абонемент №{self.subscription_id} от {self.start_date}"