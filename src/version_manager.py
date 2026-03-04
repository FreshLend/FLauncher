import re
import json
import requests
from pathlib import Path

from utils import MAX_LOAD, MAIN_REPO, get_platform_asset_pattern


class VersionManager:
    def __init__(self, settings_manager):
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
            
            releases = response.json()
            valid_versions = []
            
            for release in releases:
                if not isinstance(release, dict) or 'tag_name' not in release:
                    continue
                
                assets = release.get('assets', [])
                has_platform_asset = False
                
                for asset in assets:
                    asset_name = asset.get('name', '')
                    if self.asset_pattern in asset_name:
                        has_platform_asset = True
                        break
                
                if has_platform_asset:
                    valid_versions.append((release['tag_name'], repo))
            
            return valid_versions
            
        except Exception as e:
            print(f"Ошибка получения версий из {repo}: {e}")
            return []
    
    def get_all_online_versions(self):
        all_versions = []
        
        main_versions = self.get_github_repo_versions(MAIN_REPO)
        all_versions.extend([v[0] for v in main_versions])
        
        for repo in self.settings_manager.settings.get("github_repos", []):
            try:
                repo_versions = self.get_github_repo_versions(repo)
                all_versions.extend([v[0] for v in repo_versions])
            except Exception as e:
                print(f"Ошибка загрузки {repo}: {e}")
        
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
        return tuple(map(int, version_parts))
    
    def find_repo_for_version(self, version_tag):
        if self._is_version_in_repo(version_tag, MAIN_REPO):
            return MAIN_REPO
        
        for repo in self.settings_manager.settings.get("github_repos", []):
            if self._is_version_in_repo(version_tag, repo):
                return repo
        
        return None
    
    def _is_version_in_repo(self, version_tag, repo):
        try:
            versions = self.get_github_repo_versions(repo)
            return any(v[0] == version_tag for v in versions)
        except Exception as e:
            print(f"Ошибка при проверке версии в репозитории {repo}: {e}")
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
        except Exception as e:
            print(f"Ошибка при чтении файла config.json: {e}")
        
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
            print(f"Ошибка при обновлении файла config.json: {e}")
    
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
            print(f"Не удалось создать config.json: {e}")