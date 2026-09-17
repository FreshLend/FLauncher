import os
import json
import sys
from pathlib import Path


class SettingsManager:
    def __init__(self):
        self.system = sys.platform
        self.app_data_path = self._get_app_data_path()
        self.settings_path = self._get_settings_path()
        self.downloads_path = self._get_downloads_path()
        self.logs_path = self._get_logs_path()

        self._create_directories()
        self.settings = self._load_settings()

    def _get_app_data_path(self):
        if self.system == 'win32':
            base_path = Path(os.environ.get('APPDATA', ''))
            if not base_path:
                base_path = Path.home() / 'AppData' / 'Roaming'
            return base_path / 'com.flauncher.app' / 'FLauncher' / 'VC' / 'versions'
        elif self.system == 'darwin':
            return Path.home() / 'Library' / 'Application Support' / 'com.flauncher.app' / 'FLauncher' / 'VC' / 'versions'
        else:
            return Path.home() / '.local' / 'share' / 'com.flauncher.app' / 'FLauncher' / 'VC' / 'versions'

    def _get_settings_path(self):
        if self.system == 'win32':
            base_path = Path(os.environ.get('APPDATA', ''))
            if not base_path:
                base_path = Path.home() / 'AppData' / 'Roaming'
            return base_path / 'com.flauncher.app' / 'FLauncher' / 'settings.json'
        elif self.system == 'darwin':
            return Path.home() / 'Library' / 'Application Support' / 'com.flauncher.app' / 'FLauncher' / 'settings.json'
        else:
            return Path.home() / '.config' / 'com.flauncher.app' / 'FLauncher' / 'settings.json'

    def _get_downloads_path(self):
        return self.app_data_path.parent / "downloads"

    def _get_logs_path(self):
        return self.settings_path.parent / "logs"

    def _create_directories(self):
        self.app_data_path.mkdir(parents=True, exist_ok=True)
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        (self.settings_path.parent / "themes").mkdir(parents=True, exist_ok=True)

    def _load_settings(self):
        default_settings = {
            "github_repos": [],
            "discord_rpc_enabled": True,
            "theme": "tlauncher",
            "language": "en_US",
            "launch_params": {
                "additional_args": ""
            },
            "artifacts": {
                "enabled": False,
                "max_count": 1,
                "windows": {
                    "msvc": False,
                    "clang": True
                }
            },
            "github_token": ""
        }

        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    default_settings.update(settings)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

        if self.system != 'win32':
            try:
                default_settings["artifacts"]["windows"]["msvc"] = False
            except Exception:
                pass

        return default_settings

    def _save_settings(self, settings=None):
        if settings is None:
            settings = self.settings

        tmp_path = self.settings_path.parent / (self.settings_path.name + ".tmp")

        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass

            os.replace(tmp_path, self.settings_path)

            try:
                os.chmod(self.settings_path, 0o600)
            except Exception:
                pass
        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            raise

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

    def set_artifacts_enabled(self, enabled):
        self.settings["artifacts"]["enabled"] = enabled
        self._save_settings()

    def set_artifacts_max_count(self, count):
        self.settings["artifacts"]["max_count"] = count
        self._save_settings()

    def set_windows_artifact_visible(self, build_type, visible):
        if self.system != 'win32':
            return
        if build_type in ["msvc", "clang"]:
            self.settings["artifacts"]["windows"][build_type] = visible
            self._save_settings()

    def set_github_token(self, token):
        self.settings["github_token"] = token
        self._save_settings()

    def get_github_token(self):
        return self.settings.get("github_token", "")

    def set_language(self, code):
        self.settings["language"] = code
        self._save_settings()

    def get_language(self):
        return self.settings.get("language", "ru_RU")