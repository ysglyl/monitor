from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QIcon, QImage, QPixmap
from PySide2.QtWidgets import QDialog, QLabel, QLineEdit, QRadioButton, QPushButton, QComboBox
import os
import time

from db.db_helper import DbHelper
from tool import Tool
from haarcascade_detective import HaarcascadeDetective

import cv2


class AddUserFace(QDialog):
    def __init__(self, image):
        super(AddUserFace, self).__init__()
        self.setFixedSize(300, 275)
        self.setWindowIcon(QIcon('icons/add.png'))
        self.setWindowTitle('添加')

        self.rb_select = QRadioButton("选择", self)
        self.rb_select.setGeometry(70, 20, 50, 26)
        self.rb_select.toggled.connect(self.toggle)

        self.rb_new = QRadioButton('新建', self)
        self.rb_new.setGeometry(120, 20, 50, 26)
        self.rb_new.toggled.connect(self.toggle)

        lbl_name = QLabel('名称', self)
        lbl_name.setGeometry(10, 70, 50, 26)
        lbl_name.setAlignment(Qt.AlignCenter)

        users = DbHelper.query_users()

        self.cb_user = QComboBox(self)
        self.cb_user.setGeometry(70, 70, 200, 26)
        self.le_user = QLineEdit(self)
        self.le_user.setGeometry(70, 70, 200, 26)

        if users is not None and len(users) > 0:
            self.rb_select.setChecked(True)
            for user in users:
                self.cb_user.addItem(user[1], userData=user)
        else:
            self.rb_select.setDisabled(True)
            self.rb_new.setChecked(True)

        lbl_face = QLabel('人脸', self)
        lbl_face.setGeometry(10, 140, 50, 26)
        lbl_face.setAlignment(Qt.AlignCenter)

        self.btn_save = QPushButton(self)
        self.btn_save.setText('保存')
        self.btn_save.setGeometry(10, 234, 280, 30)
        self.btn_save.clicked.connect(self.save)

        self.cache_faces = {}
        self.face = None

        faces = HaarcascadeDetective.get_faces(image)
        index = 0
        for face in faces:
            viewer_face = QPushButton(self)
            viewer_face.setGeometry(70 * (index + 1), 120, 60, 60)
            viewer_face.setIconSize(QSize(56, 56))
            img = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            image = QImage(img, img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
            pix_map = QPixmap.fromImage(image)
            viewer_face.setIcon(QIcon(pix_map))
            viewer_face.clicked.connect(self.select_face)
            self.cache_faces[viewer_face] = face
            if index == 0:
                self.face = face
                viewer_face.setStyleSheet('border-color: rgb(255, 0, 0);border-style: outset;border-width: 2px;')
            index += 1
            if index > 3:
                break

        if index == 0:
            Tool.show_msg_box("未检测到人脸信息")

    def select_face(self):
        sender = self.sender()
        for btn in self.cache_faces:
            btn.setStyleSheet('border-style: none')
        sender.setStyleSheet("border-color: rgb(255, 0, 0);border-style: outset;border-width: 2px;")
        self.face = self.cache_faces[btn]

    def toggle(self):
        if self.rb_new.isChecked():
            self.cb_user.hide()
            self.le_user.show()
        elif self.rb_select.isChecked():
            self.le_user.hide()
            self.cb_user.show()

    def save(self):
        if self.face is None:
            return
        self.btn_save.setDisabled(True)
        if self.rb_new.isChecked():
            user_name = self.le_user.text().strip(' ')
            if not user_name.replace(' ', '').encode("utf-8").isalpha():
                Tool.show_msg_box('只支持英文字母和空格～')
                self.le_name.setFocus()
                return
            user_id = DbHelper.insert_user(user_name)
        else:
            user_id = self.cb_user.currentData()[0]
        if not os.path.exists("faces"):
            os.mkdir("faces")
        if not os.path.exists('faces/{}'.format(user_id)):
            os.mkdir('faces/{}'.format(user_id))
        face = 'faces/{}/{}.png'.format(user_id, time.time())
        cv2.imwrite(face, self.face)
        self.close()
