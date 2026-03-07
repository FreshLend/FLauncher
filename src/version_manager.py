import re
import json
from concurrent.futures import as_completed
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from utils import MAX_LOAD, MAIN_REPO, get_platform_asset_pattern
from github_client import GitHubClient

class VersionManager(QObject):
    error_occurred = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, settings_manager, thread_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.thread_manager = thread_manager
        self._github_client = None
        self.app_data_path = settings_manager.app_data_path
        self.asset_pattern = get_platform_asset_pattern()
        self.artifact_data = {}
        self._is_shutting_down = False
        
        self.workflows = {
            'win32': [
                {'name': 'MSVC Build', 'file': 'windows.yml', 'pattern': '.zip', 'type': 'msvc'},
                {'name': 'CLang Build', 'file': 'windows-clang.yml', 'pattern': '.zip', 'type': 'clang'}
            ],
            'darwin': [
                {'name': 'macOS Build', 'file': 'macos.yml', 'pattern': '.dmg', 'type': 'macos'}
            ],
            'linux': [
                {'name': 'Linux Build', 'file': 'appimage.yml', 'pattern': '.AppImage', 'type': 'linux'}
            ]
        }
        
        self.artifact_names = {
            'windows.yml': 'Windows-Build',
            'windows-clang.yml': 'Windows-Build',
            'appimage.yml': 'Linux-Build',
            'macos.yml': 'macOS-Build'
        }
    
    @property
    def github_client(self):
        if self._github_client is None:
            self._github_client = GitHubClient(self.settings_manager)
            self._github_client.error_occurred.connect(self.error_occurred)
        return self._github_client
    
    def shutdown(self):
        self._is_shutting_down = True
        self.progress.emit("Завершение работы...")
    
    def get_github_repo_versions(self, repo):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return []
        
        try:
            response = self.github_client.get(
                f"https://api.github.com/repos/{repo}/releases",
                params={'per_page': MAX_LOAD}
            )
            
            if not response or response.status_code != 200:
                return []
            
            releases = response.json()
            if not isinstance(releases, list):
                return []
            
            valid_versions = []
            for release in releases:
                if self._is_shutting_down or self.thread_manager.is_shutting_down():
                    return valid_versions
                
                if not isinstance(release, dict) or 'tag_name' not in release:
                    continue
                
                assets = release.get('assets', [])
                has_platform_asset = any(
                    self.asset_pattern in asset.get('name', '') 
                    for asset in assets
                )
                
                if has_platform_asset:
                    author = repo.split('/')[0] if '/' in repo else repo
                    
                    if repo == MAIN_REPO:
                        display_name = release['tag_name']
                        folder_name = release['tag_name']
                    else:
                        display_name = f"{author}_{release['tag_name']}"
                        folder_name = f"{author}_{release['tag_name']}"
                    
                    valid_versions.append({
                        'tag': release['tag_name'],
                        'display_name': display_name,
                        'folder_name': folder_name,
                        'repo': repo,
                        'author': author,
                        'type': 'release',
                        'date': release.get('published_at', '')
                    })
            
            return valid_versions
            
        except Exception as e:
            if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                self.error_occurred.emit(f"Ошибка получения версий из {repo}: {str(e)}")
            return []
    
    def _get_workflow_artifacts(self, repo, workflow_file, build_name, pattern, build_type, limit=50):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return []
        
        artifacts = []
        expected_artifact_name = self.artifact_names.get(workflow_file)
        
        if not expected_artifact_name:
            return artifacts
        
        try:
            response = self.github_client.get(
                f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/runs",
                params={'per_page': min(limit, 100), 'status': 'success'}
            )
            
            if not response or response.status_code != 200:
                return artifacts
            
            runs = response.json().get('workflow_runs', [])
            
            for run in runs:
                if (self._is_shutting_down or self.thread_manager.is_shutting_down() or 
                    len(artifacts) >= limit):
                    break
                
                artifacts_response = self.github_client.get(run['artifacts_url'])
                
                if artifacts_response and artifacts_response.status_code == 200:
                    run_artifacts = artifacts_response.json().get('artifacts', [])
                    
                    for artifact in run_artifacts:
                        if (self._is_shutting_down or self.thread_manager.is_shutting_down() or 
                            len(artifacts) >= limit):
                            break
                        
                        if artifact['name'] == expected_artifact_name:
                            created_at = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                            
                            author = repo.split('/')[0] if '/' in repo else repo
                            
                            if repo == MAIN_REPO:
                                display_name = f"{build_name} - {created_at.strftime('%d.%m.%Y %H.%M')}"
                                folder_name = f"{build_name} - {created_at.strftime('%d.%m.%Y %H.%M')}"
                            else:
                                base_name = f"{build_name} - {created_at.strftime('%d.%m.%Y %H.%M')}"
                                display_name = f"{author}_{base_name}"
                                folder_name = f"{author}_{base_name}"
                            
                            artifacts.append({
                                'name': display_name,
                                'folder_name': folder_name,
                                'build_name': build_name,
                                'build_type': build_type,
                                'date': created_at,
                                'created_at': created_at,
                                'run_id': run['id'],
                                'artifact_id': artifact['id'],
                                'download_url': artifact['archive_download_url'],
                                'pattern': pattern,
                                'workflow_file': workflow_file,
                                'repo': repo,
                                'author': author
                            })
            
        except Exception as e:
            if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                self.error_occurred.emit(f"Ошибка получения артефактов из {workflow_file} для {repo}: {e}")
        
        return artifacts
    
    def get_artifacts(self, repo=MAIN_REPO, max_count=None):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return []
        
        if max_count is None:
            max_count = self.settings_manager.settings["artifacts"]["max_count"]
        
        all_artifacts = []
        platform_workflows = self.workflows.get(self.settings_manager.system, [])
        
        if self.settings_manager.system == 'win32':
            platform_workflows = [
                wf for wf in platform_workflows
                if self.settings_manager.settings["artifacts"]["windows"].get(wf['type'], True)
            ]
        
        if not platform_workflows:
            return []
        
        futures = []
        for wf in platform_workflows:
            future = self.thread_manager.submit(
                self._get_workflow_artifacts,
                repo, wf['file'], wf['name'], wf['pattern'], wf['type'], max_count
            )
            futures.append(future)
        
        for future in as_completed(futures):
            if self._is_shutting_down or self.thread_manager.is_shutting_down():
                for f in futures:
                    f.cancel()
                break
            
            try:
                artifacts = future.result(timeout=15)
                if artifacts and not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                    artifacts.sort(key=lambda x: x['date'], reverse=True)
                    all_artifacts.extend(artifacts[:max_count])
                    self.progress.emit(f"Загружено {len(artifacts[:max_count])} артефактов из {repo}")
            except Exception as e:
                if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                    self.error_occurred.emit(f"Ошибка получения артефактов из {repo}: {e}")
        
        if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
            all_artifacts.sort(key=lambda x: x['date'], reverse=True)
        
        return all_artifacts[:max_count]
    
    def get_all_online_versions(self):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return []
        
        all_versions = []
        repos_to_check = [MAIN_REPO] + self.settings_manager.settings.get("github_repos", [])
        
        self.progress.emit(f"Загрузка версий из {len(repos_to_check)} репозиториев...")
        
        futures = []
        for repo in repos_to_check:
            future = self.thread_manager.submit(self.get_github_repo_versions, repo)
            futures.append(future)
        
        for future in as_completed(futures):
            if self._is_shutting_down or self.thread_manager.is_shutting_down():
                for f in futures:
                    f.cancel()
                break
            
            try:
                repo_versions = future.result(timeout=10)
                all_versions.extend(repo_versions)
            except Exception as e:
                if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                    self.error_occurred.emit(f"Ошибка обработки репозитория: {str(e)}")
        
        if not (self._is_shutting_down or self.thread_manager.is_shutting_down()) and \
           self.settings_manager.settings["artifacts"]["enabled"]:
            
            artifact_futures = []
            for repo in repos_to_check:
                future = self.thread_manager.submit(self.get_artifacts, repo)
                artifact_futures.append(future)
            
            for future in as_completed(artifact_futures):
                if self._is_shutting_down or self.thread_manager.is_shutting_down():
                    for f in artifact_futures:
                        f.cancel()
                    break
                
                try:
                    artifacts = future.result(timeout=15)
                    for artifact in artifacts:
                        if self._is_shutting_down or self.thread_manager.is_shutting_down():
                            break
                        
                        date_iso = artifact['date'].isoformat()
                        
                        all_versions.append({
                            'tag': artifact['name'],
                            'display_name': artifact['name'],
                            'folder_name': artifact['folder_name'],
                            'repo': artifact['repo'],
                            'author': artifact['author'],
                            'type': 'artifact',
                            'date': date_iso,
                            'artifact_data': artifact
                        })
                        self.artifact_data[artifact['name']] = artifact
                except Exception as e:
                    if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                        self.error_occurred.emit(f"Ошибка получения артефактов: {e}")
        
        if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
            all_versions.sort(key=lambda x: x.get('date', ''), reverse=True)
            self.progress.emit(f"Всего загружено {len(all_versions)} версий")
        
        return all_versions
    
    def get_user_versions(self):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return []
        
        user_versions = []
        if self.app_data_path.exists():
            for folder in self.app_data_path.iterdir():
                if folder.is_dir():
                    if folder.name not in ['config', 'downloads', 'logs']:
                        version_tuple = self._version_to_tuple(folder.name)
                        user_versions.append((folder.name, version_tuple))
        
        user_versions.sort(key=lambda x: x[1], reverse=True)
        return [version[0] for version in user_versions]
    
    def _version_to_tuple(self, version_str):
        version_parts = re.findall(r'\d+', version_str)
        return tuple(map(int, version_parts)) if version_parts else (0,)
    
    def find_repo_for_version(self, version_tag):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return MAIN_REPO
        
        if version_tag in self.artifact_data:
            return self.artifact_data[version_tag].get('repo', MAIN_REPO)
        
        if '_' in version_tag and not version_tag.startswith('MSVC') and not version_tag.startswith('CLang'):
            author = version_tag.split('_')[0]
            for repo in self.settings_manager.settings.get("github_repos", []):
                if repo.startswith(author + '/'):
                    return repo
        
        return MAIN_REPO
    
    def get_username_from_config(self, version):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return None
        
        if not version or version == "Получение версий...":
            return None
        
        config_file_path = self.app_data_path / version / "config" / "quartz" / "config.json"
        
        if not config_file_path.exists():
            return None
        
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "Account" in config and "name" in config["Account"]:
                    return config["Account"]["name"]
        except Exception as e:
            if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                self.error_occurred.emit(f"Ошибка при чтении config.json: {e}")
        
        return None
    
    def update_username_in_config(self, username, version):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return
        
        if not version or version == "Получение версий...":
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
            if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                self.error_occurred.emit(f"Ошибка при обновлении config.json: {e}")
    
    def create_config_json(self, extraction_path):
        if self._is_shutting_down or self.thread_manager.is_shutting_down():
            return
        
        try:
            config_path = extraction_path / 'config' / 'quartz' / 'config.json'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_content = {
                "Account": {
                    "friends": {},
                    "name": "FLauncherPlayer"
                },
                "Servers": {},
                "Pinned_packs": {}
            }
            if not config_path.exists():
                with open(config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(config_content, config_file, indent=4)
        except Exception as e:
            if not (self._is_shutting_down or self.thread_manager.is_shutting_down()):
                self.error_occurred.emit(f"Не удалось создать config.json: {e}")