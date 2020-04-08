import collections
import os
import shutil
from threading import Thread
import time

import cv2
import numpy as np
from PySide2.QtCore import QRect, Qt, QSize
from PySide2.QtGui import QIcon, QFont, QImage, QPixmap
from PySide2.QtWidgets import QMainWindow, QDesktopWidget, QLabel, QPushButton, QCheckBox, QFrame, QSpinBox, QFileDialog

from config.config import Config
from haarcascade_detective import HaarcascadeDetective
from db.db_helper import DbHelper
from user import AddUserFace


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.users = {}
        self.fps = 30

        self.playing = False

        self.capturing = False
        self.capture_frame = None

        self.flag_recognize = False
        self.recognizing_frame = None
        self.recognized_faces = []

        self.model = None

        self.setFixedSize(Config.width, Config.height)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setWindowIcon(QIcon('icons/icon.png'))
        self.setWindowTitle('人工智障人脸识别客户端')

        self.lbl_viewer = QLabel(self)
        self.lbl_viewer.setGeometry(QRect(10, 26, Config.width - 130, Config.height - 60))
        self.lbl_viewer.setText('没有图像')
        font = QFont()
        font.setPointSize(20)
        self.lbl_viewer.setFont(font)
        self.lbl_viewer.setAlignment(Qt.AlignCenter)
        self.lbl_viewer.setFrameShape(QFrame.StyledPanel)

        self.btn_open_camera = QPushButton(self)
        self.btn_open_camera.setGeometry(QRect(Config.width - 110, 10, 100, 26))
        self.btn_open_camera.setText('打开摄像头')
        self.btn_open_camera.clicked.connect(self.btn_click)

        self.btn_close_camera = QPushButton(self)
        self.btn_close_camera.setGeometry(QRect(Config.width - 110, 46, 100, 26))
        self.btn_close_camera.setText('关闭摄像头')
        self.btn_close_camera.setDisabled(True)
        self.btn_close_camera.clicked.connect(self.btn_click)

        self.btn_open_video = QPushButton(self)
        self.btn_open_video.setGeometry(QRect(Config.width - 110, 82, 100, 26))
        self.btn_open_video.setText('播放视频')
        self.btn_open_video.clicked.connect(self.btn_click)

        self.btn_close_video = QPushButton(self)
        self.btn_close_video.setGeometry(QRect(Config.width - 110, 118, 100, 26))
        self.btn_close_video.setText('停止播放')
        self.btn_close_video.setDisabled(True)
        self.btn_close_video.clicked.connect(self.btn_click)

        self.cb_recognize = QCheckBox(self)
        self.cb_recognize.setText('启动识别')
        self.cb_recognize.setDisabled(True)
        self.cb_recognize.setGeometry(QRect(Config.width - 108, 154, 100, 26))
        self.cb_recognize.clicked.connect(self.change_recognize)

        self.cb_show_match_result = QCheckBox(self)
        self.cb_show_match_result.setText('显示匹配度')
        self.cb_show_match_result.setDisabled(True)
        self.cb_show_match_result.setGeometry(QRect(Config.width - 108, 192, 100, 26))
        if Config.show_match_result:
            self.cb_show_match_result.setChecked(True)
        self.cb_show_match_result.clicked.connect(self.change_show_match_result)

        lbl_threshold = QLabel(self)
        lbl_threshold.setText("识别精度")
        lbl_threshold.setGeometry(QRect(Config.width - 108, 228, 60, 26))

        self.sb_threshold = QSpinBox(self)
        self.sb_threshold.setValue(Config.threshold)
        self.sb_threshold.setMinimum(30)
        self.sb_threshold.setMaximum(100)
        self.sb_threshold.valueChanged.connect(self.change_threshold)
        self.sb_threshold.setGeometry(QRect(Config.width - 45, 228, 40, 26))

        self.btn_capture = QPushButton(self)
        self.btn_capture.setGeometry(QRect(Config.width - 110, Config.height - 200, 100, 26))
        self.btn_capture.setText('截屏')
        self.btn_capture.setDisabled(True)
        self.btn_capture.clicked.connect(self.btn_click)

        self.lbl_capture_pic = QLabel(self)
        self.lbl_capture_pic.setGeometry(QRect(Config.width - 110, Config.height - 160, 100, 100))
        self.lbl_capture_pic.setAlignment(Qt.AlignCenter)
        self.lbl_capture_pic.setFrameShape(QFrame.StyledPanel)

        self.btn_capture_save = QPushButton(self)
        self.btn_capture_save.setGeometry(QRect(Config.width - 110, Config.height - 60, 100, 26))
        self.btn_capture_save.setText('保存截图')
        self.btn_capture_save.setDisabled(True)
        self.btn_capture_save.clicked.connect(self.btn_click)

        self.train_model()

    def btn_click(self):
        btn = self.sender()
        if btn == self.btn_open_camera:
            self.btn_open_camera.setDisabled(True)
            self.btn_close_camera.setDisabled(False)
            self.btn_capture.setDisabled(False)
            self.cb_recognize.setDisabled(False)

            self.start_play(0)
        elif btn == self.btn_close_camera:
            self.stop_play()
            self.lbl_viewer.clear()
            self.btn_open_camera.setDisabled(False)
            self.btn_close_camera.setDisabled(True)
            self.btn_capture.setDisabled(True)
            self.cb_recognize.setDisabled(True)
        elif btn == self.btn_open_video:
            file_name = QFileDialog.getOpenFileName(self, "Open Video", "/", "Video Files (*.avi *.mp4 *.mpeg *.mov)")
            if file_name[0] != '':
                self.start_play(file_name[0])
                self.btn_close_video.setDisabled(False)
        elif btn == self.btn_close_video:
            self.stop_play()
            self.lbl_viewer.clear()
            self.btn_open_camera.setDisabled(False)
            self.btn_close_camera.setDisabled(True)
            self.btn_capture.setDisabled(True)
            self.cb_recognize.setDisabled(True)
        elif btn == self.btn_capture:
            self.capturing = True
            self.btn_capture_save.setDisabled(False)
        elif btn == self.btn_capture_save:
            AddUserFace(self.capture_frame).exec_()
            self.train_model()

    def change_recognize(self):
        if self.sender().isChecked():
            self.flag_recognize = True
            Thread(target=self.recognize).start()
            self.cb_show_match_result.setDisabled(False)
        else:
            self.flag_recognize = False
            self.cb_show_match_result.setDisabled(True)

    def change_show_match_result(self):
        Config.config_parser.set("recognition", 'show_match_result', str(True if self.sender().isChecked() else False))
        Config.show_match_result = True if self.sender().isChecked() else False
        Config.save()

    @staticmethod
    def change_threshold(value):
        Config.config_parser.set("recognition", 'threshold', str(value))
        Config.threshold = value
        Config.save()

    def start_play(self, path):
        self.playing = True
        Thread(target=self.play, args=(path,)).start()

    def stop_play(self):
        self.lbl_viewer.clear()
        self.playing = False

    def play(self, path):
        video_capture = cv2.VideoCapture(path)
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        while self.playing:
            start_time = time.time()
            ret, frame = video_capture.read()
            if ret:
                if self.flag_recognize:
                    # 存放当前帧给识别线程
                    if self.recognizing_frame is None:
                        self.recognizing_frame = frame.copy()
                    # 显示已识别的人脸
                    faces = self.recognized_faces.copy()
                    for face in faces:
                        x, y, w, h = face['position']
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1, cv2.LINE_AA)
                        cv2.putText(frame, face['name'] + ('(' + str(face['degree']) + ')' if Config.show_match_result else ''), (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)

                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = QImage(img, img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
                pix_map = QPixmap.fromImage(image)
                pix_map = pix_map.scaled(Config.width - 130, Config.height - 60, Qt.KeepAspectRatio)
                self.lbl_viewer.setPixmap(pix_map)

                # 保存截图
                if self.capturing:
                    self.capture_frame = frame.copy()
                    pix_map = pix_map.scaled(100, 100, Qt.KeepAspectRatio)
                    self.lbl_capture_pic.setPixmap(pix_map)
                    self.capturing = False

                # 根据FPS控制休眠
                end_time = time.time()
                diff_time = end_time - start_time
                if diff_time < 1 / fps:
                    time.sleep(1 / fps - diff_time)

    def recognize(self):
        while self.flag_recognize:
            try:
                if self.recognizing_frame is None:
                    time.sleep(0.05)
                    continue
                self.recognized_faces.clear()
                faces = HaarcascadeDetective.get_faces_position(self.recognizing_frame)
                for (x, y, w, h) in faces:
                    recognized_face = {'position': (x, y, w, h)}
                    face = self.recognizing_frame[y:y + h, x:x + w]
                    if self.model is not None:
                        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                        params = self.model.predict(gray)
                        if params[1] <= Config.threshold:
                            recognized_face['name'] = self.users[params[0]]
                            recognized_face['degree'] = int(params[1])
                    self.recognized_faces.append(recognized_face)
                self.recognizing_frame = None
            except Exception as e:
                print(e)

    def train_model(self):
        users = DbHelper.query_users()
        for user in users:
            self.users[user[0]] = user[1]

        y, x = [], []
        if not os.path.exists("faces"):
            return
        faces_dir = os.listdir('faces')
        for user_dir in faces_dir:
            faces = os.listdir('faces{}{}'.format(os.sep, user_dir))
            for face in faces:
                y.append(int(user_dir))
                im = cv2.imread('faces{}{}{}{}'.format(os.sep, user_dir, os.sep, face), 0)
                x.append(np.asarray(im, dtype=np.uint8))
        if len(x) != 0 and len(y) != 0:
            self.model = cv2.face.LBPHFaceRecognizer_create()
            self.model.train(np.asarray(x), np.asarray(y, dtype=np.int64))

    def closeEvent(self, *args, **kwargs):
        self.playing = False
