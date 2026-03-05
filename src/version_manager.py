import re
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal

from utils import MAX_LOAD, MAIN_REPO, get_platform_asset_pattern


class VersionManager(QObject):
    error_occurred = pyqtSignal(str)
    versions_loaded = pyqtSignal()
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.app_data_path = settings_manager.app_data_path
        self.asset_pattern = get_platform_asset_pattern()
    
    def get_github_repo_versions(self, repo):
        try:
            response = requests.get(
                f"https://api.github.com/repos/{repo}/releases?per_page={MAX_LOAD}",
                timeout=5,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            
            if response.status_code != 200:
                error_msg = f"Репозиторий {repo} вернул код {response.status_code}"
                self.error_occurred.emit(error_msg)
                return []
            
            releases = response.json()
            if not isinstance(releases, list):
                self.error_occurred.emit(f"Неверный формат ответа от {repo}")
                return []
            
            valid_versions = []
            for release in releases:
                if not isinstance(release, dict) or 'tag_name' not in release:
                    continue
                
                assets = release.get('assets', [])
                has_platform_asset = any(
                    self.asset_pattern in asset.get('name', '') 
                    for asset in assets
                )
                
                if has_platform_asset:
                    valid_versions.append((release['tag_name'], repo))
            
            return valid_versions
            
        except requests.exceptions.Timeout:
            self.error_occurred.emit(f"Таймаут при подключении к {repo}")
            return []
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit(f"Ошибка подключения к {repo}. Проверьте интернет.")
            return []
        except Exception as e:
            self.error_occurred.emit(f"Ошибка получения версий из {repo}: {str(e)}")
            return []
    
    def get_all_online_versions(self):
        all_versions = []
        repos_to_check = [MAIN_REPO] + self.settings_manager.settings.get("github_repos", [])
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Запускаем все задачи
            future_to_repo = {
                executor.submit(self.get_github_repo_versions, repo): repo 
                for repo in repos_to_check
            }
            
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    repo_versions = future.result(timeout=10)
                    all_versions.extend([v[0] for v in repo_versions])
                except Exception as e:
                    self.error_occurred.emit(f"Не удалось обработать {repo}: {str(e)}")
        
        self.versions_loaded.emit()
        return all_versions
    
    def get_user_versions(self):
        user_versions = []
        if self.app_data_path.exists():
            for folder in self.app_data_path.iterdir():
                if folder.is_dir():
                    version_tuple = self._version_to_tuple(folder.name)
                    user_versions.append((folder.name, version_tuple))
        
        user_versions.sort(key=lambda x: x[1], reverse=True)
        return [version[0] for version in user_versions]
    
    def _version_to_tuple(self, version_str):
        version_parts = re.findall(r'\d+', version_str)
        return tuple(map(int, version_parts)) if version_parts else (0,)
    
    def find_repo_for_version(self, version_tag):
        if self._is_version_in_repo(version_tag, MAIN_REPO):
            return MAIN_REPO
        
        for repo in self.settings_manager.settings.get("github_repos", []):
            if self._is_version_in_repo(version_tag, repo):
                return repo
        
        return None
    
    def _is_version_in_repo(self, version_tag, repo):
        try:
            response = requests.get(
                f"https://api.github.com/repos/{repo}/releases/tags/{version_tag}",
                timeout=3
            )
            return response.status_code == 200
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при проверке {version_tag} в {repo}: {str(e)}")
            return False
    
    def get_username_from_config(self, version):
        config_file_path = self.app_data_path / version / "config" / "quartz" / "config.json"
        if not config_file_path.exists():
            return None
        
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "Account" in config and "name" in config["Account"]:
                    return config["Account"]["name"]
        except json.JSONDecodeError:
            self.error_occurred.emit(f"Ошибка чтения JSON в {config_file_path}")
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при чтении config.json: {e}")
        
        return None
    
    def update_username_in_config(self, username, version):
        if version == "Получение версий...":
            return
        
        config_file_path = self.app_data_path / version / "config" / "quartz" / "config.json"
        if not config_file_path.exists():
            return
        
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if "Account" in config:
                config["Account"]["name"] = username
            
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при обновлении config.json: {e}")
    
    def create_config_json(self, extraction_path):
        try:
            config_path = extraction_path / 'config' / 'quartz' / 'config.json'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_content = {
                "Account": {
                    "friends": {},
                    "name": "FLauncher_Player"
                },
                "Servers": {}
            }
            if not config_path.exists():
                with open(config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(config_content, config_file, indent=4)
        except Exception as e:
            self.error_occurred.emit(f"Не удалось создать config.json: {e}")