import sys
from time import sleep

import numpy as np
import cv2

from PyQt5.QtGui import QPixmap

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

class VideoCaptureThread(QObject):
    finished             = pyqtSignal()
    change_pixmap_signal = pyqtSignal(np.ndarray)
    running              = False

    def __init__(self, capture_delay=0.01, capture_device_id=0):
        super().__init__()
        self.capture_delay     = capture_delay
        self.capture_device_id = capture_device_id

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

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.resize(800, 600)
        self.centralWidget = QLabel()
        self.setCentralWidget(self.centralWidget)
        ## Create and connect widgets
        #self.stepLabel = QLabel("Thread Step: 0")
        #self.stepLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        #self.countBtn = QPushButton("Stop Thread", self)
        #self.countBtn.clicked.connect(self.stopThread)
        #self.longRunningBtn = QPushButton("Start Thread", self)
        #self.longRunningBtn.clicked.connect(self.startThread)
        # Set the layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        #layout.addWidget(self.clicksLabel)
        #layout.addWidget(self.countBtn)
        #layout.addStretch()
        #layout.addWidget(self.stepLabel)
        #layout.addWidget(self.longRunningBtn)
        self.centralWidget.setLayout(layout)
        self.startThread()

    def previousCaptureDevice(self):
        cap_id = self.video_capture_thread.capture_device_id
        if cap_id > 0:
            cap_id -= 1
        else:
            cap_id = 10

    def nextCaptureDevice(self):
        cap_id = self.video_capture_thread.capture_device_id
        if cap_id < 10:
            cap_id += 1
        else:
            cap_id = 0

    def countClicks(self):
        self.clicksCount += 1
        self.clicksLabel.setText(f"{self.clicksCount} clicks")

    def reportProgress(self, n):
        self.stepLabel.setText(f"Thread Step: {n}")

    def stopThread(self):
        self.video_capture_thread.running = False

    def startThread(self):
        self.thread = QThread()
        self.video_capture_thread = VideoCaptureThread()
        self.video_capture_thread.moveToThread(self.thread)
        self.thread.started.connect(self.video_capture_thread.run)
        self.video_capture_thread.finished.connect(self.thread.quit)
        self.video_capture_thread.finished.connect(self.video_capture_thread.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.video_capture_thread.progress.connect(self.reportProgress)
        self.thread.start()

        self.longRunningBtn.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.longRunningBtn.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.stepLabel.setText("Long-Running Step: 0")
        )

app = QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec())