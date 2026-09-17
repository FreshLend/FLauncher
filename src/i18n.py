import json
import logging
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from utils import resource_path

log = logging.getLogger("flauncher.i18n")

DEFAULT_LANG = "en_US"
FALLBACK_LANG = "en_US"

_data = {}
_current = DEFAULT_LANG
_theme_overrides = {}


def _read_lang(code):
    try:
        d = Path(resource_path("ui/langs"))
    except Exception:
        d = Path("ui/langs")
    path = d / f"{code}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception as e:
        try:
            log.error("Lang load error %s: %s", code, e)
        except Exception:
            pass
    return None


_fallback_data = _read_lang(FALLBACK_LANG) or {}
_data = dict(_fallback_data)


class I18n(QObject):
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def langs_dir(self):
        try:
            return Path(resource_path("ui/langs"))
        except Exception:
            return Path("ui/langs")

    def available(self):
        result = []
        d = self.langs_dir()
        if not d.exists():
            return [(DEFAULT_LANG, "Русский")]
        for f in sorted(d.glob("*.json")):
            code = f.stem
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                name = data.get("_name", code)
            except Exception:
                name = code
            result.append((code, name))
        return result

    def load(self, code):
        global _data, _current

        fallback = dict(_fallback_data)

        if not code or code == FALLBACK_LANG:
            merged = fallback
            code = FALLBACK_LANG
        else:
            loaded = _read_lang(code)
            if loaded is None:
                merged = fallback
                code = FALLBACK_LANG
            else:
                merged = fallback
                merged.update(loaded)

        _data = merged
        _current = code
        self.language_changed.emit(code)

    def current(self):
        return _current

    def set_theme_overrides(self, overrides):
        global _theme_overrides
        if isinstance(overrides, dict):
            _theme_overrides = dict(overrides)
        else:
            _theme_overrides = {}

    def clear_theme_overrides(self):
        global _theme_overrides
        _theme_overrides = {}


i18n = I18n()


def tr(key, **kwargs):
    s = _theme_overrides.get(key)
    if s is None:
        s = _data.get(key)
    if s is None:
        return key
    if isinstance(s, list):
        s = s[0] if s else key
    if kwargs:
        try:
            return s.format(**kwargs)
        except Exception:
            return s
    return s


def tr_list(key):
    s = _theme_overrides.get(key)
    if s is None:
        s = _data.get(key)
    if isinstance(s, list):
        return list(s)
    return []


def tr_plural(key, n, **kwargs):
    forms = _theme_overrides.get(key)
    if forms is None:
        forms = _data.get(key)
    if not isinstance(forms, list) or not forms:
        return tr(key, n=n, **kwargs)

    if _current.startswith("ru"):
        n_abs = abs(n) % 100
        n1 = n_abs % 10
        if 10 < n_abs < 20:
            idx = 2
        elif 1 < n1 < 5:
            idx = 1
        elif n1 == 1:
            idx = 0
        else:
            idx = 2
    else:
        idx = 0 if abs(n) == 1 else 1

    if idx >= len(forms):
        idx = len(forms) - 1

    s = forms[idx]
    try:
        return s.format(n=n, **kwargs)
    except Exception:
        return s


def format_date(date_str):
    if not date_str:
        return tr("date.unknown")

    try:
        from datetime import datetime

        months = tr_list("date.months")
        if not months or len(months) < 12:
            months = [
                "января", "февраля", "марта", "апреля", "мая", "июня",
                "июля", "августа", "сентября", "октября", "ноября", "декабря",
            ]

        release_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        return tr(
            "date.format",
            day=release_date.day,
            month=months[release_date.month - 1],
            year=release_date.year,
        )
    except Exception:
        return tr("date.unknown")