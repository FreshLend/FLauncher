import json
import os
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from utils import resource_path


FALLBACK_THEME = {
    "name": "TLauncher",
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
    "background": None,
    "icons": {},
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
    "icon_bg": "transparent",
    "icon_border": "transparent",
    "icon_hover": "rgba(255, 255, 255, 0.1)",
    "icon_pressed": "rgba(255, 255, 255, 0.15)",
    "icon_radius": 5,
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
    "settings_header_text": "#ffffff",
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
    "flmods_topbar_bg": "#3498db",
    "flmods_topbar_text": "white",
    "flmods_tab_active_bg": "white",
    "flmods_tab_active_text": "#3498db",
    "flmods_bg": "white",
    "flmods_card_bg": "#f5f5f5",
    "flmods_card_border": "#dcdcdc",
    "flmods_title_text": "#222222",
    "flmods_body_text": "#555555",
    "flmods_meta_text": "#999999",
    "flmods_sidebar_bg": "#ffffff",
    "flmods_sidebar_border": "#e0e0e0",
    "flmods_sidebar_item_bg": "#f5f5f5",
}


REFERENCE_THEME_JSON = json.dumps(FALLBACK_THEME, ensure_ascii=False, indent=2)


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

    def _load_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return None
            return data
        except Exception as e:
            print(f"Ошибка загрузки темы {path}: {e}")
            return None

    def reload(self):
        self.themes = {}
        for d in (self._builtin_dir(), self._user_dir()):
            if d and d.exists():
                self._load_dir(d)

        if "tlauncher" not in self.themes:
            try:
                data = json.loads(REFERENCE_THEME_JSON)
                data["_files_dir"] = None
                data["_base_key"] = "tlauncher"
                data["_is_variant"] = False
                self.themes["tlauncher"] = data
            except Exception:
                pass

        if self.current_key not in self.themes and self.themes:
            self.current_key = next(iter(self.themes))

    def _load_dir(self, base_dir):
        for f in sorted(base_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            data = self._load_json(f)
            if data:
                key = f.stem
                data.setdefault("name", key)
                data["_files_dir"] = base_dir
                data["_base_key"] = key
                data["_is_variant"] = False
                self.themes[key] = data

        for folder in sorted(base_dir.iterdir()):
            if not folder.is_dir() or folder.name.startswith("_"):
                continue
            self._load_theme_folder(folder)

    def _load_theme_folder(self, folder):
        json_data = {}
        for f in sorted(folder.glob("*.json")):
            if f.name.startswith("_"):
                continue
            data = self._load_json(f)
            if data:
                json_data[f.stem] = data

        if not json_data:
            return

        bases = {stem for stem in json_data if "." not in stem}

        for stem, data in json_data.items():
            if stem in bases:
                data.setdefault("name", stem)
                data["_files_dir"] = folder
                data["_base_key"] = stem
                data["_is_variant"] = False
                self.themes[stem] = data

        for stem, data in json_data.items():
            if stem in bases:
                continue

            if "." not in stem:
                data.setdefault("name", stem)
                data["_files_dir"] = folder
                data["_base_key"] = stem
                data["_is_variant"] = False
                self.themes[stem] = data
                continue

            base = stem.rsplit(".", 1)[1]
            if base in self.themes:
                data.setdefault("name", stem)
                data["_files_dir"] = folder
                data["_base_key"] = base
                data["_is_variant"] = True
                merged = dict(self.themes[base])
                merged.update(data)
                self.themes[stem] = merged
            else:
                data.setdefault("name", stem)
                data["_files_dir"] = folder
                data["_base_key"] = stem
                data["_is_variant"] = False
                self.themes[stem] = data

    def resolve_file(self, rel_path):
        if not rel_path or not isinstance(rel_path, str):
            return None
        rel_path = rel_path.strip()
        if not rel_path:
            return None

        if os.path.isabs(rel_path) or rel_path.startswith("~"):
            return None

        try:
            parts = Path(rel_path).parts
        except Exception:
            return None
        if ".." in parts:
            return None

        files_dir = self.current.get("_files_dir")
        if not files_dir:
            return None

        try:
            files_abs = Path(files_dir).resolve()
            full = (files_abs / rel_path).resolve()
            try:
                full.relative_to(files_abs)
            except ValueError:
                return None
            if not full.is_file():
                return None
            return full
        except Exception:
            return None

    def get_icon(self, name):
        icons = self.current.get("icons") or {}
        rel = icons.get(name)
        return self.resolve_file(rel)

    def get_background(self):
        return self.resolve_file(self.current.get("background"))

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

    def all_labels(self):
        result = []
        base_keys = [k for k, v in self.themes.items() if not v.get("_is_variant", False)]
        base_keys.sort(key=lambda k: self.themes[k].get("name", k).lower())

        for base_key in base_keys:
            base_name = self.themes[base_key].get("name", base_key)
            result.append((base_key, base_name))

            variants = []
            for k, v in self.themes.items():
                if v.get("_is_variant", False) and v.get("_base_key") == base_key:
                    variants.append((k, v.get("name", k)))
            variants.sort(key=lambda x: x[1].lower())

            for v_key, v_name in variants:
                label = "    " + v_name
                result.append((v_key, label))

        return result

    def base_themes(self):
        result = []
        for k, v in self.themes.items():
            if not v.get("_is_variant", False):
                result.append((k, v.get("name", k)))
        result.sort(key=lambda x: x[1].lower())
        return result

    def variants_of(self, base_key):
        base_name = self.themes.get(base_key, {}).get("name", base_key)
        variants = []
        for k, v in self.themes.items():
            if v.get("_is_variant", False) and v.get("_base_key") == base_key:
                variants.append((k, v.get("name", k)))
        variants.sort(key=lambda x: x[1].lower())
        return [(base_key, base_name)] + variants

    def is_variant(self, key):
        return self.themes.get(key, {}).get("_is_variant", False)

    def base_of(self, key):
        return self.themes.get(key, {}).get("_base_key", key)

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