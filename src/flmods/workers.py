import os
import shutil
import time
import queue
import zipfile
import logging
from pathlib import Path

import requests
from PyQt6.QtCore import QThread, pyqtSignal
from utils import safe_extract_zip
from flmods.api import VoxelWorldAPI

log = logging.getLogger("flauncher.flmods.workers")


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
                log.error("Ошибка в очереди картинок: %s", e)
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
                log.error("Ошибка в очереди версий: %s", e)
                break


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
                safe_extract_zip(zip_path, install_folder)
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
            log.exception("Ошибка установки %s", self.content_name)
            self.install_finished.emit(False, str(e), self.content_name, self.core_version)