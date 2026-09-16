import json
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from utils import resource_path


FALLBACK_THEME = {
    "name": "Fallback",
    "layout": {
        "mode": "bar",
        "bar_position": "bottom",
        "bar_height": 90,
        "hide_info": False,
        "hide_releases": False,
        "release_scroll": [20, 10, 800, -20],
        "info_panel": [830, 10, 250, -20],
        "nick_input": [10, 20, 200, 60],
        "version_combo": [220, 20, 300, 60],
        "play_button": [530, 20, 300, 60],
        "flm_button": [835, 20, 60, 60],
        "reload_button": [895, 20, 60, 60],
        "folder_button": [965, 20, 60, 60],
        "settings_button": [1035, 20, 60, 60],
        "progress_bar": [10, 0, -20, 20],
        "cancel_button": [1000, 0, 80, 20]
    },
    "bottom_bar": "rgba(113, 169, 76, 0.9)",
    "bottom_bar_text": "black",
    "input_bg": "white",
    "input_text": "black",
    "input_border": "transparent",
    "combo_bg": "white",
    "combo_text": "black",
    "combo_arrow": "black",
    "combo_border": "transparent",
    "combo_focus": "#3498db",
    "play_bg": "rgb(236, 193, 63)",
    "play_hover": "rgb(246, 203, 73)",
    "play_pressed": "rgb(226, 183, 53)",
    "play_text": "white",
    "icon_hover": "rgba(255, 255, 255, 0.1)",
    "release_panel_bg": "rgba(255, 255, 255, 0.85)",
    "release_panel_border": "rgba(255, 255, 255, 0.35)",
    "release_version": "#0066cc",
    "release_text": "#333",
    "release_date": "#888",
    "info_panel_bg": "rgba(90, 171, 215, 0.5)",
    "info_panel_border": "rgba(255, 255, 255, 0.2)",
    "info_text": "white",
    "info_btn_bg": "rgba(62, 148, 182, 0.85)",
    "info_btn_hover": "rgba(72, 158, 192, 0.95)",
    "info_btn_pressed": "rgba(52, 138, 172, 1.0)",
    "info_btn_border": "rgba(255, 255, 255, 0.3)",
    "info_btn_border_hover": "rgba(255, 255, 255, 0.5)",
    "settings_bg": "#f5f5f5",
    "settings_header": "#0086c7",
    "settings_tab_bg": "#E4E4E4",
    "settings_tab_hover": "#D8D8D8",
    "settings_tab_active": "#0086c7",
    "settings_tab_text": "#333",
    "settings_tab_active_text": "white",
    "group_title_bg": "#F5F5F5",
    "group_title_text": "#333",
    "group_border": "#E0E0E0",
    "group_body_bg": "white",
    "input_field_bg": "white",
    "input_field_text": "black",
    "input_field_border": "#CCC",
    "input_field_focus": "#0086c7",
    "accent": "#3498db",
    "accent_hover": "#2980b9",
    "install_bg": "#2ecc71",
    "install_hover": "#27ae60",
    "reinstall_bg": "#f39c12",
    "reinstall_hover": "#e67e22",
    "update_bg": "#3498db",
    "update_hover": "#2980b9",
    "flmods_header": "#00aaff",
    "flmods_text": "white",
}


