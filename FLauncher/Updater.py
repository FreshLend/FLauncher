import sys
import os
import subprocess
import requests
import webbrowser
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QProgressBar, QHBoxLayout, QPushButton, QFrame
)
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QFont, QPalette
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect

VERSION = "0.4.0"
LAUNCHER_REPO = "FreshLend/FLauncher"

class GradientWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(0, 150, 255))
        gradient.setColorAt(0.5, QColor(0, 100, 200))
        gradient.setColorAt(1, QColor(0, 70, 150))
        painter.fillRect(self.rect(), gradient)
        painter.end()

class BottomProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self.setTextVisible(False)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_rect = QRect(0, 0, self.width(), self.height())
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 30))
        painter.drawRect(bg_rect)
        
        if self.maximum() > 0 and self.value() > 0:
            progress = self.value() / self.maximum()
            fill_width = int(self.width() * progress)
            
            fill_rect = QRect(0, 0, fill_width, self.height())
            
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, QColor(0, 200, 255))
            gradient.setColorAt(1, QColor(0, 100, 200))
            
            painter.setBrush(gradient)
            painter.drawRect(fill_rect)
        
        painter.end()

class Updater(QMainWindow):
    def __init__(self):
        super().__init__()
        self.center_window()
        self.setup_ui()
        self.check_updates()

    def center_window(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - 300) // 2
        y = (screen_geometry.height() - 150) // 2
        self.setGeometry(x, y, 300, 150)

    def setup_ui(self):
        self.setFixedSize(300, 150)
        self.setWindowTitle('FLauncher Updater')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Главный контейнер
        main_widget = QWidget()
        main_widget.setObjectName("mainWidget")
        main_widget.setStyleSheet("""
            #mainWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #0096FF, stop: 0.5 #0077CC, stop: 1 #0055AA);
                border-radius: 8px;
            }
        """)
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("""
            #contentWidget {
                background: transparent;
                border: none;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 10)
        content_layout.setSpacing(8)
        
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        
        self.version_label = QLabel(f'v{VERSION}')
        self.version_label.setStyleSheet("""
            font-size: 10px;
            font-weight: bold;
            color: rgba(255, 255, 255, 150);
            background: transparent;
            margin: 0;
            padding: 0;
        """)
        top_layout.addWidget(self.version_label)
        
        content_layout.addLayout(top_layout)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 5, 0, 10)
        
        self.title_label = QLabel('FLAUNCHER')
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
            background: transparent;
            margin: 0;
            padding: 0;
            letter-spacing: 1px;
        """)
        title_layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel('THE LAUNCHER FOR VOXELCORE')
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            font-size: 10px;
            font-weight: bold;
            color: rgba(255, 255, 255, 200);
            background: transparent;
            margin: 0;
            padding: 0;
            letter-spacing: 0.5px;
        """)
        title_layout.addWidget(self.subtitle_label)
        
        content_layout.addLayout(title_layout)

        self.status_label = QLabel('Проверяем обновления...')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: white;
            background: transparent;
            margin: 0;
            padding: 2px;
        """)
        self.status_label.setWordWrap(True)
        content_layout.addWidget(self.status_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(8)
        self.button_layout.setContentsMargins(20, 5, 20, 0)
        
        self.yes_button = QPushButton('ОБНОВИТЬ')
        self.yes_button.setFixedHeight(25)
        self.yes_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
        """)
        self.yes_button.hide()
        
        self.no_button = QPushButton('ПРОПУСТИТЬ')
        self.no_button.setFixedHeight(25)
        self.no_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f44336, stop: 1 #da190b);
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #da190b, stop: 1 #ba000d);
            }
            QPushButton:pressed {
                background: #ba000d;
            }
        """)
        self.no_button.hide()
        
        self.button_layout.addWidget(self.yes_button)
        self.button_layout.addWidget(self.no_button)
        content_layout.addLayout(self.button_layout)

        main_layout.addWidget(content_widget)

        self.progress_bar = BottomProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.yes_button.clicked.connect(self.download_update)
        self.no_button.clicked.connect(self.skip_update)

        self.latest_version = None
        self.download_url = None

    def animate_progress(self):
        self.animation = QPropertyAnimation(self.progress_bar, b"value")
        self.animation.setDuration(1500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()

    def check_updates(self):
        self.animate_progress()
        QTimer.singleShot(300, self._check_updates_thread)

    def _check_updates_thread(self):
        try:
            self.status_label.setText('Подключение к серверу...')
            
            response = requests.get(
                f"https://api.github.com/repos/{LAUNCHER_REPO}/releases/latest",
                timeout=8,
                headers={'User-Agent': 'FLauncher-Updater'}
            )
            
            if response.status_code == 200:
                latest_release = response.json()
                self.latest_version = latest_release['tag_name'].lstrip('v')
                release_url = latest_release['html_url']

                for asset in latest_release.get('assets', []):
                    if any(ext in asset['name'].lower() for ext in ['.exe', '.zip', '.msi']):
                        self.download_url = asset['browser_download_url']
                        break
                
                if not self.download_url:
                    self.download_url = release_url
                
                if self.latest_version != VERSION:
                    self.show_update_found()
                else:
                    self.show_no_updates()
                    
            else:
                self.show_error("Ошибка сервера")
                
        except requests.ConnectionError:
            self.show_error("Нет подключения")
        except requests.Timeout:
            self.show_error("Таймаут соединения")
        except Exception as e:
            self.show_error("Ошибка проверки")

    def show_update_found(self):
        self.title_label.hide()
        self.subtitle_label.hide()
        
        self.status_label.setText(
            f'Доступно обновление!\nv{VERSION} → v{self.latest_version}'
        )
        self.progress_bar.setValue(100)

        self.yes_button.show()
        self.no_button.show()

    def show_no_updates(self):
        self.status_label.setText('Установлена актуальная версия')
        self.progress_bar.setValue(100)
        QTimer.singleShot(800, self.launch_launcher)

    def show_error(self, message):
        self.status_label.setText(message)
        self.progress_bar.setValue(100)
        QTimer.singleShot(1500, self.launch_launcher)

    def download_update(self):
        if self.download_url:
            webbrowser.open(self.download_url)
        self.close()

    def skip_update(self):
        self.title_label.show()
        self.subtitle_label.show()
        self.yes_button.hide()
        self.no_button.hide()
        
        self.status_label.setText('Обновление пропущено.')
        self.progress_bar.setValue(100)

        QTimer.singleShot(800, self.launch_launcher)

    def launch_launcher(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            paths_to_try = [
                os.path.join(script_dir, "FLauncher.exe"),
                os.path.join(script_dir, "FLauncher.py"),
                os.path.join(script_dir, "dist", "FLauncher.exe"),
            ]
            
            for path in paths_to_try:
                if os.path.exists(path):
                    if path.endswith('.py'):
                        subprocess.Popen([sys.executable, path])
                    else:
                        subprocess.Popen([path])
                    break
            
        except Exception:
            pass
        
        finally:
            self.status_label.setText('Запуск...')
            self.progress_bar.setValue(0)

            self.close_timer = QTimer()
            self.close_timer.timeout.connect(self._update_close_progress)
            self.close_timer.start(20)
            self.close_counter = 0
            self.close_max = 300

    def _update_close_progress(self):
        self.close_counter += 2
        if self.close_counter > self.close_max:
            self.close_counter = self.close_max
        
        self.progress_bar.setValue(self.close_counter)
        
        if self.close_counter >= self.close_max:
            self.close_timer.stop()
            QTimer.singleShot(100, self.close)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = Updater()
    window.show()
    
    sys.exit(app.exec_())
