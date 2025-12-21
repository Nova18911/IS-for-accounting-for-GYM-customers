import sys
from PyQt6.QtWidgets import QApplication
from src.login.login_window import LoginWindow
from src.main_window import MainWindow


class FitnessApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginWindow()
        self.main_window = None
        self.login_window.login_successful.connect(self.show_main_window)

    def show_main_window(self, user_id, user_email, user_role):
        self.main_window = MainWindow(user_id, user_email, user_role)
        self.main_window.show()
        self.login_window.close()
    def run(self):
        self.login_window.show()
        return self.app.exec()

if __name__ == "__main__":
    app_instance = FitnessApp()
    sys.exit(app_instance.run())