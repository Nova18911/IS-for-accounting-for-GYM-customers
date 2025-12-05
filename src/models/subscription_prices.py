class SubscriptionPrice:

    def __init__(self, subscription_price_id=None, duration="", price=""):
        self.subscription_price_id = subscription_price_id  # subscription_price_id (idстоимость_абонемента)
        self.duration = duration  # duration (срок_действия_абонемента)
        self.price = price  # price (стоимость)

    def __str__(self):
        return f"{self.duration} - {self.price} руб."