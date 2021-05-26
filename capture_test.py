import sys
import numpy as np
import cv2
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QGridLayout, QDesktopWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from time import sleep

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, screen_update_delay=.03, capture_device_id=0):
        """
        screen_update_delay <float> Ammount of time in seconds, to delay before grabbing next frame from capture device. Default is .03
                                    Note: This value directly impacts CPU usage
        capture_device_id <integer> Id of the VideoCapture device.  Default is 0.
        """
        super().__init__()
        self._run_flag = True
        self.screen_update_delay = screen_update_delay
        self.capture_device_id   = capture_device_id

    def run(self):
        # capture video from usb capture device
        cap = cv2.VideoCapture()
        cap.open(self.capture_device_id, cv2.CAP_DSHOW)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)
            sleep(self.screen_update_delay)
        cap.release()
    
    def stop(self):
        self._run_flag = False
        self.wait()

class CaptureWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('HDMI IN')
        screen_size = QDesktopWidget().screenGeometry(-1)
        self.display_width = screen_size.width()
        self.display_height = screen_size.height()
        #self.display_width = 1280
        #self.display_height = 900
        self.hdmi_display = QLabel(self)
        self.hdmi_display.resize(self.display_width, self.display_height)

        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.hdmi_display,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_hdmi_display)
        self.thread.start()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            print("KeyUp")
        if event.key() == Qt.Key_Down:
            print("KeyDown")
        if event.key() == Qt.Key_Left:
            if self.thread.capture_device_id > 0:
                self.thread.stop()
                self.thread = VideoThread(self.thread.capture_device_id-1)
                self.thread.start()
            print("KeyLeft")
        if event.key() == Qt.Key_Right:
            if self.thread.capture_device_id < 5:
                self.thread.stop()
                self.thread = VideoThread(self.thread.capture_device_id+1)
                self.thread.start()
            print("KeyRight")

        self.update()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_hdmi_display(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.hdmi_display.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h,w,ch = rgb_image.shape
        bytes_per_line = ch *w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        #p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        #p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        #return QPixmap.fromImage(p)
        return QPixmap.fromImage(convert_to_Qt_format)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    g = CaptureWindow()
    g.show()
    #g.showMaximized()
    #g.showFullScreen()
    sys.exit(app.exec_())
