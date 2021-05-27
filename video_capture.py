import sys
from time import sleep

import numpy as np
import cv2

from PyQt5 import QtGui

from PyQt5.QtGui import QPixmap

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QDesktopWidget

class VideoCaptureThread(QObject):
    finished             = pyqtSignal()
    change_pixmap_signal = pyqtSignal(np.ndarray)
    running              = False

    def __init__(self, capture_delay=0.03, capture_device_id=0):
        """
        capture_delay <float> Ammount of time in seconds, to delay before grabbing next frame from capture device. Default is 0.03.  Note: This value directly impacts CPU usage
        capture_device_id <integer> Id of the VideoCapture device.  Default is 0.
        """
        super().__init__()
        self.capture_delay     = capture_delay
        self.capture_device_id = capture_device_id
        print("Capture device: %s" % self.capture_device_id)

    def run(self):
        self.running = True
        cap = cv2.VideoCapture()
        cap.open(self.capture_device_id, cv2.CAP_DSHOW)
        while self.running is True:
            rect, cv_img = cap.read()
            if rect:
                self.change_pixmap_signal.emit(cv_img)
            sleep(self.capture_delay)
        cap.release()
        self.finished.emit()

    def stop(self):
        self.running = False

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.capture_device_id = 0
        self.aspect = Qt.KeepAspectRatio
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle('VideoCaptureStream')
        self.setGeometry(0,0,self.getScreenSize()['width'],self.getScreenSize()['height'])
        self.centralWidget = QLabel()

        # layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.centralWidget, 1)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.startThread()

    def getScreenSize(self):
        screen_size = QDesktopWidget().screenGeometry(-1)
        return({'width': screen_size.width(), 'height': screen_size.height()})

    def previousCaptureDevice(self):
        if self.capture_device_id > 0:
            self.capture_device_id -= 1
        else:
            self.capture_device_id = 9

    def nextCaptureDevice(self):
        if self.capture_device_id < 9:
            self.capture_device_id += 1
        else:
            self.capture_device_id = 0

    def stopThread(self):
        self.video_capture_thread.running = False
        self.thread.quit()

    def startThread(self, capture_device_id=None):
        if capture_device_id is not None:
            self.capture_device_id = capture_device_id
        print("Starting VideoCaptureThread using device: %s" % self.capture_device_id)
        self.thread = QThread()
        self.video_capture_thread = VideoCaptureThread(capture_device_id=self.capture_device_id)
        self.video_capture_thread.change_pixmap_signal.connect(self.updateCentralWidget)
        self.video_capture_thread.moveToThread(self.thread)
        self.thread.started.connect(self.video_capture_thread.run)
        self.video_capture_thread.finished.connect(self.thread.quit)
        self.video_capture_thread.finished.connect(self.video_capture_thread.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.thread.finished.connect(
            lambda: print("VideoCapture thread finished")
        )
        self.update()

    @pyqtSlot(np.ndarray)
    def updateCentralWidget(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.centralWidget.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h,w,ch = rgb_image.shape
        bytes_per_line = ch *w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.getScreenSize()['width'], self.getScreenSize()['height'], self.aspect)
        return QPixmap.fromImage(p)
        return QPixmap.fromImage(convert_to_Qt_format)

    def keyPressEvent(self, event):
        print("Key: ", event.key())
        if event.key() == Qt.Key_F1:
            print("HELP")
        if event.key() == 43: # + (plus)
            self.aspect = Qt.IgnoreAspectRatio
        if event.key() == 95: # - (minus)
            self.aspect = Qt.KeepAspectRatio
        if event.key() == Qt.Key_Up:
            print("KeyUp")
            self.showFullScreen()
            self.update()
        if event.key() == Qt.Key_Down:
            print("KeyDown")
            self.showNormal()
            self.update()
        if event.key() == Qt.Key_Left:
            self.stopThread()
            self.previousCaptureDevice()
            print("Capture device changed to: %s" % self.capture_device_id)
            while self.thread.isRunning():
                sleep(.1)
                self.update()
            self.startThread(capture_device_id=self.capture_device_id)
        if event.key() == Qt.Key_Right:
            self.stopThread()
            self.nextCaptureDevice()
            print("Capture device changed to: %s" % self.capture_device_id)
            while self.thread.isRunning():
                sleep(.1)
                self.update()
            self.startThread(capture_device_id=self.capture_device_id)
        self.update()

app = QApplication(sys.argv)
win = MainWindow()
win.show()
app.exec()