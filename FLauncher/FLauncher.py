# -*- coding: utf-8 -*-

import sys, os, subprocess, zipfile, shutil, requests, markdown, time, threading, asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel, QSpacerItem, QSizePolicy, QFrame, QPushButton, QComboBox, QMessageBox, QHBoxLayout, QProgressBar, QTextBrowser
from PyQt5.QtGui import QPalette, QBrush, QImage, QDesktopServices, QIcon
from PyQt5.QtCore import Qt, QUrl, QSize, QCoreApplication
from pathlib import Path
from datetime import datetime
from pypresence import Presence

def resource_path(relative_path):
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

        self.client_id = "1143147014226444338"
        self.discord_presence = Presence(self.client_id)
        self.discord_presence = None
        self.connectToDiscord()
        self.setDiscordPresence()

        self.add_release_panel()
        self.add_info_panel()
        self.add_settings_panel()
        self.add_FL_MODS()
        self.set_background()
        self.add_blue_bar()
        self.create_app_data_directory()
        self.load_versions()

    def connectToDiscord(self):
        try:
            self.discord_presence = Presence(self.client_id)
            self.discord_presence.connect()
        except Exception as e:
            print(f"Ошибка при подключении к Discord: {e}")
            self.discord_presence = None

    def setDiscordPresence(self):
        if self.discord_presence:
            details = "Просматривает главную страницу"
            threading.Thread(target=self.updatePresenceAsync, args=(details,)).start()

    def updatePresenceAsync(self, details):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if self.discord_presence:
                self.discord_presence.update(
                    details=details,
                    start=time.time(),
                    large_image="icon"
                )
            else:
                pass
        except Exception as e:
            print(f"Ошибка при обновлении статуса Discord: {e}")

    def set_background(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        image = QImage(resource_path('ui/background.png'))
        brush = QBrush(image)
        palette.setBrush(QPalette.Background, brush)
        self.setPalette(palette)

    def add_blue_bar(self):
        blue_bar = QWidget(self)
        blue_bar.setGeometry(0, self.height() - 90, self.width(), 90)
        blue_bar.setStyleSheet("background-color: rgba(113, 169, 76, 0.9);")

        self.version_combo = QComboBox(blue_bar)
        self.version_combo.setGeometry(10, 20, 200, 60)
        self.version_combo.setStyleSheet("background-color: white; color: black; font-size: 18px; font-weight: bold;")
        self.version_combo.addItem("Получение версий...")

        self.download_button = QPushButton("Скачать", blue_bar)
        self.download_button.setGeometry(220, 20, 150, 30)
        self.download_button.setStyleSheet("background-color: rgb(236, 193, 63); color: white; font-size: 18px; font-weight: bold;")
        self.download_button.clicked.connect(self.on_download_button_click)

        self.progress_bar = QProgressBar(blue_bar)
        self.progress_bar.setGeometry(10, 0, self.width() - 20, 20)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        self.download_info_label = QLabel("0 KB / 0 KB, Скорость: 0 KB/s", blue_bar)
        self.download_info_label.setGeometry(10, 0, self.width() - 20, 20)
        self.download_info_label.setStyleSheet("font-size: 12px; color: black;")
        self.download_info_label.setAlignment(Qt.AlignCenter)

        self.play_button = QPushButton("Играть", blue_bar)
        self.play_button.setGeometry(220, 50, 150, 30)
        self.play_button.setStyleSheet("background-color: rgb(236, 193, 63); color: white; font-size: 18px; font-weight: bold;")
        self.play_button.clicked.connect(self.on_play_button_click)

        icon_flm = QIcon(resource_path("ui/FLM.png"))
        self.flm_button = QPushButton(blue_bar)
        self.flm_button.setIcon(icon_flm)
        self.flm_button.setIconSize(QSize(60, 60))
        self.flm_button.setGeometry(835, 20, 60, 60)
        self.flm_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
        """)
        self.flm_button.clicked.connect(self.on_flm_button_click)

        icon_reload = QIcon(resource_path("ui/reload.png"))
        self.reload_button = QPushButton(blue_bar)
        self.reload_button.setIcon(icon_reload)
        self.reload_button.setIconSize(QSize(30, 30))
        self.reload_button.setGeometry(895, 20, 60, 60)
        self.reload_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
        """)
        self.reload_button.clicked.connect(self.refresh_versions)

        icon_folder = QIcon(resource_path("ui/folder.png"))
        self.folder_button = QPushButton(blue_bar)
        self.folder_button.setIcon(icon_folder)
        self.folder_button.setIconSize(QSize(30, 30))
        self.folder_button.setGeometry(965, 20, 60, 60)
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
        self.settings_button.setGeometry(1035, 20, 60, 60)
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
        release_panel.setGeometry(20, 40, 700, self.height() - 130)
        release_panel.setStyleSheet("background-color: rgba(255, 255, 255, 0.7);")

        release_layout = QVBoxLayout(release_panel)

        scroll_area = QScrollArea(self)
        scroll_area.setWidget(release_panel)
        scroll_area.setGeometry(20, 40, 800, self.height() - 130)
        scroll_area.setWidgetResizable(True)

        self.get_github_releases(release_layout)

    def add_info_panel(self):
        info_panel = QWidget(self)
        info_panel.setGeometry(830, 0, 250, self.height() - 90)
        info_panel.setStyleSheet("background-color: rgba(90, 171, 215, 0.9);")

        info_layout = QVBoxLayout(info_panel)

        label = QLabel(info_panel)
        label.setAlignment(Qt.AlignCenter)
        label.setText('''
            <div style="background-color: rgba(90, 171, 215, 0.9); padding: 10px;">
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

    def add_settings_panel(self):
        self.settings_background = QWidget(self)
        self.settings_background.setGeometry(0, 0, 1100, self.height())

        self.settings_panel = QWidget(self)
        self.settings_panel.setGeometry(200, 20, 700, self.height() - 130)
        self.settings_panel.setStyleSheet("background-color: white;")

        self.blue_strip = QWidget(self.settings_panel)
        self.blue_strip.setGeometry(0, 0, self.settings_panel.width(), 40)
        self.blue_strip.setStyleSheet("background-color: #00aaff;")

        blue_layout = QHBoxLayout(self.blue_strip)

        settings_label = QLabel('Настройки', self.blue_strip)
        settings_label.setAlignment(Qt.AlignCenter)
        settings_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        blue_layout.addWidget(settings_label)

        blue_layout.setContentsMargins(10, 0, 10, 0)
        blue_layout.setSpacing(10)

        blue_layout.setStretch(1, 1)

        layout = QVBoxLayout(self.settings_panel)

        text_browser = QTextBrowser(self.settings_panel)
        text_browser.setAlignment(Qt.AlignTop)
        text_browser.setText('''
            <div>
                <span style="font-size: 16px; font-weight: normal; color: black;">
                    Настроек пока что нет, появится когда я захочу, это будет через неизвестное время, так что ждите сто лет, у меня много других проектов, а я такой человек тот кто не доделывает проекты, мне больше интересна разработка искуственного интеллекта и создание новых проектов.<br>Просто ожидайте...<br>Сейчас максимум баги или обнову для онлайн сделаю когда он выйдет, ну и идея у меня есть создать сайт и контент-пак для достижений в игре и сколько времени вы провели в игре (не планирую создавать это просто идея, можете смело реализовать её в своих проектах), а на этом я прощаюсь, слишком много пишу, я всегда такой...<br><a href="https://discord.com/oauth2/authorize?client_id=1137405206288666634" style="color: blue; text-decoration: underline;">Оцените мой проект: Petya_Ai (искуственный интеллект, пока что тупой, но он с самообучением, умеет использовать кастомные эмодзи по смыслу, но не всегда. ещё умеет аудио отправлять и планирую возможность говорить в голосовом добавить. одноздачно повеселит.)</a><br><a href="http://f1.aurorix.net:38052" style="color: blue; text-decoration: underline;">FreshTube - копия (вообще не копия) ютуба</a><br>но запускаю я его не часто так как у меня нет видеокарты поддерживающей ИИ, а процессора для моего ИИ скоро будет не хватать так как он его уже грузит на 80% при генерации токенов.<br>Видеокарта: GTX550Ti<br>ЦП: Intel Core i7-3770k<br>ОЗУ: 8Gb
                </span>
            </div>
        ''')
        text_browser.setOpenExternalLinks(True)

        layout.addWidget(text_browser)

        layout.setContentsMargins(10, 40, 10, 10)
        layout.setSpacing(20)

        self.settings_panel.hide()
        self.settings_background.hide()

    def add_FL_MODS(self):
        self.FL_MODS_background = QWidget(self)
        self.FL_MODS_background.setGeometry(0, 0, 1100, self.height())

        self.FL_MODS = QWidget(self)
        self.FL_MODS.setGeometry(0, 0, 1100, self.height() - 90)
        self.FL_MODS.setStyleSheet("background-color: white;")

        self.blue_strip = QWidget(self.FL_MODS)
        self.blue_strip.setGeometry(0, 0, self.FL_MODS.width(), 40)
        self.blue_strip.setStyleSheet("background-color: #00aaff;")

        blue_layout = QHBoxLayout(self.blue_strip)

        FL_MODS_label = QLabel('FLMODS', self.blue_strip)
        FL_MODS_label.setAlignment(Qt.AlignCenter)
        FL_MODS_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        blue_layout.addWidget(FL_MODS_label)

        blue_layout.setContentsMargins(10, 0, 10, 0)
        blue_layout.setSpacing(10)

        blue_layout.setStretch(1, 1)

        layout = QVBoxLayout(self.FL_MODS)

        text_browser = QTextBrowser(self.FL_MODS)
        text_browser.setAlignment(Qt.AlignTop)
        text_browser.setText('''
            <div>
                <span style="font-size: 16px; font-weight: normal; color: black;">
                    Страницы модов пока что нет, появится когда я захочу, это будет через неизвестное время, так что ждите сто лет, у меня много других проектов, а я такой человек тот кто не доделывает проекты, мне больше интересна разработка искуственного интеллекта и создание новых проектов.<br>Просто ожидайте...<br>Сейчас максимум баги или обнову для онлайн сделаю когда он выйдет, ну и идея у меня есть создать сайт и контент-пак для достижений в игре и сколько времени вы провели в игре (не планирую создавать это просто идея, можете смело реализовать её в своих проектах), а на этом я прощаюсь, слишком много пишу, я всегда такой...<br><a href="https://discord.com/oauth2/authorize?client_id=1137405206288666634" style="color: blue; text-decoration: underline;">Оцените мой проект: Petya_Ai (искуственный интеллект, пока что тупой, но он с самообучением, умеет использовать кастомные эмодзи по смыслу, но не всегда. ещё умеет аудио отправлять и планирую возможность говорить в голосовом добавить. одноздачно повеселит.)</a><br><a href="http://f1.aurorix.net:38052" style="color: blue; text-decoration: underline;">FreshTube - копия (вообще не копия) ютуба</a><br>но запускаю я его не часто так как у меня нет видеокарты поддерживающей ИИ, а процессора для моего ИИ скоро будет не хватать так как он его уже грузит на 80% при генерации токенов.<br>Видеокарта: GTX550Ti<br>ЦП: Intel Core i7-3770k<br>ОЗУ: 8Gb
                </span>
            </div>
        ''')
        text_browser.setOpenExternalLinks(True)

        layout.addWidget(text_browser)

        layout.setContentsMargins(10, 40, 10, 10)
        layout.setSpacing(20)

        self.FL_MODS.hide()
        self.FL_MODS_background.hide()

    def on_download_button_click(self):
        selected_version = self.version_combo.currentText()

        if selected_version != "Получение версий...":
            version_folder = self.app_data_path / selected_version

            exe_files = list(version_folder.glob("*.exe"))

            if exe_files:
                self.show_info_message("Информация", f"В папке {version_folder} уже есть .exe файлы. Скачивание не требуется.")
            else:
                self.download_and_extract_version(selected_version)
        else:
            self.show_info_message("Выбор версии", "Пожалуйста, выберите версию для скачивания.")

    def on_play_button_click(self):
        selected_version = self.version_combo.currentText()

        if selected_version != "Получение версий...":
            version_folder = self.app_data_path / selected_version

            exe_files = [f for f in os.listdir(version_folder) if f.endswith(".exe") and f.lower() != "vctest.exe"]

            if exe_files:
                exe_to_launch = version_folder / exe_files[0]
                self.launch_game(exe_to_launch, version_folder)
            else:
                self.show_error_message("Ошибка", "Сначала скачайте выбранную версию.")
        else:
            self.show_info_message("Выбор версии", "Пожалуйста, выберите версию для игры.")

    def refresh_versions(self):
        self.load_versions()

    def on_flm_button_click(self):
        if self.FL_MODS.isVisible():
            self.FL_MODS.hide()
            self.FL_MODS_background.hide()
        else:
            self.FL_MODS.show()
            self.FL_MODS_background.show()

    def open_versions_folder(self):
        url = QUrl.fromLocalFile(str(self.app_data_path))
        QDesktopServices.openUrl(url)

    def open_settings(self):
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
            self.settings_background.hide()
        else:
            self.settings_panel.show()
            self.settings_background.show()

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
        try:
            self.download_start_time = time.time()
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
        response = requests.get(file_url, stream=True)
        
        if response.status_code == 200:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0
            chunk_size = 1024

            with open(zip_path, 'wb') as f:
                for data in response.iter_content(chunk_size=chunk_size):
                    downloaded_size += len(data)
                    f.write(data)
                    
                    progress = int((downloaded_size / total_size) * 100)
                    self.progress_bar.setValue(progress)
                    
                    speed = (downloaded_size / 1024) / (time.time() - self.download_start_time)
                    remaining_size = total_size - downloaded_size
                    remaining_time = remaining_size / (speed * 1024) if speed > 0 else 0
                    remaining_time_str = time.strftime("%H:%M:%S", time.gmtime(remaining_time))

                    downloaded_size_kb = downloaded_size / 1024
                    total_size_kb = total_size / 1024
                    self.download_info_label.setText(f"{downloaded_size_kb:.2f} KB / {total_size_kb:.2f} KB, "
                                                    f"Скорость: {speed:.2f} KB/s, Осталось: {remaining_time_str}")

                    QCoreApplication.processEvents()

        else:
            raise Exception(f"Не удалось скачать файл. Код ошибки: {response.status_code}")
    
    def extract_zip(self, zip_path, version_tag):
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
            print(f"Ошибка при загрузке версий: {e}\nВозможно у вас нет интернет соеденения.")
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
            response.raise_for_status()
            releases = response.json()

            count = 0

            for release in releases:
                if count >= 30:
                    break

                if isinstance(release, dict):
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

                    release_body = release.get('body', '')
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

        except ValueError as e:
            error_label = QLabel("Ошибка при обработке данных.", self)
            error_label.setStyleSheet("font-size: 18px; color: red;")
            layout.addWidget(error_label)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FLauncher()
    window.show()
    sys.exit(app.exec_())
