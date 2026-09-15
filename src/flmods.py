import os
import shutil
import time
import queue
import requests
import zipfile
from pathlib import Path
from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox,
    QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont


def format_relative_time(iso_str):
    if not iso_str or not isinstance(iso_str, str):
        return "неизвестно"
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - dt
        if delta.total_seconds() < 0:
            return "только что"
        years = delta.days // 365
        months = (delta.days // 30) % 12
        days = delta.days % 30
        if days >= 15:
            months += 1
        if months >= 12:
            years += 1
            months = 0

        def plural(n, one, few, many):
            n = abs(n) % 100
            n1 = n % 10
            if 10 < n < 20:
                return many
            if 1 < n1 < 5:
                return few
            if n1 == 1:
                return one
            return many

        if years > 0:
            return f"{years} {plural(years, 'год', 'года', 'лет')} назад"
        if months > 0:
            return f"{months} {plural(months, 'месяц', 'месяца', 'месяцев')} назад"
        if days > 0:
            return f"{days} {plural(days, 'день', 'дня', 'дней')} назад"
        if delta.seconds // 3600 > 0:
            hours = delta.seconds // 3600
            return f"{hours} {plural(hours, 'час', 'часа', 'часов')} назад"
        if delta.seconds // 60 > 0:
            minutes = delta.seconds // 60
            return f"{minutes} {plural(minutes, 'минуту', 'минуты', 'минут')} назад"
        return "только что"
    except Exception:
        return iso_str


class VoxelWorldAPI:
    BASE_URL = "https://api.voxelworld.ru/v2"

    def __init__(self):
        self.headers = {
            "User-Agent": "FLauncher/0.7.0 (freshlend.studio@gmail.com)",
            "Accept": "application/json"
        }

    def get_data(self, endpoint, search_query="", sort_method="Популярные", page=1, tag_ids=None):
        sort_map = {"Популярные": (1, "desc"), "Новые": (2, "desc"), "По алфавиту": (3, "asc")}
        sort_val, sort_order = sort_map.get(sort_method, (1, "desc"))
        params = {"page": page, "sortOrder": sort_order, "sort": sort_val, "item_count": 100}

        if search_query:
            params["title"] = search_query
        if tag_ids:
            if isinstance(tag_ids, int):
                tag_ids = [tag_ids]
            params['tag_id[]'] = tag_ids

        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", headers=self.headers,
                                    params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                for key in ['mods', 'items', 'data', 'results', 'texturepacks', 'worlds']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
            if isinstance(data, list):
                return data
        except Exception as e:
            print(f"Ошибка API (список): {e}")
        return []

    def get_tags(self, tag_type):
        try:
            response = requests.get(f"{self.BASE_URL}/tags", headers=self.headers,
                                    params={"type": tag_type}, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ['tags', 'items', 'data', 'results']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
        except Exception as e:
            print(f"Ошибка получения тегов ({tag_type}): {e}")
        return []

    def get_latest_version(self, mod_id):
        for attempt in range(3):
            try:
                response = requests.get(f"{self.BASE_URL}/mods/{mod_id}/versions/latest",
                                        headers=self.headers, timeout=10)
                if response.status_code == 429:
                    time.sleep(3)
                    continue
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict):
                    if data.get("version_number"):
                        return str(data.get("version_number"))
                    if data.get("version"):
                        return str(data.get("version"))
                    if data.get("tag_name"):
                        return str(data.get("tag_name"))
                    engine = data.get("engine")
                    if isinstance(engine, dict) and engine.get("version_number"):
                        return str(engine.get("version_number"))
                    inner_data = data.get("data")
                    if isinstance(inner_data, dict):
                        if inner_data.get("version_number"):
                            return str(inner_data.get("version_number"))
                        engine_inner = inner_data.get("engine")
                        if isinstance(engine_inner, dict) and engine_inner.get("version_number"):
                            return str(engine_inner.get("version_number"))
            except Exception:
                time.sleep(1)
                continue
        return "Неизвестно"

    def get_version_info(self, content_type, content_id):
        for attempt in range(3):
            try:
                response = requests.get(
                    f"{self.BASE_URL}/{content_type}/{content_id}/versions/latest",
                    headers=self.headers, timeout=10
                )
                if response.status_code == 429:
                    time.sleep(3)
                    continue
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict):
                    inner = data.get('data', data)
                    if isinstance(inner, dict):
                        return inner
            except Exception:
                time.sleep(1)
                continue
        return None

    def get_download_url(self, content_type, content_id, version_id):
        try:
            response = requests.get(
                f"{self.BASE_URL}/{content_type}/{content_id}/versions/{version_id}/download",
                headers=self.headers, timeout=15, allow_redirects=True
            )
            if response.status_code == 200:
                return response.url
        except Exception as e:
            print(f"Ошибка получения URL загрузки: {e}")
        return None

    def download_version(self, content_type, content_id, version_id,
                         progress_callback=None, is_cancelled_callback=None,
                         downloads_path=None):
        try:
            info = self.get_version_info(content_type, content_id)
            download_url = None
            if isinstance(info, dict):
                download_url = (info.get('download_url') or info.get('file_url')
                                or info.get('url') or info.get('download'))
            if not download_url:
                download_url = self.get_download_url(content_type, content_id, version_id)
            if not download_url:
                return False, None, "Не удалось получить ссылку на скачивание"

            if downloads_path is None:
                downloads_path = Path.home() / "Downloads"
            downloads_path = Path(downloads_path)
            downloads_path.mkdir(parents=True, exist_ok=True)

            zip_path = downloads_path / f"{content_type}_{content_id}_{version_id}.zip"

            response = requests.get(download_url, headers=self.headers,
                                    stream=True, timeout=30)
            if response.status_code != 200:
                return False, None, f"Ошибка загрузки: {response.status_code}"

            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if is_cancelled_callback and is_cancelled_callback():
                        f.close()
                        if zip_path.exists():
                            zip_path.unlink()
                        return False, None, "Загрузка отменена"
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(int((downloaded / total_size) * 100))

            return True, zip_path, None
        except Exception as e:
            return False, None, str(e)


