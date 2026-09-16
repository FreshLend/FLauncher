import logging
import requests
from PyQt6.QtCore import QObject, pyqtSignal

log = logging.getLogger("flauncher.update_checker")

UPDATE_REPO = "FreshLend/FLauncher"
RELEASES_URL = f"https://github.com/{UPDATE_REPO}/releases"


def parse_version(v):
    if not v:
        return (0,)
    s = str(v).strip().lower()
    if s.startswith("v"):
        s = s[1:]
    parts = []
    for chunk in s.split("."):
        num = ""
        for c in chunk:
            if c.isdigit():
                num += c
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts) if parts else (0,)


def is_newer(latest, current):
    a = parse_version(latest)
    b = parse_version(current)
    n = max(len(a), len(b))
    a = a + (0,) * (n - len(a))
    b = b + (0,) * (n - len(b))
    return a > b


class UpdateChecker(QObject):
    update_available = pyqtSignal(str, str)
    check_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def check(self, current_version):
        try:
            response = requests.get(
                f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            if response.status_code != 200:
                log.warning("Не удалось проверить обновления: код %s", response.status_code)
                self.check_finished.emit()
                return

            data = response.json()
            if not isinstance(data, dict):
                self.check_finished.emit()
                return

            tag = data.get("tag_name", "") or ""
            html_url = data.get("html_url", RELEASES_URL) or RELEASES_URL

            if tag and is_newer(tag, current_version):
                log.info("Доступно обновление: %s (текущая %s)", tag, current_version)
                self.update_available.emit(tag, html_url)

            self.check_finished.emit()
        except Exception as e:
            log.error("Ошибка проверки обновлений: %s", e)
            self.check_finished.emit()