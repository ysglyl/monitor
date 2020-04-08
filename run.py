from PySide2.QtWidgets import QApplication
from main import MainWindow

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec_()
