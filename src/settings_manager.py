import os
import json
from pathlib import Path


class SettingsManager:
    def __init__(self):
        self.app_data_path = self._get_app_data_path()
        self.settings_path = self._get_settings_path()
        self.downloads_path = self.app_data_path.parent / "downloads"
        
        self._create_directories()
        self.settings = self._load_settings()
    
    def _get_app_data_path(self):
        user_folder = Path(os.path.expanduser("~"))
        return user_folder / "AppData" / "Roaming" / "com.flauncher.app" / "FLauncher" / "VE" / "versions"
    
    def _get_settings_path(self):
        user_folder = Path(os.path.expanduser("~"))
        return user_folder / "AppData" / "Roaming" / "com.flauncher.app" / "FLauncher" / "settings.json"
    
    def _create_directories(self):
        self.app_data_path.mkdir(parents=True, exist_ok=True)
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_settings(self):
        default_settings = {
            "github_repos": [],
            "discord_rpc_enabled": True,
            "launch_params": {
                "additional_args": ""
            }
        }
        
        if not self.settings_path.exists():
            self._save_settings(default_settings)
            return default_settings
        
        try:
            with open(self.settings_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default_settings
    
    def _save_settings(self, settings=None):
        if settings is None:
            settings = self.settings
        
        with open(self.settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
    
    def add_github_repo(self, repo):
        if repo not in self.settings["github_repos"]:
            self.settings["github_repos"].append(repo)
            self._save_settings()
            return True
        return False
    
    def remove_github_repo(self, repo):
        if repo in self.settings["github_repos"]:
            self.settings["github_repos"].remove(repo)
            self._save_settings()
            return True
        return False
    
    def toggle_discord_rpc(self):
        self.settings["discord_rpc_enabled"] = not self.settings.get("discord_rpc_enabled", True)
        self._save_settings()
        return self.settings["discord_rpc_enabled"]
    
    def update_launch_params(self, additional_args):
        self.settings["launch_params"]["additional_args"] = additional_args
        self._save_settings()