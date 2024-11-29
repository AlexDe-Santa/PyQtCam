from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QToolBar, QFileDialog, QComboBox, QStatusBar, \
    QErrorMessage
from PyQt5.QtMultimedia import QCamera, QCameraImageCapture, QCameraInfo
from PyQt5.QtMultimediaWidgets import QCameraViewfinder
import os
import sys
import time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background: lightgrey;")

        self.available_cameras = QCameraInfo.availableCameras()
        if not self.available_cameras:
            sys.exit("Камеры не найдены!")

        self.status = QStatusBar()
        self.status.setStyleSheet("background: white;")
        self.setStatusBar(self.status)

        self.save_path = ""

        self.viewfinder = QCameraViewfinder()
        self.viewfinder.show()
        self.setCentralWidget(self.viewfinder)

        self.select_camera(0)

        toolbar = QToolBar("Панель инструментов камеры")
        self.addToolBar(toolbar)

        click_action = QAction("Сделать фото", self)
        click_action.setStatusTip("Это действие сделает фото")
        click_action.setToolTip("Съемка фото")
        click_action.triggered.connect(self.click_photo)
        toolbar.addAction(click_action)

        change_folder_action = QAction("Изменить папку для сохранения", self)
        change_folder_action.setStatusTip("Изменение папки, где будут сохранены фотографии.")
        change_folder_action.setToolTip("Изменить папку сохранения")
        change_folder_action.triggered.connect(self.change_folder)
        toolbar.addAction(change_folder_action)

        camera_selector = QComboBox()
        camera_selector.setStatusTip("Выберите камеру для съемки")
        camera_selector.setToolTip("Выбор камеры")
        camera_selector.setToolTipDuration(2500)
        camera_selector.addItems([camera.description() for camera in self.available_cameras])
        camera_selector.currentIndexChanged.connect(self.select_camera)
        toolbar.addWidget(camera_selector)

        toolbar.setStyleSheet("background: white;")

        self.setWindowTitle("PyQt5 Камера")
        self.show()

    def select_camera(self, i):
        self.camera = QCamera(self.available_cameras[i])
        self.camera.setViewfinder(self.viewfinder)
        self.camera.setCaptureMode(QCamera.CaptureStillImage)
        self.camera.error.connect(lambda: self.alert(self.camera.errorString()))
        self.camera.start()

        self.capture = QCameraImageCapture(self.camera)
        self.capture.error.connect(lambda error_msg, error, msg: self.alert(msg))
        self.capture.imageCaptured.connect(
            lambda d, i: self.status.showMessage("Изображение снято: " + str(self.save_seq)))

        self.current_camera_name = self.available_cameras[i].description()
        self.save_seq = 0

    def click_photo(self):
        timestamp = time.strftime("%d-%b-%Y-%H_%M_%S")
        if not self.save_path:
            self.save_path = os.getcwd()  # текущая директория

        self.capture.capture(
            os.path.join(self.save_path, f"{self.current_camera_name}-{self.save_seq:04d}-{timestamp}.jpg"))

        self.save_seq += 1

    def change_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения", "")
        if path:
            self.save_path = path
            self.save_seq = 0

    def alert(self, msg):
        error = QErrorMessage(self)
        error.showMessage(msg)


if __name__ == "__main__":
    App = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(App.exec_())
