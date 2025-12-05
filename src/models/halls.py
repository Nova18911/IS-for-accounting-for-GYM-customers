class Hall:
    def __init__(self, hall_id=None, hall_name="", capacity=0):
        self.hall_id = hall_id
        self.hall_name = hall_name
        self.capacity = capacity

    def __str__(self):
        return f"{self.hall_name} ({self.capacity} чел.)"