import sys
from PyQt6.QtWidgets import QApplication
from ui_main import OneNoteUI


def main():
    app = QApplication(sys.argv)
    win = OneNoteUI()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()