# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import zipfile
import shutil
import requests
import markdown
import time
import threading
import asyncio
import toml
import re
import json
from pathlib import Path
from datetime import datetime
from pypresence import Presence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel,
    QSpacerItem, QSizePolicy, QFrame, QPushButton, QComboBox, QMessageBox,
    QHBoxLayout, QProgressBar, QTextBrowser, QLineEdit, QInputDialog,
    QCheckBox, QSpinBox
)
from PyQt5.QtGui import (
    QPalette, QBrush, QImage, QDesktopServices, QIcon, QFont
)
from PyQt5.QtCore import Qt, QUrl, QSize, QCoreApplication, QTimer

version = "0.4.0"


def resource_path(relative_path):
    try:
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    except Exception:
        return relative_path

class FLauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.create_app_data_directory()
        self.load_settings()

        self.setup_ui()
        
        # Discord RPC
        self.discord_presence = None
        self.client_id = "1143147014226444338"
        self.connect_to_discord()
        self.set_discord_presence("Просматривает главную страницу", f"@{self.input_field.text()}" if self.input_field.text() else "Гость")
        
        self.load_versions()
        self.set_username_from_config()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start(3600000)  # Проверка обновлений лаунчера каждый час
    
    def setup_ui(self):
        """Настройка основного интерфейса"""
        self.setGeometry(100, 100, 1100, 650)
        self.setFixedSize(1100, 650)
        self.setWindowTitle(f'FLauncher {version}')
    
        icon_path = resource_path('ui/icon.ico')
        self.setWindowIcon(QIcon(icon_path))
        
        self.set_background()
        
        self.add_release_panel()
        self.add_info_panel()
        self.add_settings_panel()
        self.add_fl_mods_panel()
        self.add_blue_bar()

    def connect_to_discord(self):
        """Подключение к Discord RPC"""
        try:
            if self.settings.get("discord_rpc_enabled", True):
                self.discord_presence = Presence(self.client_id)
                self.discord_presence.connect()
        except Exception as e:
            print(f"Ошибка при подключении к Discord: {e}")
            self.discord_presence = None

    def set_discord_presence(self, details, state):
        """Установка статуса Discord"""
        if self.discord_presence:
            username = self.input_field.text()
            display_state = f"@{username}" if username else "Гость"
            threading.Thread(
                target=self.update_presence_async,
                args=(details, display_state),
                daemon=True
            ).start()

    def update_presence_async(self, details, state):
        """обновление статуса Discord"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if self.discord_presence:
                self.discord_presence.update(
                    details=details,
                    state=state,
                    start=time.time(),
                    large_image="icon",
                    large_text="FLauncher"
                )
        except Exception as e:
            print(f"Ошибка при обновлении статуса Discord: {e}")

    def set_background(self):
        """фоновое изображение"""
        self.setAutoFillBackground(True)
        palette = self.palette()
        image = QImage(resource_path('ui/background.png'))
        brush = QBrush(image)
        palette.setBrush(QPalette.Background, brush)
        self.setPalette(palette)

    def add_blue_bar(self):
        """нижняя панель управления"""
        blue_bar = QWidget(self)
        blue_bar.setGeometry(0, self.height() - 90, self.width(), 90)
        blue_bar.setStyleSheet("background-color: rgba(113, 169, 76, 0.9);")

        # Поле ввода ника
        self.input_field = QLineEdit(blue_bar)
        self.input_field.setGeometry(10, 20, 200, 60)
        self.input_field.setStyleSheet("""
            background-color: white; 
            color: black; 
            font-size: 18px; 
            font-weight: bold;
            border-radius: 5px;
            padding: 5px;
        """)
        self.input_field.setPlaceholderText("Введите ник...")
        self.input_field.textChanged.connect(self.on_text_changed)

        self.version_combo = QComboBox(blue_bar)
        self.version_combo.setGeometry(220, 20, 200, 60)
        self.version_combo.setStyleSheet("""
            background-color: white; 
            color: black; 
            font-size: 18px; 
            font-weight: bold;
            border-radius: 5px;
        """)
        self.version_combo.addItem("Получение версий...")
        self.version_combo.currentIndexChanged.connect(self.on_version_changed)

        self.progress_bar = QProgressBar(blue_bar)
        self.progress_bar.setGeometry(10, 0, self.width() - 20, 20)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 10px;
            }
        """)

        self.download_info_label = QLabel("0 KB / 0 KB, Скорость: 0 KB/s", blue_bar)
        self.download_info_label.setGeometry(10, 0, self.width() - 20, 20)
        self.download_info_label.setStyleSheet("font-size: 12px; color: black;")
        self.download_info_label.setAlignment(Qt.AlignCenter)

        self.play_button = QPushButton("Войти в игру", blue_bar)
        self.play_button.setGeometry(430, 20, 250, 60)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(236, 193, 63); 
                color: white; 
                font-size: 18px; 
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgb(246, 203, 73);
            }
            QPushButton:pressed {
                background-color: rgb(226, 183, 53);
            }
        """)
        self.play_button.clicked.connect(self.on_play_button_click)

        icon_flm = QIcon(resource_path("ui/FLM.png"))
        self.flm_button = QPushButton(blue_bar)
        self.flm_button.setIcon(icon_flm)
        self.flm_button.setIconSize(QSize(60, 60))
        self.flm_button.setGeometry(835, 20, 60, 60)
        self.flm_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
        """)
        self.flm_button.clicked.connect(self.on_flm_button_click)

        icon_reload = QIcon(resource_path("ui/reload.png"))
        self.reload_button = QPushButton(blue_bar)
        self.reload_button.setIcon(icon_reload)
        self.reload_button.setIconSize(QSize(30, 30))
        self.reload_button.setGeometry(895, 20, 60, 60)
        self.reload_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
        """)
        self.reload_button.clicked.connect(self.refresh_versions)

        icon_folder = QIcon(resource_path("ui/folder.png"))
        self.folder_button = QPushButton(blue_bar)
        self.folder_button.setIcon(icon_folder)
        self.folder_button.setIconSize(QSize(30, 30))
        self.folder_button.setGeometry(965, 20, 60, 60)
        self.folder_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
        """)
        self.folder_button.clicked.connect(self.open_versions_folder)

        icon_settings = QIcon(resource_path("ui/settings.png"))
        self.settings_button = QPushButton(blue_bar)
        self.settings_button.setIcon(icon_settings)
        self.settings_button.setIconSize(QSize(30, 30))
        self.settings_button.setGeometry(1035, 20, 60, 60)
        self.settings_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
                outline: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
        """)
        self.settings_button.clicked.connect(self.open_settings)

    def add_release_panel(self):
        """панель с релизами"""
        self.release_panel = QWidget(self)
        self.release_panel.setGeometry(20, 40, 700, self.height() - 130)
        self.release_panel.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
        """)

        self.release_layout = QVBoxLayout(self.release_panel)
        self.release_layout.setContentsMargins(15, 15, 15, 15)
        self.release_layout.setSpacing(15)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(self.release_panel)
        self.scroll_area.setGeometry(20, 40, 800, self.height() - 130)
        self.scroll_area.setWidgetResizable(True)
        
        self.release_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(200, 200, 200, 0.5);
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 100, 100, 0.5);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.get_github_releases()

    def add_info_panel(self):
        """информационная панель"""
        info_panel = QWidget(self)
        info_panel.setGeometry(830, 0, 250, self.height() - 90)
        info_panel.setStyleSheet("""
            background-color: rgba(90, 171, 215, 0.9);
            border-top-right-radius: 10px;
        """)

        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(15)

        title_label = QLabel('FLAUNCHER', info_panel)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 30px; 
            font-weight: bold; 
            color: white;
            margin-bottom: 5px;
        """)
        info_layout.addWidget(title_label)

        subtitle_label = QLabel('ЛАУНЧЕР ДЛЯ VOXELCORE', info_panel)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: normal; 
            color: white;
            margin-bottom: 15px;
        """)
        info_layout.addWidget(subtitle_label)

        button_style = """
            QPushButton {
                background-color: rgb(62, 148, 182); 
                font-size: 18px; 
                color: white; 
                padding: 10px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgb(72, 158, 192);
            }
            QPushButton:pressed {
                background-color: rgb(52, 138, 172);
            }
        """

        button_voxel = QPushButton("VoxelWorld", info_panel)
        button_voxel.setStyleSheet(button_style)
        button_voxel.setFixedHeight(40)
        button_voxel.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://voxelworld.ru/profile/84")))
        info_layout.addWidget(button_voxel)

        button_freshlend = QPushButton("FreshLend Studio", info_panel)
        button_freshlend.setStyleSheet(button_style)
        button_freshlend.setFixedHeight(40)
        button_freshlend.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://freshlend.github.io")))
        info_layout.addWidget(button_freshlend)

        version_label = QLabel(f'Версия: {version}', info_panel)
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            font-size: 14px; 
            color: white;
            margin-top: 20px;
        """)
        info_layout.addWidget(version_label)

        info_layout.addStretch(1)

    def add_settings_panel(self):
        """панель настроек"""
        self.settings_background = QWidget(self)
        self.settings_background.setGeometry(0, 0, 1100, self.height())
        self.settings_background.setStyleSheet("background-color: rgba(240, 240, 240, 0.95);")

        self.settings_panel = QWidget(self)
        self.settings_panel.setGeometry(0, 0, 1100, self.height() - 90)
        self.settings_panel.setStyleSheet("background-color: white;")

        self.blue_strip = QWidget(self.settings_panel)
        self.blue_strip.setGeometry(0, 0, self.settings_panel.width(), 50)
        self.blue_strip.setStyleSheet("background-color: #0086c7;")

        blue_layout = QHBoxLayout(self.blue_strip)
        blue_layout.setContentsMargins(20, 0, 20, 0)
        blue_layout.setSpacing(10)

        settings_label = QLabel('Настройки', self.blue_strip)
        settings_label.setAlignment(Qt.AlignCenter)
        settings_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
        """)
        blue_layout.addWidget(settings_label)

        layout = QVBoxLayout(self.settings_panel)
        layout.setContentsMargins(30, 60, 30, 30)
        layout.setSpacing(20)

        discord_group = QWidget()
        discord_layout = QVBoxLayout(discord_group)
        
        discord_label = QLabel('Discord RPC', discord_group)
        discord_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        discord_layout.addWidget(discord_label)

        discord_description = QLabel(
            'Отображает информацию о вашей активности в Discord.<br>Вы можете отключить эту функцию, если она вам не нужна.',
            discord_group
        )
        discord_description.setStyleSheet("font-size: 14px; color: #555;")
        discord_description.setWordWrap(True)
        discord_layout.addWidget(discord_description)

        self.discord_toggle = QPushButton(
            'Отключить Discord RPC' if self.settings.get("discord_rpc_enabled", True) 
            else 'Включить Discord RPC', 
            discord_group
        )
        self.discord_toggle.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #7289da;
                color: white;
                border-radius: 5px;
                padding: 10px;
                border: none;
                text-align: center;
                min-width: 200px;
                max-width: 200px;
            }
            QPushButton:hover {
                background-color: #8299ea;
            }
            QPushButton:pressed {
                background-color: #6279ca;
            }
        """)
        if not self.settings.get("discord_rpc_enabled", True):
            self.discord_toggle.setStyleSheet(self.discord_toggle.styleSheet().replace(
                "#7289da", "#4caf50"
            ))
        self.discord_toggle.setFixedHeight(40)
        self.discord_toggle.clicked.connect(self.toggle_discord_rpc)
        discord_layout.addWidget(self.discord_toggle, alignment=Qt.AlignLeft)

        layout.addWidget(discord_group)

        github_group = QWidget()
        github_layout = QVBoxLayout(github_group)
        
        github_label = QLabel('GitHub Репозитории', github_group)
        github_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        github_layout.addWidget(github_label)

        github_description = QLabel(
            'Добавьте другие GitHub репозитории для загрузки версий.<br>Формат: owner/repo (например: MihailRis/VoxelEngine-Cpp)',
            github_group
        )
        github_description.setStyleSheet("font-size: 14px; color: #555;")
        github_description.setWordWrap(True)
        github_layout.addWidget(github_description)

        add_repo_button = QPushButton('Добавить репозиторий', github_group)
        add_repo_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #7289da;
                color: white;
                border-radius: 5px;
                padding: 10px;
                border: none;
                text-align: center;
                min-width: 200px;
                max-width: 200px;
            }
            QPushButton:hover {
                background-color: #8299ea;
            }
            QPushButton:pressed {
                background-color: #6279ca;
            }
        """)
        add_repo_button.setFixedHeight(40)
        add_repo_button.clicked.connect(self.add_github_repository)
        github_layout.addWidget(add_repo_button, alignment=Qt.AlignLeft)

        self.repos_scroll = QScrollArea(github_group)
        self.repos_scroll.setWidgetResizable(True)
        self.repos_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        self.repos_container = QWidget()
        self.repos_layout = QVBoxLayout(self.repos_container)
        self.repos_layout.setContentsMargins(5, 5, 5, 5)
        self.repos_layout.setSpacing(5)
        
        self.repos_scroll.setWidget(self.repos_container)
        github_layout.addWidget(self.repos_scroll)

        self.load_github_repositories()

        layout.addWidget(github_group)
        layout.addStretch(1)

        launch_params_group = QWidget()
        launch_params_layout = QVBoxLayout(launch_params_group)
        
        launch_params_label = QLabel('Параметры запуска', launch_params_group)
        launch_params_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        launch_params_layout.addWidget(launch_params_label)

        args_label = QLabel('', launch_params_group)
        launch_params_layout.addWidget(args_label)

        self.additional_args_input = QLineEdit(launch_params_group)
        self.additional_args_input.setText(self.settings["launch_params"]["additional_args"])
        self.additional_args_input.textChanged.connect(self.update_launch_params)
        launch_params_layout.addWidget(self.additional_args_input)

        layout.addWidget(launch_params_group)
        layout.addStretch(1)

        self.settings_panel.hide()
        self.settings_background.hide()

    def update_launch_params(self):
        """Обновляет параметры запуска в настройках"""
        self.settings["launch_params"] = {
            "additional_args": self.additional_args_input.text()
        }
        self.save_settings()

    def toggle_discord_rpc(self):
        """Переключение Discord RPC"""
        if self.discord_presence:
            self.discord_presence.close()
            self.discord_presence = None
            self.discord_toggle.setText('Включить Discord RPC')
            self.discord_toggle.setStyleSheet(self.discord_toggle.styleSheet().replace(
                "#7289da", "#4caf50"
            ))
            self.settings["discord_rpc_enabled"] = False
        else:
            self.connect_to_discord()
            self.set_discord_presence("Просматривает главную страницу", "By FreshGame")
            self.discord_toggle.setText('Отключить Discord RPC')
            self.discord_toggle.setStyleSheet(self.discord_toggle.styleSheet().replace(
                "#4caf50", "#7289da"
            ))
            self.settings["discord_rpc_enabled"] = True
        
        self.save_settings()

    def add_fl_mods_panel(self):
        """панель модов"""
        self.FL_MODS_background = QWidget(self)
        self.FL_MODS_background.setGeometry(0, 0, 1100, self.height())
        self.FL_MODS_background.setStyleSheet("background-color: rgba(240, 240, 240, 0.95);")

        self.FL_MODS = QWidget(self)
        self.FL_MODS.setGeometry(0, 0, 1100, self.height() - 90)
        self.FL_MODS.setStyleSheet("background-color: white;")

        self.blue_strip = QWidget(self.FL_MODS)
        self.blue_strip.setGeometry(0, 0, self.FL_MODS.width(), 40)
        self.blue_strip.setStyleSheet("background-color: #00aaff;")

        blue_layout = QHBoxLayout(self.blue_strip)
        blue_layout.setContentsMargins(10, 0, 10, 0)
        blue_layout.setSpacing(10)

        FL_MODS_label = QLabel('FLMODS', self.blue_strip)
        FL_MODS_label.setAlignment(Qt.AlignCenter)
        FL_MODS_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: white;
        """)
        blue_layout.addWidget(FL_MODS_label)

        layout = QVBoxLayout(self.FL_MODS)
        layout.setContentsMargins(20, 50, 20, 20)
        layout.setSpacing(20)

        text_browser = QTextBrowser(self.FL_MODS)
        text_browser.setAlignment(Qt.AlignTop)
        text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: none;
                font-size: 14px;
                color: #333;
            }
            a {
                color: #0066cc;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        """)
        text_browser.setText('''
            <div style="line-height: 1.6;">
                <p style="font-size: 16px; color: #222;">
                    Страницы модов пока что нет, появится когда-нибудь, это будет через неизвестное время.
                </p>
            </div>
        ''')
        text_browser.setOpenExternalLinks(True)

        layout.addWidget(text_browser)

        self.FL_MODS.hide()
        self.FL_MODS_background.hide()

    def on_text_changed(self):
        """Обработка изменения текста в поле ввода ника"""
        input_text = self.input_field.text()
        self.update_username_in_config(input_text)

    def on_version_changed(self):
        """Обработка изменения выбранной версии"""
        self.set_username_from_config()

    def set_username_from_config(self):
        """Установка ника"""
        version = self.version_combo.currentText()
        if version == "Получение версий...":
            return
            
        config_file_path = self.app_data_path / version / "config" / "multiplayer" / "config.toml"
        if not config_file_path.exists():
            self.input_field.setPlaceholderText("Введите ник...")
            return
            
        try:
            config = toml.load(config_file_path)
            if "profiles" in config and "current" in config["profiles"]:
                username = config["profiles"]["current"].get("username", "")
                if username:
                    self.input_field.setText(username)
                else:
                    self.input_field.setPlaceholderText("Введите ник...")
        except Exception as e:
            print(f"Ошибка при чтении файла config.toml: {e}")
            self.input_field.setPlaceholderText("Введите ник...")

    def update_username_in_config(self, username):
        """Обновление ника"""
        version = self.version_combo.currentText()
        if version == "Получение версий...":
            return
            
        config_file_path = self.app_data_path / version / "config" / "multiplayer" / "config.toml"
        if not config_file_path.exists():
            return
            
        try:
            config = toml.load(config_file_path)
            if "profiles" in config and "current" in config["profiles"]:
                config["profiles"]["current"]["username"] = username
                with open(config_file_path, "w", encoding="utf-8") as config_file:
                    toml.dump(config, config_file)
        except Exception as e:
            print(f"Ошибка при обновлении файла config.toml: {e}")

    def on_play_button_click(self):
        """Обработка кнопки 'Войти в игру'"""
        selected_version = self.version_combo.currentText()
        if selected_version == "Получение версий...":
            self.show_info_message("Выбор версии", "Пожалуйста, выберите версию для игры.")
            return
            
        version_folder = self.app_data_path / selected_version
        
        if not version_folder.exists():
            reply = QMessageBox.question(
                self, 'Версия не найдена',
                f'Версия {selected_version} не установлена. Хотите скачать её сейчас?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.download_and_extract_version(selected_version)
            return
            
        exe_files = [
            f for f in version_folder.iterdir() 
            if f.is_file() and f.suffix.lower() == ".exe" and f.stem.lower() != "vctest"
        ]
        
        if exe_files:
            exe_to_launch = exe_files[0]
            self.launch_game(exe_to_launch, version_folder)
        else:
            self.show_error_message(
                "Ошибка", 
                f"Не найден исполняемый файл в папке {selected_version}. "
                "Попробуйте переустановить эту версию."
            )

    def refresh_versions(self):
        """Обновление списка версий"""
        self.version_combo.clear()
        self.version_combo.addItem("Получение версий...")
        self.load_versions()

    def on_flm_button_click(self):
        """Обработка кнопки FLMODS"""
        if self.FL_MODS.isVisible():
            self.FL_MODS.hide()
            self.FL_MODS_background.hide()
            self.set_discord_presence("Просматривает главную страницу", "By FreshGame")
        else:
            self.FL_MODS.show()
            self.FL_MODS_background.show()
            self.set_discord_presence("Просматривает FLMODS", "By FreshGame")

    def open_versions_folder(self):
        """Открытие папки с версиями"""
        url = QUrl.fromLocalFile(str(self.app_data_path))
        QDesktopServices.openUrl(url)

    def open_settings(self):
        """Открытие панели настроек"""
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
            self.settings_background.hide()
            self.set_discord_presence("Просматривает главную страницу", "By FreshGame")
        else:
            self.settings_panel.show()
            self.settings_background.show()
            self.set_discord_presence("В настройках", "By FreshGame")

    def show_error_message(self, title, message):
        """сообщение об ошибке"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: black;
            }
        """)
        msg.exec_()

    def show_info_message(self, title, message):
        """информационное сообщение"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: black;
            }
        """)
        msg.exec_()

    def launch_game(self, voxel_core_path, working_directory):
        """Запуск игры"""
        try:
            username = self.input_field.text()
            display_name = f"@{username}" if username else "Гость"
            self.set_discord_presence(
                f"Играет в {self.version_combo.currentText()}",
                display_name
            )
            
            launch_params = [str(voxel_core_path)]
            
            if self.settings["launch_params"]["additional_args"]:
                launch_params.extend(self.settings["launch_params"]["additional_args"].split())
            
            subprocess.Popen(
                launch_params,
                cwd=str(working_directory),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
        except Exception as e:
            error_msg = f"Не удалось запустить игру: {str(e)}"
            self.show_error_message("Ошибка запуска", error_msg)
            
            self.set_discord_presence(
                "Просматривает главную страницу",
                f"@{self.input_field.text()}" if self.input_field.text() else "Гость"
            )

    def download_and_extract_version(self, version_tag):
        """Скачивание и распаковка версии"""
        self.download_start_time = time.time()
        
        repo = self.find_repo_for_version(version_tag)
        if not repo:
            self.show_error_message(
                "Ошибка", 
                f"Не удалось определить репозиторий для версии {version_tag}"
            )
            return
        
        api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version_tag}"
        
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                release_data = response.json()

                file_url = None
                for asset in release_data.get('assets', []):
                    if 'win64.zip' in asset['name']:
                        file_url = asset['browser_download_url']
                        break
                
                if file_url:
                    self.downloads_path.mkdir(parents=True, exist_ok=True)
                    
                    zip_path = self.downloads_path / f"{release_data['tag_name']}_win64.zip"
                    
                    self.progress_bar.setValue(0)
                    self.download_info_label.setText("Подготовка к загрузке...")
                    QCoreApplication.processEvents()
                    
                    self._download_file(file_url, zip_path)
                    
                    self.extract_zip(zip_path, version_tag)
                    
                    self.show_info_message(
                        "Успешно!", 
                        f"Версия {version_tag} успешно скачана и установлена!"
                    )
                    
                    self.refresh_versions()
                else:
                    self.show_error_message(
                        "Ошибка", 
                        f"Не найден файл с win64.zip в релизе {version_tag}."
                    )
            else:
                self.show_error_message(
                    "Ошибка", 
                    f"Не удалось получить информацию о релизе для версии {version_tag}. "
                    f"Код ошибки: {response.status_code}"
                )
        
        except Exception as e:
            self.show_error_message(
                "Ошибка", 
                f"Ошибка при скачивании или распаковке: {e}"
            )
        finally:
            self.progress_bar.setValue(0)
            self.download_info_label.setText("")

    def find_repo_for_version(self, version_tag):
        main_repo = "MihailRis/VoxelEngine-Cpp"
        if self.is_version_in_repo(version_tag, main_repo):
            return main_repo
        
        for repo in self.settings.get("github_repos", []):
            if self.is_version_in_repo(version_tag, repo):
                return repo
        
        return None

    def is_version_in_repo(self, version_tag, repo):
        try:
            versions = self.get_github_repo_versions(repo)
            return any(v[0] == version_tag for v in versions)
        except Exception as e:
            print(f"Ошибка при проверке версии в репозитории {repo}: {e}")
            return False

    def _download_file(self, file_url, zip_path):
        """Скачивание файла"""
        response = requests.get(file_url, stream=True)
        
        if response.status_code == 200:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0
            chunk_size = 1024 * 8

            if zip_path.exists():
                zip_path.unlink()
            
            with open(zip_path, 'wb') as f:
                for data in response.iter_content(chunk_size=chunk_size):
                    if data:
                        downloaded_size += len(data)
                        f.write(data)

                        progress = int((downloaded_size / total_size) * 100)
                        self.progress_bar.setValue(progress)
                        elapsed_time = time.time() - self.download_start_time
                        speed = (downloaded_size / 1024) / elapsed_time if elapsed_time > 0 else 0
                        remaining_size = total_size - downloaded_size
                        remaining_time = remaining_size / (speed * 1024) if speed > 0 else 0
                        remaining_time_str = time.strftime("%H:%M:%S", time.gmtime(remaining_time))
                        downloaded_size_mb = downloaded_size / (1024 * 1024)
                        total_size_mb = total_size / (1024 * 1024)
                        self.download_info_label.setText(
                            f"{downloaded_size_mb:.2f} MB / {total_size_mb:.2f} MB, "
                            f"Скорость: {speed:.2f} KB/s, Осталось: {remaining_time_str}"
                        )
                        
                        QCoreApplication.processEvents()
        else:
            raise Exception(f"Не удалось скачать файл. Код ошибки: {response.status_code}")

    def extract_zip(self, zip_path, version_tag):
        """Распаковка ZIP архива"""
        try:
            extraction_path = self.app_data_path / version_tag
            extraction_path.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                self.download_info_label.setText("Распаковка архива...")
                QCoreApplication.processEvents()
            
                zip_ref.extractall(extraction_path)
                zip_files = zip_ref.namelist()
                if zip_files:
                    first_file = zip_files[0]
                    if '/' in first_file:
                        folder_in_zip = first_file.split('/')[0]
                        folder_to_move = extraction_path / folder_in_zip
                        if folder_to_move.exists():
                            for item in folder_to_move.iterdir():
                                shutil.move(str(item), extraction_path / item.name)
                            folder_to_move.rmdir()
            
            if zip_path.exists():
                zip_path.unlink()
            
            self.create_config_toml(extraction_path)
            
        except Exception as e:
            raise Exception(f"Ошибка при распаковке архива: {e}")

    def create_config_toml(self, extraction_path):
        try:
            config_path = extraction_path / 'config' / 'multiplayer' / 'config.toml'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_content = """config_version = 0

[multiplayer]
servers = []

[profiles]
profiles = ["Player"]

[profiles.current]
username = "FLauncher_Player"
"""
            if not config_path.exists():
                with open(config_path, 'w', encoding='utf-8') as config_file:
                    config_file.write(config_content)
        except Exception as e:
            print(f"Не удалось создать config.toml: {e}")

    def create_app_data_directory(self):
        """Создание необходимых директорий"""
        user_folder = Path(os.path.expanduser("~"))
        self.app_data_path = user_folder / "AppData" / "Roaming" / "com.flauncher.app" / "FLauncher" / "VE" / "versions"
        self.downloads_path = user_folder / "AppData" / "Roaming" / "com.flauncher.app" / "FLauncher" / "VE" / "downloads"
        self.settings_path = user_folder / "AppData" / "Roaming" / "com.flauncher.app" / "FLauncher" / "settings.json"
        
        self.app_data_path.mkdir(parents=True, exist_ok=True)
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        if not self.settings_path.exists():
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_path, 'w') as f:
                json.dump({
                    "github_repos": [],
                    "discord_rpc_enabled": True,
                    "launch_params": {
                        "additional_args": ""
                    }
                }, f, indent=4)

    def load_settings(self):
        """Загрузка настроек из файла"""
        try:
            with open(self.settings_path, 'r') as f:
                self.settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {
                "github_repos": [],
                "discord_rpc_enabled": True
            }

    def save_settings(self):
        """Сохранение настроек в файл"""
        with open(self.settings_path, 'w') as f:
            json.dump(self.settings, f)

    def load_versions(self):
        """Загрузка списка версий с GitHub"""
        self.version_combo.clear()
        self.version_combo.addItem("Получение версий...")
        QCoreApplication.processEvents()

        all_versions = []
        
        main_repo_versions = self.get_github_repo_versions("MihailRis/VoxelEngine-Cpp")
        all_versions.extend(main_repo_versions)
        
        for repo in self.settings.get("github_repos", []):
            try:
                repo_versions = self.get_github_repo_versions(repo)
                all_versions.extend(repo_versions)
            except Exception as e:
                print(f"Ошибка при загрузке версий из репозитория {repo}: {e}")
        
        user_versions = self.get_user_versions()
        
        self.version_combo.clear()
        added_versions = set()
        
        for version in user_versions:
            if version not in added_versions:
                self.version_combo.addItem(version)
                added_versions.add(version)
        
        for version, _ in all_versions:
            if version not in added_versions:
                self.version_combo.addItem(version)
                added_versions.add(version)
        
        if user_versions or all_versions:
            self.version_combo.setCurrentIndex(0)
        else:
            self.version_combo.addItem("Версии не найдены")

    def get_github_repo_versions(self, repo):
        """Получение версий из GitHub репозитория"""
        url = f"https://api.github.com/repos/{repo}/releases?per_page=1000"
        response = requests.get(url)
        if response.status_code == 200:
            releases = response.json()
            
            filtered_releases = [
                (release['tag_name'], repo) 
                for release in releases 
                if isinstance(release, dict) and 'tag_name' in release
            ]
            
            return filtered_releases
        else:
            print(f"Ошибка при загрузке версий из {repo}: {response.status_code}")
            return []

    def check_for_updates(self):
        """Проверка обновлений лаунчера"""
        try:
            response = requests.get(
                "https://api.github.com/repos/FreshLend/FLauncher/releases/latest"
            )
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release['tag_name']
                
                if latest_version != version:
                    download_url = self.find_download_link(latest_release['body'])
                    
                    if download_url:
                        reply = QMessageBox.question(
                            self, 'Доступно обновление',
                            f'Доступна новая версия лаунчера {latest_version}. Хотите скачать её сейчас?',
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                        )
                        
                        if reply == QMessageBox.Yes:
                            QDesktopServices.openUrl(QUrl(download_url))
                    else:
                        QDesktopServices.openUrl(QUrl(latest_release['html_url']))
        
        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")
            self.show_error_message("Ошибка", "Не удалось проверить обновления")

    def find_download_link(self, markdown_text):
        import re
        match = re.search(r'\[Скачать\]\((https?://[^\s]+)\)', markdown_text)
        return match.group(1) if match else None

    def version_to_tuple(self, version_str):
        version_parts = re.findall(r'\d+', version_str)
        return tuple(map(int, version_parts))

    def get_user_versions(self):
        """Получение списка установленных версий"""
        user_versions = []
        if self.app_data_path.exists():
            for folder in self.app_data_path.iterdir():
                if folder.is_dir():
                    version_tuple = self.version_to_tuple(folder.name)
                    user_versions.append((folder.name, version_tuple))
        
        user_versions.sort(key=lambda x: x[1], reverse=True)
        return [version[0] for version in user_versions]
    
    def load_github_repositories(self):
        """Загрузка списка GitHub репозиториев"""
        for i in reversed(range(self.repos_layout.count())): 
            self.repos_layout.itemAt(i).widget().setParent(None)
        
        for repo in self.settings.get("github_repos", []):
            self.add_repository_to_list(repo)

    def add_repository_to_list(self, repo):
        """Добавление репозитория в список"""
        repo_widget = QWidget()
        repo_widget.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")
        
        repo_layout = QHBoxLayout(repo_widget)
        repo_layout.setContentsMargins(10, 5, 10, 5)
        
        repo_label = QLabel(repo)
        repo_label.setStyleSheet("font-size: 14px;")
        repo_layout.addWidget(repo_label)
        
        delete_button = QPushButton("×")
        delete_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                color: white;
                background-color: #ff4444;
                border-radius: 10px;
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        delete_button.clicked.connect(lambda _, r=repo: self.remove_github_repository(r))
        repo_layout.addWidget(delete_button)
        
        self.repos_layout.addWidget(repo_widget)

    def add_github_repository(self):
        """Добавление нового GitHub репозитория"""
        repo, ok = QInputDialog.getText(
            self, 
            'Добавить репозиторий', 
            'Введите owner/repo (например: MihailRis/VoxelEngine-Cpp):'
        )
        
        if ok and repo:
            if len(repo.split('/')) != 2:
                self.show_error_message("Ошибка", "Неверный формат. Используйте owner/repo")
                return
                
            if repo not in self.settings["github_repos"]:
                self.settings["github_repos"].append(repo)
                self.save_settings()
                self.add_repository_to_list(repo)
                self.load_versions()

    def remove_github_repository(self, repo):
        """Удаление GitHub репозитория"""
        if repo in self.settings["github_repos"]:
            self.settings["github_repos"].remove(repo)
            self.save_settings()
            self.load_github_repositories()
            self.load_versions()

    def get_github_releases(self):
        """Получение списка релизов с GitHub"""
        url = "https://api.github.com/repos/MihailRis/VoxelEngine-Cpp/releases"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            releases = response.json()

            for i in reversed(range(self.release_layout.count())): 
                self.release_layout.itemAt(i).widget().setParent(None)

            for release in releases:
                if isinstance(release, dict):
                    tag_name = release.get('tag_name', '')
                    version = tag_name.replace('voxelcore', '').strip()

                    release_url = release.get('html_url', '#')

                    release_date_str = release.get('published_at', '')
                    if release_date_str:
                        try:
                            release_date = datetime.strptime(release_date_str, '%Y-%m-%dT%H:%M:%SZ')
                            release_date_formatted = release_date.strftime('%d %B %Y')
                        except ValueError:
                            release_date_formatted = "Дата неизвестна"

                    release_widget = QWidget()
                    release_widget.setStyleSheet("background-color: transparent;")
                    release_layout = QVBoxLayout(release_widget)
                    release_layout.setContentsMargins(0, 0, 0, 0)
                    release_layout.setSpacing(5)

                    header_layout = QHBoxLayout()
                    
                    version_label = QLabel(f'VoxelCore<a href="{release_url}"> {version}</a>')
                    version_label.setStyleSheet("""
                        font-weight: bold; 
                        font-size: 24px; 
                        color: black;
                        margin-bottom: 5px;
                    """)
                    version_label.setOpenExternalLinks(True)

                    date_label = QLabel(f'Дата релиза: {release_date_formatted}')
                    date_label.setStyleSheet("""
                        font-size: 12px; 
                        color: gray; 
                        margin-left: 10px;
                    """)

                    header_layout.addWidget(version_label)
                    header_layout.addWidget(date_label)
                    release_layout.addLayout(header_layout)

                    release_body = release.get('body', '')
                    html_body = markdown.markdown(release_body)
                    html_body = html_body.replace('<a', '<a target="_blank"')

                    release_info_label = QLabel()
                    release_info_label.setOpenExternalLinks(True)
                    release_info_label.setText(html_body)
                    release_info_label.setWordWrap(True)
                    release_info_label.setStyleSheet("""
                        font-weight: bold; 
                        font-size: 14px; 
                        line-height: 1.5; 
                        color: black;
                        margin-bottom: 15px;
                    """)
                    release_layout.addWidget(release_info_label)

                    separator = QFrame()
                    separator.setFrameShape(QFrame.HLine)
                    separator.setFrameShadow(QFrame.Sunken)
                    separator.setStyleSheet("""
                        background-color: rgba(0, 0, 0, 0.2); 
                        height: 1px;
                        margin: 10px 0;
                    """)
                    release_layout.addWidget(separator)

                    self.release_layout.addWidget(release_widget)

            all_releases_label = QLabel()
            all_releases_label.setText('''
                <div style="margin-top: 20px;">
                    Посмотреть весь список релизов: 
                    <a href="https://github.com/MihailRis/VoxelEngine-Cpp/releases">
                        https://github.com/MihailRis/VoxelEngine-Cpp/releases
                    </a>
                </div>
            ''')
            all_releases_label.setOpenExternalLinks(True)
            all_releases_label.setStyleSheet("""
                font-size: 16px; 
                color: black;
            """)
            self.release_layout.addWidget(all_releases_label)

            self.release_layout.addStretch(1)

        except requests.RequestException as e:
            error_label = QLabel("Не удалось загрузить релизы. Проверьте соединение с интернетом.")
            error_label.setStyleSheet("""
                font-size: 16px; 
                color: red;
                margin: 20px 0;
            """)
            self.release_layout.addWidget(error_label)

        except ValueError as e:
            error_label = QLabel("Ошибка при обработке данных.")
            error_label.setStyleSheet("""
                font-size: 16px; 
                color: red;
                margin: 20px 0;
            """)
            self.release_layout.addWidget(error_label)

    def closeEvent(self, event):
        if self.discord_presence:
            self.discord_presence.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FLauncher()
    window.show()
    sys.exit(app.exec_())
