import json
import os
import shutil
import logging
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from utils import resource_path

log = logging.getLogger("flauncher.themes")


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
        "progress_bar": [10, 3, -20, 15],
        "cancel_button": [1010, 3, 80, 15]
    }
}


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
            log.error("Ошибка загрузки темы %s: %s", path, e)
            return None

    def _ensure_themes_on_disk(self):
        dst = self._user_dir()
        if not dst:
            return
        try:
            dst.mkdir(parents=True, exist_ok=True)
        except Exception:
            return

        src_themes = self._builtin_dir()
        if src_themes and src_themes.exists():
            for item in src_themes.rglob("*"):
                if item.is_dir():
                    continue
                if item.name.startswith("_"):
                    continue
                try:
                    rel = item.relative_to(src_themes)
                except Exception:
                    continue
                target = dst / rel
                if target.exists():
                    continue
                try:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
                except Exception:
                    pass

        self._copy_ui_assets(dst)

        fldr = dst / "FLauncher"
        if not any(fldr.glob("*.json")) and not any(dst.glob("*.json")):
            try:
                fldr.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            target = fldr / "tlauncher.json"
            if not target.exists():
                try:
                    with open(target, "w", encoding="utf-8") as f:
                        json.dump(FALLBACK_THEME, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

    def _copy_ui_assets(self, dst):
        try:
            src_ui = Path(resource_path("ui/images"))
        except Exception:
            return
        if not src_ui.exists():
            return

        skip_names = {"icon.ico", "icon.icns", "icon.png"}
        skip_exts = {".py", ".pyc", ".pyo"}

        target_ui = dst / "FLauncher" / "ui"
        try:
            target_ui.mkdir(parents=True, exist_ok=True)
        except Exception:
            return

        for item in src_ui.rglob("*"):
            if not item.is_file():
                continue
            if item.name.startswith("_"):
                continue
            if item.name.lower() in skip_names:
                continue
            if item.suffix.lower() in skip_exts:
                continue
            try:
                rel = item.relative_to(src_ui)
            except Exception:
                continue
            target = target_ui / rel
            if target.exists():
                continue
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
            except Exception:
                pass

    def reload(self):
        self.themes = {}
        self._ensure_themes_on_disk()

        for d in (self._builtin_dir(), self._user_dir()):
            if d and d.exists():
                self._load_dir(d)

        if not self.themes:
            fallback = json.loads(json.dumps(FALLBACK_THEME))
            fallback["_files_dir"] = None
            fallback["_base_key"] = "tlauncher"
            fallback["_is_variant"] = False
            self.themes["tlauncher"] = fallback

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
        except Exception:
            return None

        try:
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
                result.append((v_key, "    " + v_name))

        return result

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