class APIWorker(QThread):
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    list_finished = pyqtSignal()

    def __init__(self, endpoint, search_query="", sort_method="Популярные",
                 page=1, tag_ids=None, is_pagination=False):
        super().__init__()
        self.endpoint = endpoint
        self.search_query = search_query
        self.sort_method = sort_method
        self.page = page
        self.tag_ids = tag_ids
        self.is_pagination = is_pagination
        self.cancelled = False

    def run(self):
        if self.cancelled:
            return
        api = VoxelWorldAPI()
        data = api.get_data(self.endpoint, self.search_query, self.sort_method,
                            self.page, self.tag_ids)
        if self.cancelled:
            return
        if data:
            self.data_loaded.emit(data)
        elif self.is_pagination:
            self.list_finished.emit()
        else:
            self.error_occurred.emit(f"Не удалось загрузить раздел: {self.endpoint}")


class TagWorker(QThread):
    tags_loaded = pyqtSignal(list)

    def __init__(self, tag_type):
        super().__init__()
        self.tag_type = tag_type
        self.cancelled = False

    def run(self):
        if self.cancelled:
            return
        api = VoxelWorldAPI()
        tags = api.get_tags(self.tag_type)
        if self.cancelled:
            return
        self.tags_loaded.emit(tags)


class ImageDownloaderThread(QThread):
    image_downloaded = pyqtSignal(str, bytes)

    def __init__(self, image_queue):
        super().__init__()
        self.image_queue = image_queue
        self.running = True

    def run(self):
        headers = {"User-Agent": "MyTLauncher/1.0 (support@mygame.com)"}
        while self.running:
            try:
                url = self.image_queue.get(timeout=1)
                if url is None:
                    break
                if url:
                    try:
                        resp = requests.get(url, headers=headers, timeout=5)
                        if resp.status_code == 200:
                            self.image_downloaded.emit(url, resp.content)
                        else:
                            self.image_downloaded.emit(url, b'')
                    except Exception:
                        self.image_downloaded.emit(url, b'')
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка в очереди картинок: {e}")
                break

    def stop(self):
        self.running = False
        self.wait(3000)


