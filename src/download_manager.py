import os
import time
import zipfile
import shutil
import subprocess
import requests
import sys
import platform
from pathlib import Path
from utils import get_platform_asset_pattern, get_executable_pattern, MAIN_REPO

class DownloadManager:
    def __init__(self, version_manager):
        self.version_manager = version_manager
        self.download_start_time = 0
        self.asset_pattern = get_platform_asset_pattern()
        self.executable_pattern = get_executable_pattern()
        self.system = sys.platform
    
    def download_version(self, version_tag, progress_callback=None, is_cancelled_callback=None):
        if hasattr(self.version_manager, 'artifact_data') and \
           version_tag in self.version_manager.artifact_data:
            artifact_info = self.version_manager.artifact_data[version_tag]
            repo = artifact_info.get('repo', MAIN_REPO)
            return self._download_artifact(
                version_tag, 
                artifact_info,
                repo,
                progress_callback,
                is_cancelled_callback
            )
        else:
            repo = self._get_repo_for_version(version_tag)
            return self._download_release(
                version_tag, 
                repo,
                progress_callback, 
                is_cancelled_callback
            )
    
    def _get_repo_for_version(self, version_tag):
        if '_' in version_tag and not version_tag.startswith('MSVC') and not version_tag.startswith('CLang'):
            author = version_tag.split('_')[0]
            for repo in self.version_manager.settings_manager.settings.get("github_repos", []):
                if repo.startswith(author + '/'):
                    return repo
        return MAIN_REPO
    
    def _get_clean_version_tag(self, version_tag):
        if '_' in version_tag and not version_tag.startswith('MSVC') and not version_tag.startswith('CLang'):
            return version_tag.split('_', 1)[-1]
        return version_tag
    
    def _download_release(self, version_tag, repo, progress_callback=None, is_cancelled_callback=None):
        try:
            clean_tag = self._get_clean_version_tag(version_tag)
            
            api_url = f"https://api.github.com/repos/{repo}/releases/tags/{clean_tag}"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                return False, f"Не удалось получить информацию о релизе из {repo}. Код: {response.status_code}"
            
            release_data = response.json()
            
            file_url = None
            asset_name = None
            asset_size = 0
            for asset in release_data.get('assets', []):
                if self.asset_pattern in asset['name']:
                    file_url = asset['browser_download_url']
                    asset_name = asset['name']
                    asset_size = asset.get('size', 0)
                    break
            
            if not file_url:
                return False, f"Не найден файл для вашей платформы в релизе {version_tag} из {repo}"
            
            downloads_path = self.version_manager.app_data_path.parent / "downloads"
            downloads_path.mkdir(parents=True, exist_ok=True)
            
            required_space = asset_size * 2
            free_space = shutil.disk_usage(downloads_path).free
            
            if free_space < required_space and asset_size > 0:
                required_mb = required_space / (1024 * 1024)
                free_mb = free_space / (1024 * 1024)
                return False, f"Недостаточно свободного места. Требуется: {required_mb:.0f} MB, Доступно: {free_mb:.0f} MB"
            
            zip_path = downloads_path / asset_name
            
            if progress_callback:
                progress_callback(0, f"Подготовка к загрузке из {repo}...")
            
            success = self._download_file(file_url, zip_path, asset_size, progress_callback, is_cancelled_callback)
            if not success:
                if zip_path.exists():
                    zip_path.unlink()
                return False, "Загрузка была отменена или произошла ошибка"
            
            if is_cancelled_callback and is_cancelled_callback():
                return False, "Загрузка отменена"
            
            if progress_callback:
                progress_callback(0, "Распаковка архива...")
            
            try:
                self._extract_archive(zip_path, version_tag, is_cancelled_callback)
            except Exception as e:
                extraction_path = self.version_manager.app_data_path / version_tag
                if extraction_path.exists():
                    shutil.rmtree(extraction_path)
                raise e
            
            if is_cancelled_callback and is_cancelled_callback():
                extraction_path = self.version_manager.app_data_path / version_tag
                if extraction_path.exists():
                    shutil.rmtree(extraction_path)
                return False, "Установка была отменена"
            
            return True, f"Версия {version_tag} успешно скачана и установлена!"
            
        except Exception as e:
            return False, f"Ошибка при скачивании или распаковке: {e}"
    
    def _download_artifact(self, version_tag, artifact_data, repo, progress_callback=None, is_cancelled_callback=None):
        try:
            download_url = artifact_data['download_url']
            
            headers = self.version_manager.github_client._get_headers()
            
            response = requests.get(download_url, headers=headers, stream=True)
            if response.status_code != 200:
                return False, f"Не удалось скачать артефакт из {repo}. Код: {response.status_code}"
            
            content_disposition = response.headers.get('content-disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                filename = f"{version_tag.replace(' ', '_').replace('/', '_')}.zip"
            
            downloads_path = self.version_manager.app_data_path.parent / "downloads"
            downloads_path.mkdir(parents=True, exist_ok=True)
            file_path = downloads_path / filename
            
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0
            chunk_size = 1024 * 64
            
            with open(file_path, 'wb') as f:
                for data in response.iter_content(chunk_size=chunk_size):
                    if is_cancelled_callback and is_cancelled_callback():
                        return False, "Загрузка отменена"
                    
                    if data:
                        downloaded_size += len(data)
                        f.write(data)
                        
                        if progress_callback and total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            progress_callback(progress, f"Скачивание артефакта из {repo}... {progress}%")
            
            version_folder = self.version_manager.app_data_path / version_tag
            version_folder.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(version_folder)
            
            file_path.unlink()
            
            self.version_manager.create_config_json(version_folder)
            
            return True, f"Артефакт {version_tag} успешно установлен!"
            
        except Exception as e:
            return False, f"Ошибка при скачивании артефакта из {repo}: {e}"
    
    def _download_file(self, file_url, file_path, expected_size, progress_callback=None, is_cancelled_callback=None):
        try:
            response = requests.get(file_url, stream=True, timeout=30)
            
            if response.status_code != 200:
                return False
            
            total_size = int(response.headers.get('Content-Length', 0))
            if total_size == 0 and expected_size > 0:
                total_size = expected_size
            
            downloaded_size = 0
            chunk_size = 1024 * 64
            self.download_start_time = time.time()
            
            if file_path.exists():
                file_path.unlink()
            
            with open(file_path, 'wb') as f:
                for data in response.iter_content(chunk_size=chunk_size):
                    if is_cancelled_callback and is_cancelled_callback():
                        return False
                    
                    if data:
                        downloaded_size += len(data)
                        f.write(data)
                        
                        if progress_callback and total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            elapsed_time = time.time() - self.download_start_time
                            speed = (downloaded_size / 1024) / elapsed_time if elapsed_time > 0 else 0
                            
                            if speed > 0:
                                remaining_size = total_size - downloaded_size
                                remaining_time = remaining_size / (speed * 1024)
                                remaining_time_str = time.strftime("%H:%M:%S", time.gmtime(remaining_time))
                            else:
                                remaining_time_str = "расчет..."
                            
                            downloaded_size_mb = downloaded_size / (1024 * 1024)
                            total_size_mb = total_size / (1024 * 1024)
                            
                            progress_callback(
                                progress,
                                f"{downloaded_size_mb:.1f} MB / {total_size_mb:.1f} MB, "
                                f"Скорость: {speed:.1f} KB/s, Осталось: {remaining_time_str}"
                            )
            
            if total_size > 0 and downloaded_size != total_size:
                return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            return False
        except Exception as e:
            return False
    
    def _extract_archive(self, archive_path, version_tag, is_cancelled_callback=None):
        extraction_path = self.version_manager.app_data_path / version_tag
        extraction_path.mkdir(parents=True, exist_ok=True)
        
        file_ext = archive_path.suffix.lower()
        
        if file_ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                bad_file = zip_ref.testzip()
                if bad_file:
                    raise Exception(f"Поврежденный файл в архиве: {bad_file}")
                
                zip_ref.extractall(extraction_path)
            
            items = list(extraction_path.iterdir())
            
            if len(items) == 1 and items[0].is_dir():
                folder_path = items[0]
                for item in folder_path.iterdir():
                    dest = extraction_path / item.name
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    shutil.move(str(item), extraction_path)
                shutil.rmtree(folder_path)
                
        elif file_ext == '.dmg' and platform.system() == 'Darwin':
            try:
                mount_output = subprocess.check_output(
                    ['hdiutil', 'attach', '-nobrowse', '-readonly', str(archive_path)],
                    universal_newlines=True
                )
                
                mount_path = None
                for line in mount_output.split('\n'):
                    if '/Volumes/' in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('/Volumes/'):
                                mount_path = part
                                break
                
                if mount_path:
                    for item in Path(mount_path).iterdir():
                        if item.name not in ['.DS_Store', '.Trashes']:
                            dest = extraction_path / item.name
                            if item.is_dir():
                                shutil.copytree(item, dest, dirs_exist_ok=True)
                            else:
                                shutil.copy2(item, dest)
                    
                    subprocess.run(['hdiutil', 'detach', mount_path], check=False)
                
            except subprocess.CalledProcessError as e:
                raise Exception(f"Ошибка при монтировании DMG: {e}")
            except Exception as e:
                raise Exception(f"Ошибка при распаковке DMG: {e}")
        else:
            dest_path = extraction_path / archive_path.name
            shutil.copy2(archive_path, dest_path)
            if file_ext == '.appimage':
                dest_path.chmod(0o755)
        
        if archive_path.exists() and not (is_cancelled_callback and is_cancelled_callback()):
            archive_path.unlink()
        
        if not (is_cancelled_callback and is_cancelled_callback()):
            self.version_manager.create_config_json(extraction_path)
    
    def launch_game(self, voxel_core_path, working_directory, additional_args=""):
        launch_params = [str(voxel_core_path)]
        
        if additional_args:
            launch_params.extend(additional_args.split())
        
        creation_flags = 0
        if self.system == 'win32':
            creation_flags = subprocess.CREATE_NEW_CONSOLE
        
        subprocess.Popen(
            launch_params,
            cwd=str(working_directory),
            creationflags=creation_flags
        )
    
    def find_executable(self, version_folder):
        if self.system == 'win32':
            exe_files = [
                f for f in version_folder.iterdir() 
                if f.is_file() and f.suffix.lower() == ".exe" and f.stem.lower() != "vctest"
            ]
            return exe_files[0] if exe_files else None
            
        elif self.system == 'darwin':
            app_files = [
                f for f in version_folder.iterdir()
                if f.is_file() and (f.suffix.lower() == '.dmg' or f.suffix.lower() == '.app')
            ]
            return app_files[0] if app_files else None
            
        else:
            appimage_files = [
                f for f in version_folder.iterdir()
                if f.is_file() and f.suffix.lower() == '.appimage'
            ]
            return appimage_files[0] if appimage_files else None