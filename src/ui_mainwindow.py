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
from themes import ThemeManager
from utils import resource_path, VERSION
from flmods import InstallWorker


class FLauncher(QMainWindow):
    repo_check_error = pyqtSignal(str)
    repo_added = pyqtSignal()
    versions_loaded = pyqtSignal(object)
    load_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.thread_manager = ThreadManager()
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings
        self.theme_manager = ThemeManager(self.settings_manager)
        self.github_client = GitHubClient(self.settings_manager)
        self.version_manager = VersionManager(self.settings_manager, self.thread_manager)
        self.download_manager = DownloadManager(self.version_manager)
        self.discord_rpc = DiscordRPC(self.settings_manager)
        self.ui = UIComponents(self, self.settings_manager, self.theme_manager)
        self.artifact_data = {}
        self.setup_ui()
        self._connect_signals()
        self.repo_check_error.connect(lambda msg: self.show_error_message("Ошибка", msg))
        self.repo_added.connect(self.on_repo_added)
        self.versions_loaded.connect(self._update_versions_combo)
        self.load_failed.connect(lambda msg: self.show_error_message("Ошибка загрузки данных", msg))
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
        self.ui.theme_selected.connect(self.on_theme_selected)
        self.ui.open_themes_folder_clicked.connect(self.on_open_themes_folder)
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
        self.ui.mods_widget.install_requested.connect(self.on_mod_install_requested)
        self.ui.mods_target_version_changed.connect(self.on_version_selected_for_mods)

    @pyqtSlot(str)
    def on_theme_selected(self, key):
        if self.theme_manager.set_theme(key):
            self.ui.apply_theme()
            self.set_discord_presence("Сменил тему лаунчера", "", "settings")

    @pyqtSlot()
    def on_open_themes_folder(self):
        d = self.theme_manager.user_dir()
        if not d:
            return
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))

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
                if self.isVisible():
                    self.versions_loaded.emit(online_versions_info)
            except Exception as e:
                if self.isVisible():
                    self.load_failed.emit(str(e))

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
                    self.artifact_data[version_tag] = version_info.get('artifact_data')
        if self.ui.version_combo.count() > 1 and self.ui.version_combo.itemText(0) == "Получение версий...":
            self.ui.version_combo.removeItem(0)
        if self.ui.version_combo.count() > 0:
            self.ui.version_combo.setCurrentIndex(0)
        self.ui.download_info_label.setText("")

        user_versions_only = self.version_manager.get_user_versions()
        current_version = self.ui.version_combo.currentText()
        if self.ui.FL_MODS.isVisible():
            self.ui.set_available_versions(user_versions_only, current_version)

        if current_version and current_version != "Получение версий...":
            installed = self.get_installed_mods_for_version(current_version)
            self.ui.update_mods_installed_status(installed)
            self.ui.update_version_info(current_version)

    @pyqtSlot()
    def refresh_all_data(self):
        if getattr(self, "_refresh_in_progress", False):
            return
        self._refresh_in_progress = True
        QTimer.singleShot(150, self._do_refresh_all_data)

    def _do_refresh_all_data(self):
        self._refresh_in_progress = False
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
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
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
        worker = None
        if hasattr(self, 'download_worker') and self.download_worker.isRunning():
            worker = self.download_worker
        elif hasattr(self, 'install_worker') and self.install_worker.isRunning():
            worker = self.install_worker

        if worker is None:
            return

        reply = QMessageBox.question(
            self, 'Отмена загрузки',
            'Вы действительно хотите отменить загрузку?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            worker.cancel()
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
            self.ui.mods_widget.stop()
            self.ui.hide_flmods()
            self.set_discord_presence("Просматривает главную страницу", "", "home")
        else:
            self.ui.show_flmods()
            self.set_discord_presence("Просматривает FLMODS", "", "mods")
            user_versions = self.version_manager.get_user_versions()
            current_version = self.ui.version_combo.currentText()
            self.ui.mods_widget.start()
            self.ui.set_available_versions(user_versions, current_version)
            if current_version and current_version != "Получение версий...":
                installed = self.get_installed_mods_for_version(current_version)
                self.ui.update_mods_installed_status(installed)
                self.ui.update_version_info(current_version)

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
        ui = self.ui
        settings = self.settings
        artifacts = settings.get("artifacts", {})

        ui.refresh_themes_combo()
        ui.update_discord_button_style(settings.get("discord_rpc_enabled", True))

        if getattr(ui, "additional_args_input", None) is not None:
            ui.additional_args_input.blockSignals(True)
            ui.additional_args_input.setText(
                settings.get("launch_params", {}).get("additional_args", "")
            )
            ui.additional_args_input.blockSignals(False)

        ui.update_artifacts_button_style(artifacts.get("enabled", False))

        if getattr(ui, "artifacts_count_spin", None) is not None:
            ui.artifacts_count_spin.blockSignals(True)
            ui.artifacts_count_spin.setValue(artifacts.get("max_count", 1))
            ui.artifacts_count_spin.blockSignals(False)

        if getattr(ui, "artifacts_count_group", None) is not None:
            ui.artifacts_count_group.setVisible(artifacts.get("enabled", False))

        if getattr(ui, "github_token_input", None) is not None:
            ui.github_token_input.blockSignals(True)
            ui.github_token_input.setText(settings.get("github_token", ""))
            ui.github_token_input.blockSignals(False)

        self.update_token_status()

        if getattr(ui, "repos_layout", None) is not None:
            ui.load_github_repositories(settings.get("github_repos", []))

        if hasattr(ui, "windows_group") and self.settings_manager.system == 'win32':
            ui.windows_group.setVisible(artifacts.get("enabled", False))
            windows = artifacts.get("windows", {})
            if hasattr(ui, "msvc_checkbox"):
                ui.msvc_checkbox.blockSignals(True)
                ui.msvc_checkbox.setChecked(windows.get("msvc", False))
                ui.msvc_checkbox.blockSignals(False)
            if hasattr(ui, "clang_checkbox"):
                ui.clang_checkbox.blockSignals(True)
                ui.clang_checkbox.setChecked(windows.get("clang", True))
                ui.clang_checkbox.blockSignals(False)

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
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
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
        try:
            self.ui.mods_widget.stop()
        except Exception:
            pass
        self.discord_rpc.close()
        self.version_manager.shutdown()
        self.thread_manager.shutdown(timeout=3)
        event.accept()

    @pyqtSlot(int, str, str, str)
    def on_mod_install_requested(self, content_id, content_name, version_number, content_type):
        target_version = self.ui.mods_version_combo.currentText()
        if not target_version or target_version == "Получение версий...":
            self.show_error_message("Ошибка", "Сначала выберите версию VoxelCore для установки.")
            return
        version_folder = self.version_manager.app_data_path / target_version
        if not version_folder.exists():
            self.show_error_message(
                "Ошибка",
                f"Версия {target_version} не установлена. Установите её перед установкой контента."
            )
            return

        self.ui.download_info_label.setText(f"Установка {content_name}...")
        self.ui.progress_bar.setValue(0)
        self.ui.set_cancel_button_visible(True)
        self.ui.cancel_button.setEnabled(True)

        self.install_worker = InstallWorker(
            content_id,
            content_name,
            version_number,
            content_type,
            target_version,
            str(self.settings_manager.downloads_path),
            str(self.version_manager.app_data_path)
        )
        self.install_worker.install_progress.connect(self._on_install_progress)
        self.install_worker.install_finished.connect(self._on_install_finished)
        self.install_worker.start()

    @pyqtSlot(int, str)
    def _on_install_progress(self, value, text):
        self.ui.progress_bar.setValue(value)
        self.ui.download_info_label.setText(text)

    @pyqtSlot(bool, str, str, str)
    def _on_install_finished(self, success, message, content_name, core_version):
        self.ui.set_cancel_button_visible(False)
        self.ui.progress_bar.setValue(0)
        self.ui.download_info_label.setText("")

        if success:
            installed = self.get_installed_mods_for_version(core_version)
            self.ui.update_mods_installed_status(installed)
            self.show_info_message("Успешно", message)
        else:
            self.show_error_message("Ошибка установки", message)

    def get_installed_mods_for_version(self, core_version):
        core_version_folder = self.version_manager.app_data_path / core_version
        installed = set()
        content_folder = core_version_folder / "content"
        if content_folder.exists():
            for item in content_folder.iterdir():
                if item.is_dir() and item.name != "disabled":
                    installed.add(item.name)
        disabled_folder = content_folder / "disabled"
        if disabled_folder.exists():
            for item in disabled_folder.iterdir():
                if item.is_dir():
                    installed.add(item.name)
        worlds_folder = core_version_folder / "worlds"
        if worlds_folder.exists():
            for item in worlds_folder.iterdir():
                if item.is_dir():
                    installed.add(item.name)
        return installed

    @pyqtSlot(str)
    def on_version_selected_for_mods(self, version):
        if version and version != "Получение версий...":
            installed = self.get_installed_mods_for_version(version)
            self.ui.update_mods_installed_status(installed)
            self.ui.update_version_info(version)
        else:
            self.ui.update_version_info("")