class VersionDownloaderThread(QThread):
    version_fetched = pyqtSignal(int, str)

    def __init__(self, version_queue):
        super().__init__()
        self.version_queue = version_queue
        self.running = True

    def run(self):
        while self.running:
            try:
                mod_id = self.version_queue.get(timeout=1)
                if mod_id is None:
                    break
                if mod_id:
                    api = VoxelWorldAPI()
                    version = api.get_latest_version(mod_id)
                    if not self.running:
                        break
                    self.version_fetched.emit(mod_id, version)
                    time.sleep(0.05)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка в очереди версий: {e}")
                break

    def stop(self):
        self.running = False
        self.wait(3000)


class ModCard(QFrame):
    image_requested = pyqtSignal(str)
    install_clicked = pyqtSignal(int, str, str, str)

    def __init__(self, mod_data, content_type="mods", cached_version=None,
                 image_cache=None, parent=None):
        super().__init__(parent)
        if not isinstance(mod_data, dict):
            mod_data = {}
        self.mod_id = mod_data.get("id")
        self.mod_title = mod_data.get("title", "Unknown Mod")
        self.content_type = content_type
        self.icon_url = mod_data.get("logo_url") or mod_data.get("icon")
        self.image_cache = image_cache if image_cache else {}

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                margin: 4px;
            }
            QFrame:hover {
                border: 1px solid #3498db;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setStyleSheet("background-color: #ccc; border-radius: 6px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        if self.icon_url and self.icon_url in self.image_cache:
            self.set_image_from_data(self.image_cache[self.icon_url])
        elif self.icon_url and self.icon_url.startswith(('http://', 'https://')):
            self.icon_label.setText("Загрузка...")
            QTimer.singleShot(0, lambda: self.image_requested.emit(self.icon_url))
        else:
            self.icon_label.setText("No Img")

        author_data = mod_data.get("author", "Unknown")
        if isinstance(author_data, dict):
            author_name = author_data.get("name", "Unknown")
        else:
            author_name = author_data

        info_layout = QVBoxLayout()
        title_label = QLabel(self.mod_title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(title_label)
        author_label = QLabel(f"Автор: {author_name}")
        author_label.setStyleSheet("color: #555;")
        info_layout.addWidget(author_label)
        desc_label = QLabel(str(mod_data.get("description", ""))[:300] + "...")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #777;")
        info_layout.addWidget(desc_label)

        downloads = mod_data.get('downloads', 0)
        raw_date = mod_data.get("last_update_date", "")
        updated = format_relative_time(raw_date)
        self.version_text = "Версия: Загрузка..."
        if cached_version:
            self.version_text = f"Версия: {cached_version}"

        meta_label = QLabel(f"Загрузок: {downloads} | Обновлено: {updated}")
        meta_label.setStyleSheet("color: #999; font-size: 10px;")
        self.version_label = QLabel(self.version_text)
        self.version_label.setStyleSheet("color: #999; font-size: 10px;")
        info_layout.addWidget(meta_label)
        info_layout.addWidget(self.version_label)
        layout.addLayout(info_layout, stretch=1)

        self.action_btn = QPushButton("Установить")
        self.action_btn.setFixedSize(120, 35)
        self._apply_install_style()
        self.action_btn.clicked.connect(self._on_install)
        layout.addWidget(self.action_btn)

    def _apply_install_style(self):
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)

    def _apply_reinstall_style(self):
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)

    def set_image_from_data(self, data):
        if not data:
            self.icon_label.setText("Err")
            return
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if not pixmap.isNull():
            self.icon_label.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.icon_label.setText("Err")

    def update_version(self, version):
        self.version_label.setText(f"Версия: {version}")

    def set_installed(self, installed):
        if installed:
            self.action_btn.setText("Переустановить")
            self._apply_reinstall_style()
        else:
            self.action_btn.setText("Установить")
            self._apply_install_style()

    def _on_install(self):
        if self.mod_id is None:
            return
        self.install_clicked.emit(self.mod_id, self.mod_title,
                                  self.version_text.replace("Версия: ", ""),
                                  self.content_type)


