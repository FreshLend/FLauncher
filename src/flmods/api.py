import time
import logging
from pathlib import Path

import requests

from i18n import tr, tr_plural

log = logging.getLogger("flauncher.flmods.api")


def format_relative_time(iso_str):
    from datetime import datetime, timezone
    if not iso_str or not isinstance(iso_str, str):
        return tr("time.unknown")
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - dt
        if delta.total_seconds() < 0:
            return tr("time.just_now")
        years = delta.days // 365
        months = (delta.days // 30) % 12
        days = delta.days % 30
        if days >= 15:
            months += 1
        if months >= 12:
            years += 1
            months = 0

        if years > 0:
            return tr_plural("time.years_ago", years)
        if months > 0:
            return tr_plural("time.months_ago", months)
        if days > 0:
            return tr_plural("time.days_ago", days)
        if delta.seconds // 3600 > 0:
            hours = delta.seconds // 3600
            return tr_plural("time.hours_ago", hours)
        if delta.seconds // 60 > 0:
            minutes = delta.seconds // 60
            return tr_plural("time.minutes_ago", minutes)
        return tr("time.just_now")
    except Exception:
        return iso_str


def normalize_version_str(v):
    if v is None:
        return ""
    s = str(v).strip().lower()
    if s.startswith('v'):
        s = s[1:]
    return s


def is_valid_version(v):
    if v is None:
        return False
    s = normalize_version_str(v)
    if not s:
        return False
    if s in ("неизвестно", "загрузка...", "unknown", "loading..."):
        return False
    return True


class VoxelWorldAPI:
    BASE_URL = "https://api.voxelworld.ru/v2"

    SORT_MAP = {
        "popular": (1, "desc"),
        "new": (2, "desc"),
        "alphabet": (3, "asc"),
    }

    def __init__(self):
        self.headers = {
            "User-Agent": "FLauncher/0.7.0 (freshlend.studio@gmail.com)",
            "Accept": "application/json"
        }

    def get_data(self, endpoint, search_query="", sort_id="popular", page=1, tag_ids=None):
        sort_val, sort_order = self.SORT_MAP.get(sort_id, (1, "desc"))
        params = {"page": page, "sortOrder": sort_order, "sort": sort_val, "item_count": 100}

        if search_query:
            params["title"] = search_query
        if tag_ids:
            if isinstance(tag_ids, int):
                tag_ids = [tag_ids]
            params['tag_id[]'] = tag_ids

        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", headers=self.headers,
                                    params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                for key in ['mods', 'items', 'data', 'results', 'texturepacks', 'worlds']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
            if isinstance(data, list):
                return data
        except Exception as e:
            log.error(tr("log.api_error", endpoint=endpoint, error=e))
        return []

    def get_tags(self, tag_type):
        try:
            response = requests.get(f"{self.BASE_URL}/tags", headers=self.headers,
                                    params={"type": tag_type}, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ['tags', 'items', 'data', 'results']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
        except Exception as e:
            log.error(tr("log.tags_error", tag_type=tag_type, error=e))
        return []

    def get_latest_version(self, mod_id):
        for attempt in range(3):
            try:
                response = requests.get(f"{self.BASE_URL}/mods/{mod_id}/versions/latest",
                                        headers=self.headers, timeout=10)
                if response.status_code == 429:
                    time.sleep(3)
                    continue
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict):
                    if data.get("version_number"):
                        return str(data.get("version_number"))
                    if data.get("version"):
                        return str(data.get("version"))
                    if data.get("tag_name"):
                        return str(data.get("tag_name"))
                    engine = data.get("engine")
                    if isinstance(engine, dict) and engine.get("version_number"):
                        return str(engine.get("version_number"))
                    inner_data = data.get("data")
                    if isinstance(inner_data, dict):
                        if inner_data.get("version_number"):
                            return str(inner_data.get("version_number"))
                        engine_inner = inner_data.get("engine")
                        if isinstance(engine_inner, dict) and engine_inner.get("version_number"):
                            return str(engine_inner.get("version_number"))
            except Exception:
                time.sleep(1)
                continue
        return "?"

    def get_version_info(self, content_type, content_id):
        for attempt in range(3):
            try:
                response = requests.get(
                    f"{self.BASE_URL}/{content_type}/{content_id}/versions/latest",
                    headers=self.headers, timeout=10
                )
                if response.status_code == 429:
                    time.sleep(3)
                    continue
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict):
                    inner = data.get('data', data)
                    if isinstance(inner, dict):
                        return inner
            except Exception:
                time.sleep(1)
                continue
        return None

    def get_download_url(self, content_type, content_id, version_id):
        try:
            response = requests.get(
                f"{self.BASE_URL}/{content_type}/{content_id}/versions/{version_id}/download",
                headers=self.headers, timeout=15, allow_redirects=True
            )
            if response.status_code == 200:
                return response.url
        except Exception as e:
            log.error(tr("log.download_url_error", error=e))
        return None

    def download_version(self, content_type, content_id, version_id,
                         progress_callback=None, is_cancelled_callback=None,
                         downloads_path=None):
        try:
            info = self.get_version_info(content_type, content_id)
            download_url = None
            if isinstance(info, dict):
                download_url = (info.get('download_url') or info.get('file_url')
                                or info.get('url') or info.get('download'))
            if not download_url:
                download_url = self.get_download_url(content_type, content_id, version_id)
            if not download_url:
                return False, None, "no_download_url"

            if downloads_path is None:
                downloads_path = Path.home() / "Downloads"
            downloads_path = Path(downloads_path)
            downloads_path.mkdir(parents=True, exist_ok=True)

            zip_path = downloads_path / f"{content_type}_{content_id}_{version_id}.zip"

            response = requests.get(download_url, headers=self.headers,
                                    stream=True, timeout=30)
            if response.status_code != 200:
                return False, None, f"HTTP {response.status_code}"

            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if is_cancelled_callback and is_cancelled_callback():
                        f.close()
                        if zip_path.exists():
                            zip_path.unlink()
                        return False, None, "cancelled"
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(int((downloaded / total_size) * 100))

            return True, zip_path, None
        except Exception as e:
            return False, None, str(e)