REFERENCE_THEME_JSON = """{
  "name": "TLauncher",
  "layout": {
    "mode": "bar",
    "bar_position": "bottom",
    "bar_height": 90,
    "hide_info": false,
    "hide_releases": false,
    "release_scroll": [20, 10, 800, -20],
    "info_panel": [830, 10, 250, -20],
    "nick_input": [10, 20, 200, 60],
    "version_combo": [220, 20, 300, 60],
    "play_button": [530, 20, 300, 60],
    "flm_button": [835, 20, 60, 60],
    "reload_button": [895, 20, 60, 60],
    "folder_button": [965, 20, 60, 60],
    "settings_button": [1035, 20, 60, 60],
    "progress_bar": [10, 0, -20, 20],
    "cancel_button": [1000, 0, 80, 20]
  },
  "bottom_bar": "rgba(113, 169, 76, 0.9)",
  "bottom_bar_text": "black",
  "input_bg": "white",
  "input_text": "black",
  "input_border": "transparent",
  "combo_bg": "white",
  "combo_text": "black",
  "combo_arrow": "black",
  "combo_border": "transparent",
  "combo_focus": "#3498db",
  "play_bg": "rgb(236, 193, 63)",
  "play_hover": "rgb(246, 203, 73)",
  "play_pressed": "rgb(226, 183, 53)",
  "play_text": "white",
  "icon_hover": "rgba(255, 255, 255, 0.1)",
  "release_panel_bg": "rgba(255, 255, 255, 0.85)",
  "release_panel_border": "rgba(255, 255, 255, 0.35)",
  "release_version": "#0066cc",
  "release_text": "#333",
  "release_date": "#888",
  "info_panel_bg": "rgba(90, 171, 215, 0.5)",
  "info_panel_border": "rgba(255, 255, 255, 0.2)",
  "info_text": "white",
  "info_btn_bg": "rgba(62, 148, 182, 0.85)",
  "info_btn_hover": "rgba(72, 158, 192, 0.95)",
  "info_btn_pressed": "rgba(52, 138, 172, 1.0)",
  "info_btn_border": "rgba(255, 255, 255, 0.3)",
  "info_btn_border_hover": "rgba(255, 255, 255, 0.5)",
  "settings_bg": "#f5f5f5",
  "settings_header": "#0086c7",
  "settings_tab_bg": "#E4E4E4",
  "settings_tab_hover": "#D8D8D8",
  "settings_tab_active": "#0086c7",
  "settings_tab_text": "#333",
  "settings_tab_active_text": "white",
  "settings_header_text": "#ffffff",
  "group_title_bg": "#F5F5F5",
  "group_title_text": "#333",
  "group_border": "#E0E0E0",
  "group_body_bg": "white",
  "input_field_bg": "white",
  "input_field_text": "black",
  "input_field_border": "#CCC",
  "input_field_focus": "#0086c7",
  "accent": "#3498db",
  "accent_hover": "#2980b9",
  "install_bg": "#2ecc71",
  "install_hover": "#27ae60",
  "reinstall_bg": "#f39c12",
  "reinstall_hover": "#e67e22",
  "update_bg": "#3498db",
  "update_hover": "#2980b9",
  "flmods_header": "#00aaff",
  "flmods_text": "white"
}
"""


class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.themes = {}
        self.current_key = "tlauncher"
        self.reload()
        saved = settings_manager.settings.get("theme", "tlauncher")
        if saved in self.themes:
            self.current_key = saved
        elif self.themes:
            self.current_key = next(iter(self.themes))

    def _builtin_dir(self):
        try:
            return Path(resource_path("themes"))
        except Exception:
            return Path("themes")

    def _user_dir(self):
        try:
            return Path(self.settings_manager.settings_path).parent / "themes"
        except Exception:
            return None

    def _write_tlauncher(self, user_dir):
        if not user_dir:
            return
        try:
            user_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return
        path = user_dir / "tlauncher.json"
        if path.exists():
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(REFERENCE_THEME_JSON)
        except Exception:
            pass

    def _load_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return None
            data.setdefault("name", path.stem)
            return data
        except Exception as e:
            print(f"Ошибка загрузки темы {path}: {e}")
            return None

    def reload(self):
        self.themes = {}
        builtin = self._builtin_dir()
        if builtin and builtin.exists():
            for f in sorted(builtin.glob("*.json")):
                data = self._load_json(f)
                if data:
                    self.themes[f.stem] = data

        user = self._user_dir()
        self._write_tlauncher(user)
        if user:
            for f in sorted(user.glob("*.json")):
                if f.name.startswith("_"):
                    continue
                data = self._load_json(f)
                if data:
                    self.themes[f.stem] = data

        if "tlauncher" not in self.themes:
            try:
                self.themes["tlauncher"] = json.loads(REFERENCE_THEME_JSON)
            except Exception:
                self.themes["tlauncher"] = dict(FALLBACK_THEME)

        if self.current_key not in self.themes and self.themes:
            self.current_key = next(iter(self.themes))

    @property
    def current(self):
        if self.current_key in self.themes:
            merged = dict(FALLBACK_THEME)
            user = self.themes[self.current_key]
            merged.update(user)
            base_layout = dict(FALLBACK_THEME["layout"])
            user_layout = user.get("layout")
            if isinstance(user_layout, dict):
                base_layout.update(user_layout)
                merged["layout"] = base_layout
            return merged
        return dict(FALLBACK_THEME)

    def get(self, key, default=""):
        return self.current.get(key, default)

    def name(self):
        return self.current.get("name", self.current_key)

    def available(self):
        result = []
        for k, v in self.themes.items():
            result.append((k, v.get("name", k)))
        result.sort(key=lambda x: x[1].lower())
        return result

    def user_dir(self):
        d = self._user_dir()
        return d if d else None

    def set_theme(self, key):
        if key not in self.themes:
            return False
        if key == self.current_key:
            return False
        self.current_key = key
        self.settings_manager.settings["theme"] = key
        self.settings_manager._save_settings()
        self.theme_changed.emit(key)
        return True