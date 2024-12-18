import sys, os, subprocess, zipfile, shutil, requests, markdown
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel, QSpacerItem, QSizePolicy, QFrame, QPushButton, QComboBox, QMessageBox, QHBoxLayout
from PyQt5.QtGui import QPalette, QBrush, QImage, QDesktopServices, QIcon
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize
from pathlib import Path
from datetime import datetime

def resource_path(relative_path):
        """Получить абсолютный путь к ресурсу, независимо от того, запущена ли программа как .exe или нет."""
        try:
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)
        except Exception as e:
            return relative_path

class FLauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 1100, 650)
        self.setFixedSize(1100, 650)
        self.setWindowTitle('FLauncher')

        self.add_release_panel()
        self.add_info_panel()
        
        self.set_background()
        self.add_blue_bar()
        self.create_app_data_directory()
        self.load_versions()

    def set_background(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        image = QImage(resource_path('ui/background.png'))
        brush = QBrush(image)
        palette.setBrush(QPalette.Background, brush)
        self.setPalette(palette)

    def add_blue_bar(self):
        blue_bar = QWidget(self)
        blue_bar.setGeometry(0, self.height() - 80, self.width(), 80)
        blue_bar.setStyleSheet("background-color: rgba(114, 241, 89, 0.8);")

        self.version_combo = QComboBox(blue_bar)
        self.version_combo.setGeometry(10, 10, 200, 60)
        self.version_combo.setStyleSheet("background-color: white; color: black; font-size: 18px; font-weight: bold;")
        self.version_combo.addItem("Получение версий...")

        self.download_button = QPushButton("Скачать", blue_bar)
        self.download_button.setGeometry(220, 10, 150, 30)
        self.download_button.setStyleSheet("background-color: rgb(240, 207, 61); color: white; font-size: 18px; font-weight: bold;")
        self.download_button.clicked.connect(self.on_download_button_click)

        self.play_button = QPushButton("Играть", blue_bar)
        self.play_button.setGeometry(220, 40, 150, 30)
        self.play_button.setStyleSheet("background-color: rgb(240, 207, 61); color: white; font-size: 18px; font-weight: bold;")
        self.play_button.clicked.connect(self.on_play_button_click)

        icon_reload = QIcon(resource_path("ui/FLM.png"))
        self.reload_button = QPushButton(blue_bar)
        self.reload_button.setIcon(icon_reload)
        self.reload_button.setIconSize(QSize(60, 60))
        self.reload_button.setGeometry(835, 10, 60, 60)
        self.reload_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
        """)
        self.reload_button.clicked.connect(self.on_vwm_button_click)

        icon_vwm = QIcon(resource_path("ui/reload.png"))
        self.vwm_button = QPushButton(blue_bar)
        self.vwm_button.setIcon(icon_vwm)
        self.vwm_button.setIconSize(QSize(30, 30))
        self.vwm_button.setGeometry(895, 10, 60, 60)
        self.vwm_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
        """)
        self.vwm_button.clicked.connect(self.refresh_versions)

        icon_folder = QIcon(resource_path("ui/folder.png"))
        self.folder_button = QPushButton(blue_bar)
        self.folder_button.setIcon(icon_folder)
        self.folder_button.setIconSize(QSize(30, 30))
        self.folder_button.setGeometry(965, 10, 60, 60)
        self.folder_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
        """)
        self.folder_button.clicked.connect(self.open_versions_folder)

        icon_settings = QIcon(resource_path("ui/settings.png"))
        self.settings_button = QPushButton(blue_bar)
        self.settings_button.setIcon(icon_settings)
        self.settings_button.setIconSize(QSize(30, 30))
        self.settings_button.setGeometry(1035, 10, 60, 60)
        self.settings_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
        """)
        self.settings_button.clicked.connect(self.open_settings)

    def add_release_panel(self):
        release_panel = QWidget(self)
        release_panel.setGeometry(20, 40, 700, self.height() - 120)
        release_panel.setStyleSheet("background-color: rgba(255, 255, 255, 0.7);")

        release_layout = QVBoxLayout(release_panel)

        scroll_area = QScrollArea(self)
        scroll_area.setWidget(release_panel)
        scroll_area.setGeometry(20, 40, 800, self.height() - 120)
        scroll_area.setWidgetResizable(True)

        self.get_github_releases(release_layout)

    def add_info_panel(self):
        info_panel = QWidget(self)
        info_panel.setGeometry(830, 40, 250, self.height() - 120)
        info_panel.setStyleSheet("background-color: rgba(73, 171, 209, 0.7);")

        info_layout = QVBoxLayout(info_panel)

        label = QLabel(info_panel)
        label.setAlignment(Qt.AlignCenter)
        label.setText('''
            <div style="background-color: rgba(73, 171, 209, 0.5); padding: 10px;">
                <span style="font-size: 30px; font-weight: bold; color: white;">
                    FLAUNCHER
                </span><br>
                <span style="font-size: 16px; font-weight: normal; color: white;">
                    ЛАУНЧЕР ДЛЯ VOXELCORE
                </span>
            </div>
        ''')
        info_layout.addWidget(label)

        info_layout.addSpacing(5)

        button_voxel = QPushButton("VoxelWorld", info_panel)
        button_voxel.setStyleSheet("background-color: rgb(62, 148, 182); font-size: 18px; color: white; padding: 10px;")
        button_voxel.setFixedHeight(40)
        button_voxel.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://voxelworld.ru/profile/84")))
        info_layout.addWidget(button_voxel)

        info_layout.addSpacing(-7)

        button_freshlend = QPushButton("FreshLend Studio", info_panel)
        button_freshlend.setStyleSheet("background-color: rgb(62, 148, 182); font-size: 18px; color: white; padding: 10px;")
        button_freshlend.setFixedHeight(40)
        button_freshlend.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://freshlend.github.io")))
        info_layout.addWidget(button_freshlend)

        info_layout.addStretch(1)

    def on_download_button_click(self):
        selected_version = self.version_combo.currentText()

        if selected_version != "Получение версий...":
            version_folder = self.app_data_path / selected_version
            voxel_core_path = version_folder / "VoxelCore.exe"

            if os.path.exists(voxel_core_path):
                self.show_info_message("Информация", f"VoxelCore.exe уже существует в папке {version_folder}. Скачивание не требуется.")
            else:
                self.download_and_extract_version(selected_version)
        else:
            self.show_info_message("Выбор версии", "Пожалуйста, выберите версию для скачивания.")

    def on_play_button_click(self):
        selected_version = self.version_combo.currentText()

        if selected_version != "Получение версий...":
            version_folder = self.app_data_path / selected_version
            voxel_core_path = version_folder / "VoxelCore.exe"
            voxel_engine_path = version_folder / "VoxelEngine.exe"

            if os.path.exists(voxel_core_path) or os.path.exists(voxel_engine_path):
                exe_to_launch = voxel_core_path if os.path.exists(voxel_core_path) else voxel_engine_path
                self.launch_game(exe_to_launch, version_folder)
            else:
                self.show_error_message("Ошибка", "Сначала скачайте выбранную версию.")
        else:
            self.show_info_message("Выбор версии", "Пожалуйста, выберите версию для игры.")

    def refresh_versions(self):
        self.load_versions()

    def on_vwm_button_click(self):
        self.show_info_message("Скоро...", "Страница с модами будет когда-то...\nа пока ИДИ ИГРАЙ ИЛИ МОДЫ ДЕЛАЙ!")

    def open_versions_folder(self):
        url = QUrl.fromLocalFile(str(self.app_data_path))
        QDesktopServices.openUrl(url)

    def open_settings(self):
        self.show_info_message("Скоро...", "Настройки появятся через 10 веков!")

    def show_error_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

    def show_info_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

    def launch_game(self, voxel_core_path, working_directory):
        try:
            subprocess.Popen([str(voxel_core_path)], cwd=str(working_directory))
        except Exception as e:
            self.show_error_message("Ошибка запуска", f"Не удалось запустить игру: {str(e)}")

    def download_and_extract_version(self, version_tag):
        """
        Скачивает архив с версией с GitHub, распаковывает и сохраняет в директорию versions.
        Ищет файл с win64.zip в релизах.
        """
        try:
            api_url = f"https://api.github.com/repos/MihailRis/VoxelEngine-Cpp/releases/tags/{version_tag}"
            
            response = requests.get(api_url)
            if response.status_code == 200:
                release_data = response.json()
                
                file_url = None
                for asset in release_data.get('assets', []):
                    if 'win64.zip' in asset['name']:
                        file_url = asset['browser_download_url']
                        break
                
                if file_url:
                    zip_path = self.downloads_path / f"{release_data['tag_name']}_win64.zip"
                    self._download_file(file_url, zip_path)
                    
                    self.extract_zip(zip_path, version_tag)
                    
                    self.show_info_message("Успешно!", f"Версия {version_tag} успешно скачана и распакована!")
                else:
                    self.show_error_message("Ошибка", f"Не найден файл с win64.zip в релизе {version_tag}.")
            else:
                self.show_error_message("Ошибка", f"Не удалось получить информацию о релизе для версии {version_tag}. Код ошибки: {response.status_code}")
        
        except Exception as e:
            self.show_error_message("Ошибка", f"Ошибка при скачивании или распаковке: {e}")
    
    def _download_file(self, file_url, zip_path):
        """Скачивает файл по URL и сохраняет в указанном пути"""
        response = requests.get(file_url)
        if response.status_code == 200:
            with open(zip_path, "wb") as f:
                f.write(response.content)
        else:
            raise Exception(f"Не удалось скачать файл. Код ошибки: {response.status_code}")
    
    def extract_zip(self, zip_path, version_tag):
        """
        Распаковывает ZIP-файл в нужную директорию.
        Извлекает содержимое архива в папку, соответствующую версии.
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extraction_path = self.app_data_path / version_tag
                extraction_path.mkdir(parents=True, exist_ok=True)
                
                zip_ref.extractall(extraction_path)
                
                zip_files = zip_ref.namelist()

                folder_in_zip = zip_files[0].split('/')[0]

                folder_to_move = extraction_path / folder_in_zip

                if folder_to_move.exists():
                    for item in folder_to_move.iterdir():
                        shutil.move(str(item), extraction_path / item.name)
                    folder_to_move.rmdir()

            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception as e:
            self.show_error_message("Ошибка", f"Ошибка при распаковке архива: {e}")

    def create_app_data_directory(self):
        user_folder = Path(os.path.expanduser("~"))
        self.app_data_path = user_folder / "AppData" / "Roaming" / "com.flauncher.app" / "FLauncher" / "VE" / "versions"
        self.downloads_path = user_folder / "AppData" / "Roaming" / "com.flauncher.app" / "FLauncher" / "VE" / "downloads"
        
        self.app_data_path.mkdir(parents=True, exist_ok=True)
        self.downloads_path.mkdir(parents=True, exist_ok=True)

    def load_versions(self):
        url = "https://api.github.com/repos/MihailRis/VoxelEngine-Cpp/releases"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                releases = response.json()

                filtered_releases = [release for release in releases if not release['tag_name'].startswith('v11') and not release['tag_name'].startswith('v12')]
                user_versions = self.get_user_versions()

                self.version_combo.clear()

                added_versions = set()

                for version in user_versions:
                    if version not in added_versions:
                        self.version_combo.addItem(version)
                        added_versions.add(version)

                for release in filtered_releases:
                    release_version = release['tag_name']
                    if release_version not in added_versions:
                        self.version_combo.addItem(release_version)
                        added_versions.add(release_version)

                if user_versions or filtered_releases:
                    self.version_combo.setCurrentIndex(0)

        except Exception as e:
            self.show_error_message("Ошибка", f"Ошибка при загрузке версий: {e}")
            self.version_combo.clear()
            user_versions = self.get_user_versions()
            
            for version in user_versions:
                self.version_combo.addItem(version)

    def fetch_versions(self):
        try:
            response = requests.get("https://api.github.com/repos/MihailRis/VoxelEngine-Cpp/releases")
            if response.status_code == 200:
                releases = response.json()

                filtered_releases = [release for release in releases if not release['tag_name'].startswith('v11') and not release['tag_name'].startswith('v12')]

                user_versions = self.get_user_versions()

                self.version_combo.clear()

                added_versions = set()

                for version in user_versions:
                    if version not in added_versions:
                        self.version_combo.addItem(version)
                        added_versions.add(version)

                for release in filtered_releases:
                    release_version = release['tag_name']
                    if release_version not in added_versions:
                        self.version_combo.addItem(release_version)
                        added_versions.add(release_version)

                if user_versions or filtered_releases:
                    self.version_combo.setCurrentIndex(0)

                self.timer.stop()

        except Exception as e:
            print(f"Ошибка при загрузке версий: {e}")
            self.version_combo.clear()
            self.version_combo.addItem("Ошибка загрузки данных")
            
            user_versions = self.get_user_versions()

            for version in user_versions:
                self.version_combo.addItem(version)

    def get_user_versions(self):
        """
        Получаем список пользовательских версий из папок в директории версий.
        """
        user_versions = []
        if self.app_data_path.exists():
            for folder in self.app_data_path.iterdir():
                if folder.is_dir():
                    user_versions.append(folder.name)
        return user_versions

    def get_github_releases(self, layout):
        url = "https://api.github.com/repos/MihailRis/VoxelEngine-Cpp/releases"

        try:
            response = requests.get(url)
            releases = response.json()

            count = 0

            for release in releases:
                if count >= 30:
                    break

                tag_name = release.get('tag_name', '')
                version = tag_name.replace('voxelcore', '').strip()

                release_url = release.get('html_url', '#')

                release_date_str = release.get('published_at', '')
                if release_date_str:
                    release_date = datetime.strptime(release_date_str, '%Y-%m-%dT%H:%M:%SZ')
                    release_date_formatted = release_date.strftime('%d %B %Y')

                release_layout = QHBoxLayout()

                version_label = QLabel(f'VoxelCore<a href="{release_url}"> {version}</a>', self)
                version_label.setStyleSheet("font-weight: bold; font-size: 24px; color: black;")
                version_label.setOpenExternalLinks(True)

                date_label = QLabel(f'Дата релиза: {release_date_formatted}', self)
                date_label.setStyleSheet("font-size: 12px; color: gray; margin-left: 10px;")

                release_layout.addWidget(version_label)
                release_layout.addWidget(date_label)

                layout.addLayout(release_layout)

                release_body = release['body']
                html_body = markdown.markdown(release_body)
                html_body = html_body.replace('<a', '<a target="_blank"')

                release_info_label = QLabel(self)
                release_info_label.setOpenExternalLinks(True)
                release_info_label.setText(html_body)
                release_info_label.setWordWrap(True)
                release_info_label.setStyleSheet("font-weight: bold; font-size: 14px; line-height: 1.5; color: black;")
                layout.addWidget(release_info_label)

                separator = QFrame(self)
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("background-color: black; height: 2px;")
                layout.addWidget(separator)

                layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

                count += 1

        except requests.RequestException as e:
            error_label = QLabel("Не удалось загрузить релизы.", self)
            error_label.setStyleSheet("font-size: 18px; color: red;")
            layout.addWidget(error_label)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FLauncher()
    window.show()
    sys.exit(app.exec_())
