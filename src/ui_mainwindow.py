import sys
import threading
from pathlib import Path

from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import QUrl

from ui_components import UIComponents
from discord_rpc import DiscordRPC
from version_manager import VersionManager
from download_manager import DownloadManager
from settings_manager import SettingsManager
from utils import resource_path, VERSION


class FLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings
        self.version_manager = VersionManager(self.settings_manager)
        self.download_manager = DownloadManager(self.version_manager)
        self.discord_rpc = DiscordRPC(self.settings_manager)
        
        self.ui = UIComponents(self)
        self.setup_ui()
        
        self.load_versions()
        self.ui.set_username_from_config()
        
        if self.settings.get("discord_rpc_enabled", True):
            self.connect_to_discord()
            self.set_discord_presence("Просматривает главную страницу", "")
    
    def setup_ui(self):
        self.setGeometry(100, 100, 1100, 650)
        self.setFixedSize(1100, 650)
        self.setWindowTitle(f'FLauncher {VERSION}')
        
        icon_path = resource_path('ui/icon.ico')
        self.setWindowIcon(QIcon(icon_path))
        
        self.ui.setup_all()
    
    def connect_to_discord(self):
        self.discord_rpc.connect()
    
    def set_discord_presence(self, details, state, small_image=None):
        display_state = f"@{self.ui.input_field.text()}" if self.ui.input_field.text() else "Гость"
        self.discord_rpc.set_presence(details, display_state, small_image)
    
    def load_versions(self):
        self.ui.version_combo.clear()
        self.ui.version_combo.addItem("Получение версий...")
        
        user_versions = self.version_manager.get_user_versions()
        for version in user_versions:
            self.ui.version_combo.addItem(version)
        
        def load_online():
            try:
                online_versions = self.version_manager.get_all_online_versions()
                
                current_items = [self.ui.version_combo.itemText(i) 
                            for i in range(self.ui.version_combo.count())]
                
                added_versions = []
                for version in online_versions:
                    if version not in current_items and version not in added_versions:
                        self.ui.version_combo.addItem(version)
                        added_versions.append(version)
                
                if self.ui.version_combo.count() > 1 and self.ui.version_combo.itemText(0) == "Получение версий...":
                    self.ui.version_combo.removeItem(0)
                
                if self.ui.version_combo.count() > 0:
                    self.ui.version_combo.setCurrentIndex(0)
                    
            except Exception as e:
                print(f"Ошибка загрузки версий: {e}")
        
        threading.Thread(target=load_online, daemon=True).start()
        
        if user_versions and self.ui.version_combo.count() > 1:
            if self.ui.version_combo.itemText(0) != "Получение версий...":
                self.ui.version_combo.setCurrentIndex(0)
    
    def on_text_changed(self, text):
        self.version_manager.update_username_in_config(
            text,
            self.ui.version_combo.currentText()
        )
    
    def on_version_changed(self, index):
        if index >= 0:
            self.ui.set_username_from_config()
    
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
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
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
    
    def download_version(self, version_tag):
        def update_progress(value, text):
            self.ui.progress_bar.setValue(value)
            self.ui.download_info_label.setText(text)
        
        success, message = self.download_manager.download_and_extract_version(
            version_tag,
            update_progress
        )
        
        if success:
            self.show_info_message("Успешно!", message)
            self.refresh_versions()
        else:
            self.show_error_message("Ошибка", message)
        
        self.ui.progress_bar.setValue(0)
        self.ui.download_info_label.setText("")
    
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
    
    def refresh_versions(self):
        self.load_versions()
    
    def on_flm_button_click(self):
        if self.ui.FL_MODS.isVisible():
            self.ui.hide_flmods()
        else:
            self.ui.show_flmods()
            self.set_discord_presence("Просматривает FLMODS", "", "mods")
    
    def open_versions_folder(self):
        url = QUrl.fromLocalFile(str(self.version_manager.app_data_path))
        QDesktopServices.openUrl(url)
    
    def open_settings(self):
        if self.ui.settings_panel.isVisible():
            self.ui.hide_settings()
            self.set_discord_presence("Просматривает главную страницу", "", "home")
        else:
            self.ui.show_settings()
            self.set_discord_presence("В настройках", "", "settings")
    
    def show_error_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
    
    def show_info_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()
    
    def add_github_repository(self):
        from PyQt5.QtWidgets import QInputDialog
        
        repo, ok = QInputDialog.getText(
            self, 
            'Добавить репозиторий', 
            'Введите owner/repo (например: MihailRis/voxelcore):'
        )
        
        if ok and repo:
            if len(repo.split('/')) != 2:
                self.show_error_message("Ошибка", "Неверный формат. Используйте owner/repo")
                return
            
            if self.settings_manager.add_github_repo(repo):
                self.ui.add_repository_to_list(repo)
                self.load_versions()
    
    def remove_github_repository(self, repo):
        if self.settings_manager.remove_github_repo(repo):
            self.ui.load_github_repositories()
            self.load_versions()
    
    def toggle_discord_rpc(self):
        enabled = self.settings_manager.toggle_discord_rpc()
        if enabled:
            self.discord_rpc.connect()
            self.set_discord_presence("Просматривает главную страницу", "")
        else:
            self.discord_rpc.close()
        self.ui.update_discord_button_style(enabled)
    
    def update_launch_params(self, text):
        self.settings_manager.update_launch_params(text)
    
    def closeEvent(self, event):
        self.discord_rpc.close()
        event.accept()