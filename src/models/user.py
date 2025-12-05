class User:

    def __init__(self, user_id=None, email="", role="", is_active=True):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.is_active = is_active

    def __str__(self):
        return f"{self.email} ({self.role})"