class InstallWorker(QThread):
    install_progress = pyqtSignal(int, str)
    install_finished = pyqtSignal(bool, str, str, str)

    def __init__(self, content_id, content_name, version_number, content_type,
                 core_version, downloads_path, app_data_path):
        super().__init__()
        self.content_id = content_id
        self.content_name = content_name
        self.version_number = version_number
        self.content_type = content_type
        self.core_version = core_version
        self.downloads_path = downloads_path
        self.app_data_path = app_data_path
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            api = VoxelWorldAPI()
            self.install_progress.emit(0, f"Получение информации о {self.content_name}...")

            version_info = api.get_version_info(self.content_type, self.content_id)
            if not version_info:
                self.install_finished.emit(False, "Не удалось получить информацию о версии",
                                           self.content_name, self.core_version)
                return

            version_id = version_info.get('id') or version_info.get('version_id')
            if not version_id:
                self.install_finished.emit(False, "Не найден ID версии",
                                           self.content_name, self.core_version)
                return

            def progress_cb(p):
                self.install_progress.emit(p, f"Скачивание {self.content_name}... {p}%")

            def cancel_cb():
                return self.is_cancelled

            success, zip_path, error = api.download_version(
                self.content_type, self.content_id, version_id,
                progress_callback=progress_cb,
                is_cancelled_callback=cancel_cb,
                downloads_path=self.downloads_path
            )

            if self.is_cancelled:
                if zip_path and os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except Exception:
                        pass
                self.install_finished.emit(False, "Установка отменена",
                                           self.content_name, self.core_version)
                return

            if not success or not zip_path:
                self.install_finished.emit(False, error or "Не удалось скачать",
                                           self.content_name, self.core_version)
                return

            self.install_progress.emit(90, "Распаковка архива...")

            core_version_folder = Path(self.app_data_path) / self.core_version
            if self.content_type == "worlds":
                install_folder = core_version_folder / "worlds" / self.content_name
            else:
                install_folder = core_version_folder / "content" / self.content_name

            if install_folder.exists():
                try:
                    shutil.rmtree(install_folder)
                except Exception:
                    pass
            install_folder.mkdir(parents=True, exist_ok=True)

            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(install_folder)
            except Exception as e:
                self.install_finished.emit(False, f"Ошибка распаковки: {e}",
                                           self.content_name, self.core_version)
                return
            finally:
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except Exception:
                        pass

            try:
                items = list(install_folder.iterdir())
                if len(items) == 1 and items[0].is_dir():
                    folder_path = items[0]
                    for item in folder_path.iterdir():
                        dest = install_folder / item.name
                        if dest.exists():
                            if dest.is_dir():
                                shutil.rmtree(dest)
                            else:
                                dest.unlink()
                        shutil.move(str(item), str(install_folder))
                    shutil.rmtree(folder_path)
            except Exception:
                pass

            self.install_progress.emit(100, f"{self.content_name} установлен!")
            self.install_finished.emit(
                True,
                f"{self.content_name} установлен в версию {self.core_version}",
                self.content_name,
                self.core_version
            )
        except Exception as e:
            self.install_finished.emit(False, str(e), self.content_name, self.core_version)


