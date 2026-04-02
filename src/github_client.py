import requests
import markdown
from PyQt6.QtCore import QObject, pyqtSignal
from utils import MAIN_REPO, format_date, get_platform_asset_pattern

class GitHubClient(QObject):
    error_occurred = pyqtSignal(str)
    rate_limit_info = pyqtSignal(dict)
    releases_loaded = pyqtSignal(list)
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.asset_pattern = get_platform_asset_pattern()
    
    def _get_headers(self):
        token = self.settings_manager.get_github_token()
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if token and token.strip():
            headers['Authorization'] = f'token {token}'
        return headers
    
    def get(self, url, params=None, timeout=10):
        try:
            headers = self._get_headers()
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            return response
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Ошибка при запросе к GitHub API: {e}")
            return None
    
    def check_rate_limit(self):
        try:
            response = self.get("https://api.github.com/rate_limit")
            if response and response.status_code == 200:
                data = response.json()
                rate = data.get('rate', {})
                return {
                    'remaining': rate.get('remaining', 0),
                    'limit': rate.get('limit', 60),
                    'reset': rate.get('reset', 0)
                }
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при проверке лимитов: {e}")
        return None
    
    def get_authenticated_user(self):
        try:
            response = self.get("https://api.github.com/user")
            if response and response.status_code == 200:
                return response.json()
            elif response and response.status_code == 401:
                self.error_occurred.emit("Токен недействителен или истек")
            elif response and response.status_code == 403:
                self.error_occurred.emit("Достигнут лимит запросов к API")
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при проверке токена: {e}")
        return None
    
    def check_repo_exists(self, repo):
        try:
            response = self.get(f"https://api.github.com/repos/{repo}", timeout=5)
            return response and response.status_code == 200
        except:
            return False
    
    def get_releases_for_display(self, limit=10):
        releases_data = []
        
        try:
            rate_limit = self.check_rate_limit()
            if rate_limit:
                self.rate_limit_info.emit(rate_limit)
            
            response = self.get(f"https://api.github.com/repos/{MAIN_REPO}/releases")
            if not response or response.status_code != 200:
                self.error_occurred.emit("Не удалось загрузить релизы")
                return []
            
            releases = response.json()
            
            platform_names = {
                'win64.zip': 'Windows',
                '.dmg': 'macOS',
                '.AppImage': 'Linux'
            }
            platform_name = platform_names.get(self.asset_pattern, 'Unknown')
            
            for release in releases[:limit]:
                if isinstance(release, dict):
                    assets = release.get('assets', [])
                    has_platform_asset = any(
                        self.asset_pattern in asset.get('name', '') 
                        for asset in assets
                    )
                    
                    if not has_platform_asset:
                        continue
                    
                    tag_name = release.get('tag_name', '')
                    version = tag_name.replace('voxelcore', '').strip()
                    release_url = release.get('html_url', '#')
                    
                    release_date_str = release.get('published_at', '')
                    release_date_formatted = format_date(release_date_str) if release_date_str else "Дата неизвестна"
                    
                    release_body = release.get('body', '')
                    html_body = markdown.markdown(release_body) if release_body else ""
                    if html_body:
                        html_body = html_body.replace('<a', '<a target="_blank"')
                    
                    releases_data.append({
                        'version': version,
                        'tag_name': tag_name,
                        'release_url': release_url,
                        'date': release_date_formatted,
                        'date_raw': release_date_str,
                        'body_html': html_body,
                        'platform_name': platform_name,
                        'repo': MAIN_REPO
                    })
            
            self.releases_loaded.emit(releases_data)
            return releases_data
            
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit("Не удалось загрузить релизы. Проверьте соединение с интернетом.")
            return []
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при обработке данных: {str(e)}")
            return []