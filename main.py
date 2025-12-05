import sys
from PyQt6.QtWidgets import QApplication
from src.ui.login_window import Ui_LoginWindow

def main():
    app = QApplication(sys.argv)
    window = Ui_LoginWindow()

    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()