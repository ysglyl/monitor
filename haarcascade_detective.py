import os
import cv2
import numpy as np


class HaarcascadeDetective(object):

    cascade_classifier = cv2.CascadeClassifier()
    cascade_classifier.load('haarcascades' + os.path.sep + 'haarcascade_frontalface_default.xml')

    @staticmethod
    def get_faces(image):
        gray = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
        faces = HaarcascadeDetective.cascade_classifier.detectMultiScale(gray, 1.2, 10)
        for (x, y, w, h) in faces:
            yield image[y:y + h, x:x + w]

    @staticmethod
    def get_faces_position(image):
        gray = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
        faces = HaarcascadeDetective.cascade_classifier.detectMultiScale(gray, 1.3, 10)
        return faces
