from PyQt6.QtWidgets import QMainWindow, QMessageBox, QInputDialog
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtCore import QUrl, pyqtSlot, pyqtSignal, QTimer
from ui_components import UIComponents
from discord_rpc import DiscordRPC
from version_manager import VersionManager
from download_manager import DownloadManager
from settings_manager import SettingsManager
from download_worker import DownloadWorker
from thread_manager import ThreadManager
from github_client import GitHubClient
from utils import resource_path, VERSION

class FLauncher(QMainWindow):
    repo_check_error = pyqtSignal(str)
    repo_added = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.thread_manager = ThreadManager()
        
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings
        
        self.github_client = GitHubClient(self.settings_manager)
        self.version_manager = VersionManager(self.settings_manager, self.thread_manager)
        self.download_manager = DownloadManager(self.version_manager)
        self.discord_rpc = DiscordRPC(self.settings_manager)
        
        self.ui = UIComponents(self, self.settings_manager)
        self.setup_ui()
        
        self._connect_signals()
        self.repo_check_error.connect(lambda msg: self.show_error_message("Ошибка", msg))
        self.repo_added.connect(self.on_repo_added)
        
        self.ui.set_username_from_config(
            self.version_manager.get_username_from_config(
                self.ui.version_combo.currentText()
            )
        )
        
        if self.settings.get("discord_rpc_enabled", True):
            self.connect_to_discord()
            self.set_discord_presence("Просматривает главную страницу", "")
        
        QTimer.singleShot(100, self.load_all_data)
    
    def setup_ui(self):
        self.setGeometry(100, 100, 1100, 650)
        self.setFixedSize(1100, 650)
        self.setWindowTitle(f'FLauncher {VERSION}')
        
        icon_path = resource_path('ui/icon.ico')
        self.setWindowIcon(QIcon(icon_path))
        
        self.ui.setup_all()
    
    def _connect_signals(self):
        self.ui.username_changed.connect(self.on_username_changed)
        self.ui.version_selected.connect(self.on_version_selected)
        self.ui.play_clicked.connect(self.on_play_button_click)
        self.ui.flm_clicked.connect(self.on_flm_button_click)
        self.ui.reload_clicked.connect(self.refresh_all_data)
        self.ui.folder_clicked.connect(self.open_versions_folder)
        self.ui.settings_clicked.connect(self.toggle_settings)
        self.ui.cancel_clicked.connect(self.cancel_download)
        
        self.github_client.releases_loaded.connect(self.ui.display_releases)
        self.github_client.error_occurred.connect(
            lambda msg: self.ui.show_release_error(msg)
        )
        self.github_client.rate_limit_info.connect(
            lambda data: self.ui.show_rate_limit_warning(
                data.get('remaining', 0), 
                data.get('limit', 60)
            )
        )
        
        self.version_manager.error_occurred.connect(
            lambda msg: self.show_error_message("Ошибка", msg)
        )
        self.version_manager.progress.connect(
            lambda msg: self.ui.download_info_label.setText(msg)
        )
        
        self.ui.artifacts_toggled.connect(self.toggle_artifacts)
        self.ui.artifacts_count_changed.connect(self.on_artifacts_count_changed)
        self.ui.windows_build_type_changed.connect(self.on_windows_build_type_changed)
        self.ui.discord_toggled.connect(self.toggle_discord_rpc)
        self.ui.launch_params_changed.connect(self.update_launch_params)
        self.ui.github_token_changed.connect(self.on_github_token_changed)
        self.ui.check_token_clicked.connect(self.check_github_token)
        self.ui.refresh_releases_clicked.connect(self.refresh_releases_panel)
        self.ui.add_repo_clicked.connect(self.add_github_repository)
        self.ui.remove_repo_clicked.connect(self.remove_github_repository)
    
    def connect_to_discord(self):
        self.discord_rpc.connect()
    
    def set_discord_presence(self, details, state, small_image=None):
        display_state = f"@{self.ui.input_field.text()}" if self.ui.input_field.text() else "Гость"
        self.discord_rpc.set_presence(details, display_state, small_image)
    
    def load_all_data(self):
        self.ui.version_combo.clear()
        self.ui.version_combo.addItem("Получение версий...")
        self.ui.download_info_label.setText("Загрузка данных...")
        
        def load_data():
            try:
                online_versions_info = self.version_manager.get_all_online_versions()
                
                releases = self.github_client.get_releases_for_display()
                
                if not self.isVisible():
                    return
                
                self._update_versions_combo(online_versions_info)
                
            except Exception as e:
                if self.isVisible():
                    self.show_error_message("Ошибка загрузки данных", str(e))
        
        future = self.thread_manager.submit(load_data)
    
    def _update_versions_combo(self, online_versions_info):
        current_items = [self.ui.version_combo.itemText(i) 
                        for i in range(self.ui.version_combo.count())]
        
        user_versions = self.version_manager.get_user_versions()
        for version in user_versions:
            if version not in current_items:
                self.ui.version_combo.addItem(version)
                current_items.append(version)
        
        added_versions = []
        for version_info in online_versions_info:
            if not self.isVisible():
                return
            
            version_tag = version_info.get('display_name', version_info['tag'])
            if version_tag not in current_items and version_tag not in added_versions:
                self.ui.version_combo.addItem(version_tag)
                added_versions.append(version_tag)
                
                if version_info.get('type') == 'artifact' and version_info.get('artifact_data'):
                    if not hasattr(self, 'artifact_data'):
                        self.artifact_data = {}
                    self.artifact_data[version_tag] = version_info.get('artifact_data')
        
        if self.ui.version_combo.count() > 1 and self.ui.version_combo.itemText(0) == "Получение версий...":
            self.ui.version_combo.removeItem(0)
        
        if self.ui.version_combo.count() > 0:
            self.ui.version_combo.setCurrentIndex(0)
        
        self.ui.download_info_label.setText("")
    
    @pyqtSlot()
    def refresh_all_data(self):
        self.load_all_data()
    
    @pyqtSlot(str)
    def on_username_changed(self, text):
        self.version_manager.update_username_in_config(
            text,
            self.ui.version_combo.currentText()
        )
    
    @pyqtSlot(str)
    def on_version_selected(self, version):
        username = self.version_manager.get_username_from_config(version)
        self.ui.set_username_from_config(username)
    
    @pyqtSlot()
    def on_play_button_click(self):
        selected_version = self.ui.version_combo.currentText()
        if selected_version == "Получение версий...":
            self.show_info_message("Выбор версии", "Пожалуйста, выберите версию для игры.")
            return
        
        version_folder = self.version_manager.app_data_path / selected_version
        
        if not version_folder.exists():
            reply = QMessageBox.question(
                self, 'Версия не найдена',
                f'Версия {selected_version} не установлена. Хотите скачать её сейчас?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.download_version(selected_version)
            return
        
        executable = self.download_manager.find_executable(version_folder)
        
        if executable:
            self.launch_game(executable, version_folder, selected_version)
        else:
            self.show_error_message(
                "Ошибка", 
                f"Не найден исполняемый файл для вашей платформы в папке {selected_version}"
            )
    
    @pyqtSlot(bool)
    def toggle_artifacts(self, enabled):
        self.settings_manager.set_artifacts_enabled(enabled)
        self.ui.update_artifacts_button_style(enabled)
        
        if hasattr(self.ui, 'artifacts_count_group'):
            self.ui.artifacts_count_group.setVisible(enabled)
        if hasattr(self.ui, 'windows_group'):
            self.ui.windows_group.setVisible(enabled)
        
        self.refresh_all_data()
    
    @pyqtSlot(int)
    def on_artifacts_count_changed(self, value):
        self.settings_manager.set_artifacts_max_count(value)
        self.refresh_all_data()
    
    @pyqtSlot(str, bool)
    def on_windows_build_type_changed(self, build_type, enabled):
        self.settings_manager.set_windows_artifact_visible(build_type, enabled)
        self.refresh_all_data()
    
    def download_version(self, version_tag):
        self.ui.play_button.setEnabled(False)
        self.ui.version_combo.setEnabled(False)
        self.ui.input_field.setEnabled(False)
        self.ui.reload_button.setEnabled(False)
        self.ui.flm_button.setEnabled(False)
        self.ui.folder_button.setEnabled(False)
        self.ui.settings_button.setEnabled(False)
        
        self.ui.set_cancel_button_visible(True)
        
        self.download_worker = DownloadWorker(self.download_manager, version_tag)
        self.download_worker.progress.connect(self.update_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(
            lambda msg: self.show_error_message("Ошибка загрузки", msg)
        )
        self.download_worker.start()
    
    @pyqtSlot(int, str)
    def update_download_progress(self, value, text):
        self.ui.progress_bar.setValue(value)
        self.ui.download_info_label.setText(text)
    
    @pyqtSlot(bool, str)
    def on_download_finished(self, success, message):
        self.ui.play_button.setEnabled(True)
        self.ui.version_combo.setEnabled(True)
        self.ui.input_field.setEnabled(True)
        self.ui.reload_button.setEnabled(True)
        self.ui.flm_button.setEnabled(True)
        self.ui.folder_button.setEnabled(True)
        self.ui.settings_button.setEnabled(True)
        
        self.ui.set_cancel_button_visible(False)
        
        self.ui.progress_bar.setValue(0)
        self.ui.download_info_label.setText("")
        
        if success:
            self.show_info_message("Успешно!", message)
            self.refresh_all_data()
        else:
            self.show_error_message("Ошибка", message)
    
    @pyqtSlot()
    def cancel_download(self):
        if hasattr(self, 'download_worker') and self.download_worker.isRunning():
            reply = QMessageBox.question(
                self, 'Отмена загрузки',
                'Вы действительно хотите отменить загрузку?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.download_worker.cancel()
                self.ui.download_info_label.setText("Отмена загрузки...")
                self.ui.cancel_button.setEnabled(False)
    
    def launch_game(self, voxel_core_path, working_directory, version):
        try:
            self.set_discord_presence(
                f"Играет в {version}",
                f"@{self.ui.input_field.text()}" if self.ui.input_field.text() else "Гость",
                "game"
            )
            
            self.download_manager.launch_game(
                voxel_core_path,
                working_directory,
                self.settings["launch_params"]["additional_args"]
            )
            
        except Exception as e:
            self.show_error_message("Ошибка запуска", str(e))
            self.set_discord_presence(
                "Просматривает главную страницу",
                f"@{self.ui.input_field.text()}" if self.ui.input_field.text() else "Гость",
                "home"
            )
    
    @pyqtSlot()
    def on_flm_button_click(self):
        if self.ui.FL_MODS.isVisible():
            self.ui.hide_flmods()
        else:
            self.ui.show_flmods()
            self.set_discord_presence("Просматривает FLMODS", "", "mods")
    
    @pyqtSlot()
    def open_versions_folder(self):
        url = QUrl.fromLocalFile(str(self.version_manager.app_data_path))
        QDesktopServices.openUrl(url)
    
    @pyqtSlot()
    def toggle_settings(self):
        if self.ui.settings_panel.isVisible():
            self.ui.hide_settings()
            self.set_discord_presence("Просматривает главную страницу", "", "home")
        else:
            self._update_settings_ui()
            self.ui.show_settings()
            self.set_discord_presence("В настройках", "", "settings")
    
    def _update_settings_ui(self):
        self.ui.update_discord_button_style(self.settings.get("discord_rpc_enabled", True))
        
        self.ui.additional_args_input.setText(self.settings["launch_params"]["additional_args"])
        
        self.ui.update_artifacts_button_style(self.settings["artifacts"]["enabled"])
        self.ui.artifacts_count_spin.setValue(self.settings["artifacts"]["max_count"])
        self.ui.artifacts_count_group.setVisible(self.settings["artifacts"]["enabled"])
        
        self.ui.github_token_input.setText(self.settings.get("github_token", ""))
        self.update_token_status()
        
        self.ui.load_github_repositories(self.settings.get("github_repos", []))
        
        if hasattr(self.ui, 'windows_group') and self.settings_manager.system == 'win32':
            self.ui.windows_group.setVisible(self.settings["artifacts"]["enabled"])
            if hasattr(self.ui, 'msvc_checkbox'):
                self.ui.msvc_checkbox.setChecked(self.settings["artifacts"]["windows"]["msvc"])
            if hasattr(self.ui, 'clang_checkbox'):
                self.ui.clang_checkbox.setChecked(self.settings["artifacts"]["windows"]["clang"])
    
    def show_error_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()
    
    def show_info_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

    @pyqtSlot()
    def on_repo_added(self):
        self.ui.load_github_repositories(
            self.settings_manager.settings.get("github_repos", [])
        )
        self.refresh_all_data()
    
    @pyqtSlot(str)
    def on_github_token_changed(self, token):
        self.settings_manager.set_github_token(token)
        self.update_token_status()
    
    @pyqtSlot()
    def check_github_token(self):
        token = self.settings_manager.get_github_token()
        if not token:
            self.ui.update_token_status("❌ Токен не указан", "#f44336")
            return
        
        user = self.github_client.get_authenticated_user()
        
        if user:
            rate_limit = self.github_client.check_rate_limit()
            if rate_limit:
                remaining = rate_limit.get('remaining', 0)
                limit = rate_limit.get('limit', 60)
                self.ui.update_token_status(
                    f"✅ Токен действителен (пользователь: {user.get('login', 'Unknown')})\n"
                    f"📊 Лимиты API: {remaining}/{limit} запросов осталось",
                    "#4CAF50"
                )
                
                reply = QMessageBox.question(
                    self, 'Обновить релизы?',
                    'Токен успешно проверен. Хотите обновить список релизов сейчас?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.refresh_releases_panel()
            else:
                self.ui.update_token_status(
                    f"✅ Токен действителен (пользователь: {user.get('login', 'Unknown')})",
                    "#4CAF50"
                )
        else:
            self.ui.update_token_status("❌ Токен недействителен", "#f44336")
    
    def update_token_status(self):
        token = self.settings_manager.get_github_token()
        if token:
            self.ui.update_token_status("⏳ Токен сохранен (нажмите 'Проверить' для проверки)", "#FF9800")
        else:
            self.ui.update_token_status("⚪ Токен не указан", "#9E9E9E")
    
    @pyqtSlot()
    def refresh_releases_panel(self):
        self.ui.download_info_label.setText("Загрузка релизов...")
        
        def load_releases():
            releases = self.github_client.get_releases_for_display()
        
        future = self.thread_manager.submit(load_releases)
    
    @pyqtSlot()
    def add_github_repository(self):
        repo, ok = QInputDialog.getText(
            self, 
            'Добавить репозиторий', 
            'Введите owner/repo (например: MihailRis/voxelcore):'
        )
        
        if ok and repo:
            if len(repo.split('/')) != 2:
                self.show_error_message("Ошибка", "Неверный формат. Используйте owner/repo")
                return
            
            def check_and_add():
                try:
                    exists = self.github_client.check_repo_exists(repo)
                    if exists:
                        if self.settings_manager.add_github_repo(repo):
                            self.repo_added.emit()
                    else:
                        self.repo_check_error.emit(f"Репозиторий {repo} не найден")
                except Exception as e:
                    self.repo_check_error.emit(f"Ошибка при проверке репозитория: {str(e)}")
            
            self.thread_manager.submit(check_and_add)
    
    @pyqtSlot(str)
    def remove_github_repository(self, repo):
        if self.settings_manager.remove_github_repo(repo):
            self.ui.load_github_repositories(
                self.settings_manager.settings.get("github_repos", [])
            )
            self.refresh_all_data()
    
    @pyqtSlot(bool)
    def toggle_discord_rpc(self, enabled):
        enabled = self.settings_manager.toggle_discord_rpc()
        if enabled:
            self.discord_rpc.connect()
            self.set_discord_presence("Просматривает главную страницу", "")
        else:
            self.discord_rpc.close()
        self.ui.update_discord_button_style(enabled)
    
    @pyqtSlot(str)
    def update_launch_params(self, text):
        self.settings_manager.update_launch_params(text)
    
    def closeEvent(self, event):
        print("Закрытие приложения...")
        self.discord_rpc.close()
        self.version_manager.shutdown()
        self.thread_manager.shutdown(timeout=3)
        event.accept()