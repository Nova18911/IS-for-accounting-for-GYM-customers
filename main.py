from PyQt6.QtWidgets import QApplication
from src.login.login_window import LoginWindow
from src.main_window import MainWindow
# main.py — добавь в самый верх
import faulthandler, sys, traceback, os, signal, logging

# лог в файл
LOGFILE = os.path.join(os.path.dirname(__file__), "crash.log")
logging.basicConfig(filename=LOGFILE, level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")

# включаем faulthandler — он поможет в нативных падениях
faulthandler.enable(file=open(LOGFILE, "a"))
try:
    # регистрируем сигналы (SIGSEGV/SIGFPE) чтобы faulthandler печатал стек
    faulthandler.register(signal.SIGSEGV, file=open(LOGFILE, "a"), all_threads=True)
    faulthandler.register(signal.SIGFPE, file=open(LOGFILE, "a"), all_threads=True)
except Exception:
    # на Windows могут быть ограничения, но faulthandler.enable() обычно достаточно
    pass

# перехват необработанных исключений в Python
def excepthook(exc_type, exc_value, exc_tb):
    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
    # вывод в консоль и в файл
    traceback.print_exception(exc_type, exc_value, exc_tb)
    # падаем как обычно
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = excepthook


class FitnessApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginWindow()
        self.main_window = None

        # Подключаем сигнал успешной авторизации
        self.login_window.login_successful.connect(self.on_login_success)

    def on_login_success(self, user_id, user_email, user_role):
        # Создаем и показываем main_window (он будет мгновенно открыт и закрыт)
        self.main_window = MainWindow(user_id, user_email, user_role)
        self.main_window.show()  # Показываем на мгновение (прозрачное окно)

    def run(self):
        self.login_window.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    fitness_app = FitnessApp()
    fitness_app.run()