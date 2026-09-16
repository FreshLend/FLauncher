import os
import json
import shutil
import time
import queue
import requests
import zipfile
from pathlib import Path
from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox,
    QLabel, QFrame, QScrollArea, QCheckBox
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


def _normalize_version_str(v):
    if v is None:
        return ""
    s = str(v).strip().lower()
    if s.startswith('v'):
        s = s[1:]
    return s


def _is_valid_version(v):
    if v is None:
        return False
    s = _normalize_version_str(v)
    if not s:
        return False
    if s in ("неизвестно", "загрузка...", "неизвестно"):
        return False
    return True


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
                        resp = requests.get(url, headers=headers, timeout=3)
                        if resp.status_code == 200:
                            self.image_downloaded.emit(url, resp.content)
                        else:
                            self.image_downloaded.emit(url, b'')
                    except Exception:
                        self.image_downloaded.emit(url, b'')
                    time.sleep(0.05)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка в очереди картинок: {e}")
                break


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


class InstalledSidebar(QWidget):
    def __init__(self, settings_manager, theme_manager=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.version_folder = None
        self.setFixedWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.title_label = QLabel("Установлено")
        layout.addWidget(self.title_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)

        self.items_container = QWidget()
        self.items_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(4)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.items_container)

        layout.addWidget(self.scroll, 1)

        self.apply_theme()
        self.refresh()

    def _theme(self):
        if self.theme_manager is None:
            return {}
        return self.theme_manager.current

    def apply_theme(self):
        t = self._theme()
        sidebar_bg = t.get("flmods_sidebar_bg", "#ffffff")
        sidebar_border = t.get("flmods_sidebar_border", "#e0e0e0")
        title_color = t.get("flmods_title_text", "#333333")

        self.setStyleSheet(
            f"background-color: {sidebar_bg}; border-right: 1px solid {sidebar_border};"
        )
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {title_color};
            background: transparent;
            border: none;
        """)
        self.items_container.setStyleSheet("background: transparent;")
        self.refresh()

    def set_version(self, version_folder):
        self.version_folder = version_folder
        self.refresh()

    def refresh(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.version_folder:
            self._show_empty()
            return

        try:
            content_folder = Path(str(self.version_folder)) / "content"
            disabled_folder = content_folder / "disabled"
        except Exception:
            self._show_empty()
            return

        enabled_items = []
        disabled_items = []

        if content_folder.exists():
            try:
                for d in content_folder.iterdir():
                    if d.is_dir() and d.name != "disabled":
                        enabled_items.append(d)
            except Exception:
                pass

        if disabled_folder.exists():
            try:
                for d in disabled_folder.iterdir():
                    if d.is_dir():
                        disabled_items.append(d)
            except Exception:
                pass

        if not enabled_items and not disabled_items:
            self._show_empty()
            return

        enabled_items.sort(key=lambda p: p.name.lower())
        disabled_items.sort(key=lambda p: p.name.lower())

        for folder in enabled_items:
            self.items_layout.addWidget(self._create_item(folder, enabled=True))

        for folder in disabled_items:
            self.items_layout.addWidget(self._create_item(folder, enabled=False))

    def _show_empty(self):
        t = self._theme()
        color = t.get("flmods_meta_text", "#999999")
        empty = QLabel("Ничего не установлено")
        empty.setStyleSheet(f"""
            font-size: 12px;
            color: {color};
            background: transparent;
            border: none;
            padding: 20px 5px;
        """)
        empty.setWordWrap(True)
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items_layout.addWidget(empty)

    def _create_item(self, folder, enabled):
        t = self._theme()
        item_bg = t.get("flmods_sidebar_item_bg", "#f5f5f5")
        title_color = t.get("flmods_title_text", "#333333")
        muted_color = t.get("flmods_meta_text", "#999999")
        accent = t.get("accent", "#2ecc71")
        border_color = t.get("flmods_sidebar_border", "#999999")

        item = QWidget()
        item.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        item.setStyleSheet(f"""
            QWidget {{
                background-color: {item_bg};
                border-radius: 4px;
                border: none;
            }}
        """)
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(6, 6, 6, 6)
        item_layout.setSpacing(6)

        checkbox = QCheckBox()
        checkbox.setChecked(enabled)
        checkbox.setFixedSize(18, 18)
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                background: transparent;
                border: none;
                spacing: 0px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {border_color};
                border-radius: 3px;
                background-color: {t.get('flmods_sidebar_bg', 'white')};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {accent};
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent};
                border: 1px solid {accent};
                image: none;
            }}
        """)
        checkbox.stateChanged.connect(
            lambda state, f=folder, e=enabled: self._on_toggle(f, e, state)
        )
        item_layout.addWidget(checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)

        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet("background-color: transparent; border-radius: 4px; border: none;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_path = folder / "icon.png"
        loaded = False
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                if not enabled:
                    pixmap = self._grayscale(pixmap)
                icon_label.setPixmap(pixmap.scaled(
                    32, 32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                loaded = True
        if not loaded:
            icon_label.setText("?")

        title = folder.name
        pkg_path = folder / "package.json"
        if pkg_path.exists():
            try:
                with open(pkg_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        tt = data.get('title') or data.get('name')
                        if tt:
                            title = str(tt)
            except Exception:
                pass

        title_label = QLabel(title)
        if enabled:
            title_label.setStyleSheet(f"""
                font-size: 12px;
                color: {title_color};
                background: transparent;
                border: none;
            """)
        else:
            title_label.setStyleSheet(f"""
                font-size: 12px;
                color: {muted_color};
                background: transparent;
                border: none;
            """)
        title_label.setWordWrap(True)

        item_layout.addWidget(icon_label)
        item_layout.addWidget(title_label, 1)

        return item

    def _grayscale(self, pixmap):
        image = pixmap.toImage()
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixelColor(x, y)
                if pixel.alpha() == 0:
                    continue
                gray = int(0.299 * pixel.red() + 0.587 * pixel.green() + 0.114 * pixel.blue())
                pixel.setRed(gray)
                pixel.setGreen(gray)
                pixel.setBlue(gray)
                image.setPixelColor(x, y, pixel)
        return QPixmap.fromImage(image)

    def _on_toggle(self, folder, was_enabled, state):
        if not self.version_folder:
            return

        now_enabled = (state == Qt.CheckState.Checked.value)
        if now_enabled == was_enabled:
            return

        try:
            content_folder = Path(str(self.version_folder)) / "content"
            disabled_folder = content_folder / "disabled"
            disabled_folder.mkdir(parents=True, exist_ok=True)

            name = folder.name
            if now_enabled:
                src = disabled_folder / name
                dst = content_folder / name
            else:
                src = content_folder / name
                dst = disabled_folder / name

            if src.exists():
                if dst.exists():
                    try:
                        if dst.is_dir():
                            shutil.rmtree(dst)
                        else:
                            dst.unlink()
                    except Exception:
                        pass
                shutil.move(str(src), str(dst))
        except Exception as e:
            print(f"Ошибка переключения мода: {e}")

        self.refresh()

    def get_enabled_names(self):
        result = set()
        if not self.version_folder:
            return result
        try:
            content_folder = Path(str(self.version_folder)) / "content"
            if content_folder.exists():
                for d in content_folder.iterdir():
                    if d.is_dir() and d.name != "disabled":
                        result.add(d.name)
        except Exception:
            pass
        return result


class ModCard(QFrame):
    image_requested = pyqtSignal(str)
    install_clicked = pyqtSignal(int, str, str, str)

    def __init__(self, mod_data, content_type="mods", cached_version=None,
                 image_cache=None, theme_manager=None, parent=None):
        super().__init__(parent)
        if not isinstance(mod_data, dict):
            mod_data = {}
        self.mod_id = mod_data.get("id")
        self.mod_title = mod_data.get("title", "Unknown Mod")
        self.content_type = content_type
        self.icon_url = mod_data.get("logo_url") or mod_data.get("icon")
        self.image_cache = image_cache if image_cache else {}
        self.theme_manager = theme_manager

        self.setFrameShape(QFrame.Shape.StyledPanel)

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
        self.title_label = QLabel(self.mod_title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(self.title_label)

        self.author_label = QLabel(f"Автор: {author_name}")
        info_layout.addWidget(self.author_label)

        self.desc_label = QLabel(str(mod_data.get("description", ""))[:300] + "...")
        self.desc_label.setWordWrap(True)
        info_layout.addWidget(self.desc_label)

        downloads = mod_data.get('downloads', 0)
        raw_date = mod_data.get("last_update_date", "")
        updated = format_relative_time(raw_date)
        self.version_text = "Версия: Загрузка..."
        if cached_version:
            self.version_text = f"Версия: {cached_version}"

        self.meta_label = QLabel(f"Загрузок: {downloads} | Обновлено: {updated}")
        self.version_label = QLabel(self.version_text)
        info_layout.addWidget(self.meta_label)
        info_layout.addWidget(self.version_label)
        layout.addLayout(info_layout, stretch=1)

        self.action_btn = QPushButton("Установить")
        self.action_btn.setFixedSize(120, 35)
        self.action_btn.clicked.connect(self._on_install)
        layout.addWidget(self.action_btn)

        self._current_state = "install"
        self.apply_theme()

    def _theme(self):
        if self.theme_manager is None:
            return {}
        return self.theme_manager.current

    def apply_theme(self):
        t = self._theme()
        card_bg = t.get("flmods_card_bg", "#f5f5f5")
        card_border = t.get("flmods_card_border", "#dcdcdc")
        hover_border = t.get("accent", "#3498db")
        title_color = t.get("flmods_title_text", "#222222")
        body_color = t.get("flmods_body_text", "#555555")
        meta_color = t.get("flmods_meta_text", "#999999")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
                margin: 4px;
            }}
            QFrame:hover {{
                border: 1px solid {hover_border};
            }}
        """)

        self.title_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {title_color};
            background: transparent;
            border: none;
        """)
        self.author_label.setStyleSheet(f"color: {body_color}; background: transparent; border: none;")
        self.desc_label.setStyleSheet(f"color: {body_color}; background: transparent; border: none;")
        self.meta_label.setStyleSheet(f"color: {meta_color}; font-size: 10px; background: transparent; border: none;")
        self.version_label.setStyleSheet(f"color: {meta_color}; font-size: 10px; background: transparent; border: none;")

        self._reapply_button_style()

    def _reapply_button_style(self):
        if self._current_state == "install":
            self._apply_install_style()
        elif self._current_state == "reinstall":
            self._apply_reinstall_style()
        elif self._current_state == "update":
            self._apply_update_style()

    def _apply_install_style(self):
        t = self._theme()
        bg = t.get("install_bg", "#2ecc71")
        hover = t.get("install_hover", "#27ae60")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
            }}
        """)

    def _apply_reinstall_style(self):
        t = self._theme()
        bg = t.get("reinstall_bg", "#f39c12")
        hover = t.get("reinstall_hover", "#e67e22")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
            }}
        """)

    def _apply_update_style(self):
        t = self._theme()
        bg = t.get("update_bg", "#3498db")
        hover = t.get("update_hover", "#2980b9")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
            }}
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
        self.version_text = f"Версия: {version}"
        self.version_label.setText(self.version_text)

    def set_installed(self, installed, latest_version=None, installed_version=None):
        if not installed:
            self.action_btn.setText("Установить")
            self._current_state = "install"
            self._apply_install_style()
            return

        has_update = False
        if _is_valid_version(latest_version) and _is_valid_version(installed_version):
            if _normalize_version_str(latest_version) != _normalize_version_str(installed_version):
                has_update = True

        if has_update:
            self.action_btn.setText("Обновить")
            self._current_state = "update"
            self._apply_update_style()
        else:
            self.action_btn.setText("Переустановить")
            self._current_state = "reinstall"
            self._apply_reinstall_style()

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

            disabled_folder = core_version_folder / "content" / "disabled" / self.content_name
            if disabled_folder.exists():
                try:
                    shutil.rmtree(disabled_folder)
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

    def __init__(self, settings_manager, thread_manager, theme_manager=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.thread_manager = thread_manager
        self.theme_manager = theme_manager
        self.target_version_folder = None
        self.installed_items = set()
        self.installed_versions = {}
        self._is_active = False
        self._old_workers = []

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

        self.top_bar = QWidget()
        self.top_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(15, 10, 15, 10)

        self.btn_mods = QPushButton("Моды")
        self.btn_respacks = QPushButton("Ресурс-паки")
        self.btn_maps = QPushButton("Карты")
        self.tab_buttons = {self.btn_mods: "mods",
                            self.btn_respacks: "texturepacks",
                            self.btn_maps: "worlds"}

        for btn, tab in self.tab_buttons.items():
            btn.clicked.connect(lambda checked, b=btn, t=tab: self.switch_tab(b, t))
            top_layout.addWidget(btn)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск по названию...")
        self.search_bar.setFixedWidth(250)
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        top_layout.addWidget(self.search_bar)

        self.tag_combo = QComboBox()
        self.tag_combo.setMinimumWidth(150)
        self.tag_combo.addItem("Все теги", None)
        self.tag_combo.currentTextChanged.connect(self.on_tag_changed)
        top_layout.addWidget(self.tag_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Популярные", "Новые", "По алфавиту"])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        top_layout.addWidget(self.sort_combo)

        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.clicked.connect(self.force_refresh_current_tab)
        top_layout.addWidget(self.btn_refresh)

        main_layout.addWidget(self.top_bar)

        body = QWidget()
        body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.body = body
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.installed_sidebar = InstalledSidebar(settings_manager, theme_manager=theme_manager)
        body_layout.addWidget(self.installed_sidebar)

        self.mods_scroll = QScrollArea()
        self.mods_scroll.setWidgetResizable(True)
        self.mods_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.mods_content = QWidget()
        self.mods_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.mods_layout = QVBoxLayout(self.mods_content)
        self.mods_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.mods_scroll.setWidget(self.mods_content)
        self.mods_scroll.verticalScrollBar().valueChanged.connect(self.check_scroll_bottom)
        body_layout.addWidget(self.mods_scroll, 1)

        main_layout.addWidget(body, 1)

        self.apply_theme()

    def _cleanup_old_workers(self):
        alive = []
        for w in self._old_workers:
            try:
                if not w.isFinished():
                    alive.append(w)
            except RuntimeError:
                pass
        self._old_workers = alive

    def _theme(self):
        if self.theme_manager is None:
            return {}
        return self.theme_manager.current

    def apply_theme(self):
        t = self._theme()

        accent = t.get("accent", "#3498db")
        topbar_bg = t.get("flmods_topbar_bg", "#3498db")
        topbar_text = t.get("flmods_topbar_text", "white")
        tab_active_bg = t.get("flmods_tab_active_bg", "white")
        tab_active_text = t.get("flmods_tab_active_text", accent)

        input_bg = t.get("input_field_bg", "white")
        input_text = t.get("input_field_text", "black")
        input_border = t.get("input_field_border", "#ccc")

        bg = t.get("flmods_bg", t.get("settings_bg", "white"))
        scrollbar_bg = t.get("flmods_sidebar_item_bg", "#f0f0f0")

        self.top_bar.setStyleSheet(f"background-color: {topbar_bg};")
        self.body.setStyleSheet(f"background-color: {bg};")

        self.mods_content.setStyleSheet(f"background-color: {bg};")
        self.mods_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {bg}; }}
            QScrollArea > QWidget > QWidget {{ background-color: {bg}; }}
            QScrollBar:vertical {{
                border: none;
                background: {scrollbar_bg};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #C0C0C0;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #A0A0A0;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        for btn in self.tab_buttons.keys():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {topbar_text};
                    border: none;
                    padding: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgba(255,255,255,0.1);
                    border-radius: 4px;
                }}
            """)

        active = self.get_active_button()
        active.setStyleSheet(f"""
            QPushButton {{
                background-color: {tab_active_bg};
                color: {tab_active_text};
                border: none;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)

        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {input_border};
                border-radius: 4px;
                padding: 5px;
                background-color: {input_bg};
                color: {input_text};
            }}
        """)

        combo_qss = f"""
            QComboBox {{
                border: 1px solid {input_border};
                border-radius: 4px;
                padding: 4px;
                background-color: {input_bg};
                color: {input_text};
            }}
            QComboBox QAbstractItemView {{
                background-color: {input_bg};
                color: {input_text};
                selection-background-color: {accent};
                selection-color: white;
                outline: none;
            }}
        """
        self.tag_combo.setStyleSheet(combo_qss)
        self.sort_combo.setStyleSheet(combo_qss)

        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {tab_active_bg};
                color: {tab_active_text};
                font-weight: bold;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {input_bg};
            }}
        """)

        if self.installed_sidebar:
            self.installed_sidebar.apply_theme()

        for card in self.active_cards.values():
            card.apply_theme()

    def start(self):
        if self._is_active:
            return
        self._is_active = True

        self._cleanup_old_workers()

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

        self.apply_theme()
        self.installed_sidebar.refresh()
        self._reload_installed_versions()
        self.reload_data()

    def stop(self):
        if not self._is_active:
            return
        self._is_active = False

        for w in self.image_workers:
            try:
                w.image_downloaded.disconnect()
            except Exception:
                pass
            w.running = False
            self._old_workers.append(w)

        for w in self.version_workers:
            try:
                w.version_fetched.disconnect()
            except Exception:
                pass
            w.running = False
            self._old_workers.append(w)

        if hasattr(self, 'tag_worker') and self.tag_worker is not None:
            try:
                self.tag_worker.tags_loaded.disconnect()
            except Exception:
                pass
            self.tag_worker.cancelled = True
            self._old_workers.append(self.tag_worker)
            self.tag_worker = None

        if hasattr(self, 'worker') and self.worker is not None:
            try:
                self.worker.data_loaded.disconnect()
                self.worker.error_occurred.disconnect()
                self.worker.list_finished.disconnect()
            except Exception:
                pass
            self.worker.cancelled = True
            self._old_workers.append(self.worker)
            self.worker = None

        for _ in range(len(self.image_workers) + 2):
            try:
                self.image_queue.put_nowait(None)
            except Exception:
                pass

        for _ in range(len(self.version_workers) + 2):
            try:
                self.version_queue.put_nowait(None)
            except Exception:
                pass

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

    def set_target_version(self, version_name):
        self.target_version_folder = version_name
        if version_name:
            try:
                folder_path = Path(str(self.settings_manager.app_data_path)) / version_name
                self.installed_sidebar.set_version(folder_path)
            except Exception:
                self.installed_sidebar.set_version(None)
        else:
            self.installed_sidebar.set_version(None)
        self._reload_installed_versions()
        self._refresh_cards_state()

    def _reload_installed_versions(self):
        self.installed_versions = {}
        if not self.target_version_folder:
            return
        try:
            folder = Path(str(self.settings_manager.app_data_path)) / self.target_version_folder
            content = folder / "content"
            disabled = content / "disabled"
        except Exception:
            return

        for base in (content, disabled):
            if not base.exists():
                continue
            try:
                for d in base.iterdir():
                    if d.is_dir() and d.name != "disabled":
                        v = self._read_pkg_version(d)
                        if v:
                            self.installed_versions[d.name] = v
            except Exception:
                pass

    def _read_pkg_version(self, folder):
        pkg = folder / "package.json"
        if not pkg.exists():
            return None
        try:
            with open(pkg, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                v = data.get('version')
                if v is not None:
                    return str(v)
        except Exception:
            pass
        return None

    def set_installed_items(self, installed_set):
        self.installed_items = set(installed_set or set())
        self._reload_installed_versions()
        self._refresh_cards_state()
        self.installed_sidebar.refresh()

    def _refresh_cards_state(self):
        for card in self.active_cards.values():
            is_installed = card.mod_title in self.installed_items
            latest = self.version_cache.get(card.mod_id)
            installed_ver = self.installed_versions.get(card.mod_title)
            card.set_installed(is_installed, latest, installed_ver)

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
            is_installed = card.mod_title in self.installed_items
            installed_ver = self.installed_versions.get(card.mod_title)
            card.set_installed(is_installed, version, installed_ver)
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
                           cached_version=cached_ver, image_cache=self.image_cache,
                           theme_manager=self.theme_manager)
            card.image_requested.connect(self.fetch_image)
            card.install_clicked.connect(self._on_card_install)
            self.mods_layout.addWidget(card)
            if mod.get('id'):
                self.active_cards[mod.get('id')] = card

            is_installed = card.mod_title in self.installed_items
            installed_ver = self.installed_versions.get(card.mod_title)
            card.set_installed(is_installed, cached_ver, installed_ver)

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