import os
import time
import hashlib
import json
from config.config import Config
from PySide2.QtWidgets import QMessageBox


class Tool(object):

    @staticmethod
    def show_msg_box(msg):
        box = QMessageBox()
        box.setText(msg)
        box.exec_()