class ModsWidget(QWidget):
    install_requested = pyqtSignal(int, str, str, str)

    def __init__(self, settings_manager, thread_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.thread_manager = thread_manager
        self.target_version_folder = None
        self.installed_items = set()
        self._is_active = False

        self.all_mods = []
        self.current_tab = "mods"
        self.current_page = 1
        self.is_loading = False
        self.has_more = True
        self.version_cache = {}
        self.active_cards = {}
        self.tags_loaded_flags = {}

        self.is_initializing = True
        self.is_waiting_for_retry = False
        self.retry_btn = None

        self.image_cache = {}
        self.image_queue = queue.Queue()
        self.active_downloads = set()
        self.image_workers = []

        self.version_queue = queue.Queue()
        self.version_workers = []
        self.active_version_downloads = set()

        self.cache = {}
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.reload_data)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #3498db; color: white;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 10, 15, 10)

        self.btn_mods = QPushButton("Моды")
        self.btn_respacks = QPushButton("Ресурс-паки")
        self.btn_maps = QPushButton("Карты")
        self.tab_buttons = {self.btn_mods: "mods",
                            self.btn_respacks: "texturepacks",
                            self.btn_maps: "worlds"}

        for btn, tab in self.tab_buttons.items():
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: white;
                    border: none;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.1);
                }
            """)
            btn.clicked.connect(lambda checked, b=btn, t=tab: self.switch_tab(b, t))
            top_layout.addWidget(btn)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск по названию...")
        self.search_bar.setFixedWidth(250)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                color: black;
            }
        """)
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        top_layout.addWidget(self.search_bar)

        self.tag_combo = QComboBox()
        self.tag_combo.setMinimumWidth(150)
        self.tag_combo.addItem("Все теги", None)
        self.tag_combo.currentTextChanged.connect(self.on_tag_changed)
        self.tag_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
                color: black;
            }
        """)
        top_layout.addWidget(self.tag_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Популярные", "Новые", "По алфавиту"])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        self.sort_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
                color: black;
            }
        """)
        top_layout.addWidget(self.sort_combo)

        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #3498db;
                font-weight: bold;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        self.btn_refresh.clicked.connect(self.force_refresh_current_tab)
        top_layout.addWidget(self.btn_refresh)

        main_layout.addWidget(top_bar)

        self.mods_scroll = QScrollArea()
        self.mods_scroll.setWidgetResizable(True)
        self.mods_content = QWidget()
        self.mods_layout = QVBoxLayout(self.mods_content)
        self.mods_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.mods_scroll.setWidget(self.mods_content)
        self.mods_scroll.verticalScrollBar().valueChanged.connect(self.check_scroll_bottom)
        main_layout.addWidget(self.mods_scroll)

    def start(self):
        if self._is_active:
            return
        self._is_active = True

        self.all_mods = []
        self.version_cache = {}
        self.active_cards.clear()
        self.image_cache = {}
        self.active_downloads = set()
        self.active_version_downloads = set()
        self.cache = {}
        self.tags_loaded_flags = {}
        self.current_page = 1
        self.has_more = True
        self.is_loading = False
        self.is_waiting_for_retry = False

        self.image_workers = []
        for _ in range(3):
            worker = ImageDownloaderThread(self.image_queue)
            worker.image_downloaded.connect(self.on_image_loaded)
            worker.start()
            self.image_workers.append(worker)

        self.version_workers = []
        for _ in range(3):
            worker = VersionDownloaderThread(self.version_queue)
            worker.version_fetched.connect(self.on_version_fetched)
            worker.start()
            self.version_workers.append(worker)

        self.reload_data()

    def stop(self):
        if not self._is_active:
            return
        self._is_active = False

        if hasattr(self, 'tag_worker') and self.tag_worker and self.tag_worker.isRunning():
            self.tag_worker.cancelled = True
            self.tag_worker.wait(1000)

        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.cancelled = True
            self.worker.wait(1000)

        for _ in self.image_workers:
            try:
                self.image_queue.put_nowait(None)
            except Exception:
                pass
        for _ in self.version_workers:
            try:
                self.version_queue.put_nowait(None)
            except Exception:
                pass

        for w in self.image_workers:
            w.stop()
        for w in self.version_workers:
            w.stop()
        self.image_workers = []
        self.version_workers = []

        while not self.image_queue.empty():
            try:
                self.image_queue.get_nowait()
            except queue.Empty:
                break
        while not self.version_queue.empty():
            try:
                self.version_queue.get_nowait()
            except queue.Empty:
                break

        self.all_mods = []
        self.version_cache = {}
        self.active_cards.clear()
        self.image_cache = {}
        self.active_downloads = set()
        self.active_version_downloads = set()
        self.cache = {}
        self.tags_loaded_flags = {}
        self.current_page = 1
        self.has_more = True
        self.is_loading = False
        self.is_waiting_for_retry = False

        self.clear_layout()

    def set_target_version(self, version_folder):
        self.target_version_folder = version_folder

    def set_installed_items(self, installed_set):
        self.installed_items = set(installed_set or set())
        for card in self.active_cards.values():
            card.set_installed(card.mod_title in self.installed_items)

    def on_search_text_changed(self, text):
        self.cache.pop(self.current_tab, None)
        self.search_timer.start(500)

    def on_sort_changed(self, text):
        self.cache.pop(self.current_tab, None)
        self.reload_data()

    def on_tag_changed(self, text):
        self.cache.pop(self.current_tab, None)
        self.reload_data()

    def get_active_button(self):
        if self.current_tab == "mods":
            return self.btn_mods
        elif self.current_tab == "texturepacks":
            return self.btn_respacks
        return self.btn_maps

    def reload_data(self):
        active_btn = self.get_active_button()
        tag_id = self.tag_combo.currentData()
        self.current_page = 1
        self.has_more = True
        self.switch_tab(active_btn, self.current_tab, self.search_bar.text(),
                        self.sort_combo.currentText(), tag_id)

    def force_refresh_current_tab(self):
        active_btn = self.get_active_button()
        tag_id = self.tag_combo.currentData()
        self.switch_tab(active_btn, self.current_tab, self.search_bar.text(),
                        self.sort_combo.currentText(), tag_id, force_reload=True)

    def switch_tab(self, clicked_btn, tab_name, search_query="",
                   sort_method="Популярные", tag_ids=None, force_reload=False):
        for btn in self.tab_buttons.keys():
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: white;
                    border: none;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.1);
                }
            """)
        clicked_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #3498db;
                border: none;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)

        self.is_initializing = True
        self.is_waiting_for_retry = False
        if self.retry_btn:
            self.retry_btn.deleteLater()
            self.retry_btn = None

        while not self.image_queue.empty():
            try:
                self.image_queue.get_nowait()
            except queue.Empty:
                break

        while not self.version_queue.empty():
            try:
                self.version_queue.get_nowait()
            except queue.Empty:
                break

        self.active_downloads.clear()
        self.active_version_downloads.clear()

        self.current_tab = tab_name

        if not self.tags_loaded_flags.get(tab_name, False):
            self.load_tags(tab_name)
            self.tags_loaded_flags[tab_name] = True

        cache_key = (tab_name, search_query, sort_method,
                     tuple(tag_ids) if isinstance(tag_ids, list) else tag_ids)

        if cache_key in self.cache and not force_reload:
            cached_data = self.cache[cache_key]
            self.all_mods = cached_data['all_mods']
            self.current_page = cached_data['current_page']
            self.has_more = cached_data['has_more']
            self.version_cache = cached_data['version_cache']

            scrollbar = self.mods_scroll.verticalScrollBar()
            scrollbar.blockSignals(True)
            scrollbar.setValue(0)
            scrollbar.blockSignals(False)

            self.apply_filters()
            self.is_initializing = False
            return

        self.all_mods = []
        self.current_page = 1
        self.has_more = True
        self.is_loading = False

        scrollbar = self.mods_scroll.verticalScrollBar()
        scrollbar.blockSignals(True)
        scrollbar.setValue(0)
        scrollbar.blockSignals(False)

        self.clear_layout()
        self.status_label = QLabel("Загрузка данных...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #888; font-size: 14px; padding: 50px;")
        self.mods_layout.addWidget(self.status_label)

        self.worker = APIWorker(tab_name, search_query, sort_method,
                                self.current_page, tag_ids, is_pagination=False)
        self.worker.data_loaded.connect(self.on_data_loaded)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.list_finished.connect(self.on_list_finished)
        self.worker.start()

    def fetch_image(self, url):
        if not self._is_active:
            return
        if url not in self.image_cache and url not in self.active_downloads:
            self.active_downloads.add(url)
            self.image_queue.put(url)

    def on_image_loaded(self, url, data):
        if not self._is_active:
            return
        self.active_downloads.discard(url)
        if data:
            self.image_cache[url] = data
            for card in self.active_cards.values():
                if card.icon_url == url:
                    card.set_image_from_data(data)
        else:
            self.image_cache[url] = b''
            for card in self.active_cards.values():
                if card.icon_url == url:
                    card.set_image_from_data(b'')

    def load_tags(self, tab_name):
        self.tag_combo.blockSignals(True)
        self.tag_combo.clear()
        self.tag_combo.addItem("Все теги", None)
        self.tag_combo.blockSignals(False)
        self.tag_worker = TagWorker(tab_name)
        self.tag_worker.tags_loaded.connect(self.populate_tags)
        self.tag_worker.start()

    def populate_tags(self, tags):
        if not self._is_active:
            return
        self.tag_combo.blockSignals(True)
        for tag in tags:
            if isinstance(tag, dict):
                self.tag_combo.addItem(tag.get('title'), tag.get('id'))
        self.tag_combo.blockSignals(False)

    def check_scroll_bottom(self, value):
        if not self._is_active:
            return
        if self.is_initializing:
            return
        if value >= self.mods_scroll.verticalScrollBar().maximum() - 100:
            if not self.is_loading and self.has_more and not self.is_waiting_for_retry:
                self.load_more_items()

    def load_more_items(self):
        self.is_loading = True
        self.is_waiting_for_retry = False
        self.current_page += 1

        bottom_label = QLabel("Загрузка следующих элементов...")
        bottom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_label.setStyleSheet("color: #999; padding: 15px;")
        self.mods_layout.addWidget(bottom_label)

        tag_id = self.tag_combo.currentData()
        self.worker = APIWorker(self.current_tab, self.search_bar.text(),
                                self.sort_combo.currentText(), self.current_page,
                                tag_id, is_pagination=True)
        self.worker.data_loaded.connect(self.on_more_data_loaded)
        self.worker.error_occurred.connect(self.on_pagination_error)
        self.worker.list_finished.connect(self.on_list_finished)
        self.worker.start()

    def on_more_data_loaded(self, data):
        if not self._is_active:
            return
        last_item = self.mods_layout.takeAt(self.mods_layout.count() - 1)
        if last_item.widget():
            last_item.widget().deleteLater()

        self.is_loading = False
        self.is_waiting_for_retry = False

        if not data or len(data) < 100:
            self.has_more = False

        self.all_mods.extend(data)
        self.apply_filters()
        cache_key = (self.current_tab, self.search_bar.text(),
                     self.sort_combo.currentText(), self.tag_combo.currentData())
        self.cache[cache_key] = {
            'all_mods': self.all_mods,
            'current_page': self.current_page,
            'has_more': self.has_more,
            'version_cache': self.version_cache
        }

        missing_ids = [mod.get('id') for mod in data
                       if mod.get('id') not in self.version_cache
                       and mod.get('id') not in self.active_version_downloads]
        if missing_ids:
            for mid in missing_ids:
                self.active_version_downloads.add(mid)
                self.version_queue.put(mid)

    def on_list_finished(self):
        if not self._is_active:
            return
        if self.mods_layout.count() > 0:
            last_item = self.mods_layout.takeAt(self.mods_layout.count() - 1)
            if last_item.widget():
                last_item.widget().deleteLater()

        self.is_loading = False
        self.is_waiting_for_retry = False
        self.has_more = False

    def on_data_loaded(self, data):
        if not self._is_active:
            return
        self.all_mods = data
        self.apply_filters()
        cache_key = (self.current_tab, self.search_bar.text(),
                     self.sort_combo.currentText(), self.tag_combo.currentData())
        self.cache[cache_key] = {
            'all_mods': self.all_mods,
            'current_page': self.current_page,
            'has_more': self.has_more,
            'version_cache': self.version_cache
        }

        missing_ids = [mod.get('id') for mod in data
                       if mod.get('id') not in self.version_cache
                       and mod.get('id') not in self.active_version_downloads]
        if missing_ids:
            for mid in missing_ids:
                self.active_version_downloads.add(mid)
                self.version_queue.put(mid)

        self.is_initializing = False

    def on_version_fetched(self, mod_id, version):
        if not self._is_active:
            return
        self.active_version_downloads.discard(mod_id)
        self.version_cache[mod_id] = version
        card = self.active_cards.get(mod_id)
        if card:
            card.update_version(version)
        cache_key = (self.current_tab, self.search_bar.text(),
                     self.sort_combo.currentText(), self.tag_combo.currentData())
        if cache_key in self.cache:
            self.cache[cache_key]['version_cache'] = self.version_cache

    def on_error(self, msg):
        if not self._is_active:
            return
        self.is_loading = False
        self.has_more = False
        self.clear_layout()
        error_label = QLabel(msg)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14px; padding: 50px;")
        self.mods_layout.addWidget(error_label)
        self.is_initializing = False

    def on_pagination_error(self, msg):
        if not self._is_active:
            return
        print(f"Ошибка при загрузке следующей страницы: {msg}")
        self.is_loading = False
        self.has_more = True
        self.is_waiting_for_retry = True

        if self.mods_layout.count() > 0:
            last_item = self.mods_layout.takeAt(self.mods_layout.count() - 1)
            if last_item.widget():
                last_item.widget().deleteLater()

        self.show_retry_button(msg)

    def show_retry_button(self, msg):
        if self.retry_btn:
            return

        self.retry_btn = QFrame()
        self.retry_btn.setStyleSheet("""
            QFrame {
                background-color: #fdf0f0;
                border: 1px solid #e74c3c;
                border-radius: 8px;
                margin: 10px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout(self.retry_btn)
        layout.setContentsMargins(10, 10, 10, 10)

        label = QLabel(f"Ошибка загрузки: {msg}")
        label.setStyleSheet("color: #c0392b; font-weight: bold;")
        label.setWordWrap(True)
        layout.addWidget(label, stretch=1)

        retry_button = QPushButton("Повторить")
        retry_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        retry_button.clicked.connect(self.retry_load_more)
        layout.addWidget(retry_button)

        self.mods_layout.addWidget(self.retry_btn)

    def retry_load_more(self):
        if self.retry_btn:
            self.mods_layout.removeWidget(self.retry_btn)
            self.retry_btn.deleteLater()
            self.retry_btn = None

        self.is_waiting_for_retry = False
        self.load_more_items()

    def clear_layout(self):
        self.active_cards.clear()

        if self.retry_btn:
            self.retry_btn.deleteLater()
            self.retry_btn = None

        while self.mods_layout.count():
            item = self.mods_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def apply_filters(self):
        scrollbar = self.mods_scroll.verticalScrollBar()
        current_scroll = scrollbar.value()
        self.clear_layout()

        filtered = []
        for mod in self.all_mods:
            if not isinstance(mod, dict):
                continue
            title = str(mod.get('title', '')).lower()
            search_text = self.search_bar.text().strip().lower()
            if search_text in title:
                filtered.append(mod)

        sort_method = self.sort_combo.currentText()
        if sort_method == "Популярные":
            filtered.sort(key=lambda x: x.get('downloads', 0), reverse=True)
        elif sort_method == "Новые":
            filtered.sort(key=lambda x: str(x.get('last_update_date', '')), reverse=True)
        elif sort_method == "По алфавиту":
            filtered.sort(key=lambda x: str(x.get('title', '')))

        for mod in filtered:
            cached_ver = self.version_cache.get(mod.get('id'))
            card = ModCard(mod, content_type=self.current_tab,
                           cached_version=cached_ver, image_cache=self.image_cache)
            card.image_requested.connect(self.fetch_image)
            card.install_clicked.connect(self._on_card_install)
            self.mods_layout.addWidget(card)
            if mod.get('id'):
                self.active_cards[mod.get('id')] = card
            card.set_installed(card.mod_title in self.installed_items)

        if not filtered:
            empty_label = QLabel("Элементы не найдены")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #888; padding: 30px;")
            self.mods_layout.addWidget(empty_label)

        if self.is_initializing:
            scrollbar.blockSignals(True)
            scrollbar.setValue(0)
            scrollbar.blockSignals(False)
        else:
            scrollbar.setValue(current_scroll)

    def _on_card_install(self, content_id, content_name, version_text, content_type):
        self.install_requested.emit(content_id, content_name, version_text, content_type)