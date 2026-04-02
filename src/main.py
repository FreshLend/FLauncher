import sys
from PyQt6.QtWidgets import QApplication
from ui_mainwindow import FLauncher

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FLauncher()
    window.show()
    sys.exit(app.exec())