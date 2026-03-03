import os
import time
import zipfile
import shutil
import subprocess
import requests
from pathlib import Path


class DownloadManager:
    def __init__(self, version_manager):
        self.version_manager = version_manager
        self.download_start_time = 0
    
    def download_and_extract_version(self, version_tag, progress_callback=None):
        self.download_start_time = time.time()
        
        repo = self.version_manager.find_repo_for_version(version_tag)
        if not repo:
            return False, f"Не удалось определить репозиторий для версии {version_tag}"
        
        api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version_tag}"
        
        try:
            response = requests.get(api_url)
            if response.status_code != 200:
                return False, f"Не удалось получить информацию о релизе. Код: {response.status_code}"
            
            release_data = response.json()
            
            file_url = None
            for asset in release_data.get('assets', []):
                if 'win64.zip' in asset['name']:
                    file_url = asset['browser_download_url']
                    break
            
            if not file_url:
                return False, f"Не найден файл с win64.zip в релизе {version_tag}"
            
            downloads_path = self.version_manager.app_data_path.parent / "downloads"
            downloads_path.mkdir(parents=True, exist_ok=True)
            
            zip_path = downloads_path / f"{release_data['tag_name']}_win64.zip"
            
            if progress_callback:
                progress_callback(0, "Подготовка к загрузке...")
            
            success = self._download_file(file_url, zip_path, progress_callback)
            if not success:
                return False, "Ошибка при скачивании файла"
            
            if progress_callback:
                progress_callback(0, "Распаковка архива...")
            
            self._extract_zip(zip_path, version_tag)
            
            return True, f"Версия {version_tag} успешно скачана и установлена!"
            
        except Exception as e:
            return False, f"Ошибка при скачивании или распаковке: {e}"
    
    def _download_file(self, file_url, zip_path, progress_callback=None):
        try:
            response = requests.get(file_url, stream=True)
            
            if response.status_code != 200:
                return False
            
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0
            chunk_size = 1024 * 8
            
            if zip_path.exists():
                zip_path.unlink()
            
            with open(zip_path, 'wb') as f:
                for data in response.iter_content(chunk_size=chunk_size):
                    if data:
                        downloaded_size += len(data)
                        f.write(data)
                        
                        if progress_callback and total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            elapsed_time = time.time() - self.download_start_time
                            speed = (downloaded_size / 1024) / elapsed_time if elapsed_time > 0 else 0
                            remaining_size = total_size - downloaded_size
                            remaining_time = remaining_size / (speed * 1024) if speed > 0 else 0
                            remaining_time_str = time.strftime("%H:%M:%S", time.gmtime(remaining_time))
                            downloaded_size_mb = downloaded_size / (1024 * 1024)
                            total_size_mb = total_size / (1024 * 1024)
                            
                            progress_callback(
                                progress,
                                f"{downloaded_size_mb:.2f} MB / {total_size_mb:.2f} MB, "
                                f"Скорость: {speed:.2f} KB/s, Осталось: {remaining_time_str}"
                            )
            
            return True
            
        except Exception as e:
            print(f"Ошибка при скачивании: {e}")
            return False
    
    def _extract_zip(self, zip_path, version_tag):
        try:
            extraction_path = self.version_manager.app_data_path / version_tag
            extraction_path.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extraction_path)
                zip_files = zip_ref.namelist()
                if zip_files:
                    first_file = zip_files[0]
                    if '/' in first_file:
                        folder_in_zip = first_file.split('/')[0]
                        folder_to_move = extraction_path / folder_in_zip
                        if folder_to_move.exists():
                            for item in folder_to_move.iterdir():
                                shutil.move(str(item), extraction_path / item.name)
                            folder_to_move.rmdir()
            
            if zip_path.exists():
                zip_path.unlink()
            
            self.version_manager.create_config_json(extraction_path)
            
        except Exception as e:
            raise Exception(f"Ошибка при распаковке архива: {e}")
    
    def launch_game(self, voxel_core_path, working_directory, additional_args=""):
        launch_params = [str(voxel_core_path)]
        
        if additional_args:
            launch_params.extend(additional_args.split())
        
        subprocess.Popen(
            launch_params,
            cwd=str(working_directory),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )