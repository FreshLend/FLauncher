import markdown
from datetime import datetime
import requests
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QPushButton, 
    QComboBox, QTabWidget, QHBoxLayout, QProgressBar, QTextBrowser, 
    QLineEdit, QSizePolicy
)
from PyQt5.QtGui import QPalette, QBrush, QImage, QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QSize, QUrl

from utils import resource_path, MAIN_REPO


class UIComponents:
    def __init__(self, main_window):
        self.main = main_window
        
        self.input_field = None
        self.version_combo = None
        self.progress_bar = None
        self.download_info_label = None
        self.play_button = None
        self.flm_button = None
        self.reload_button = None
        self.folder_button = None
        self.settings_button = None
        self.blue_bar = None
        
        self.release_panel = None
        self.release_layout = None
        self.scroll_area = None
        
        self.settings_background = None
        self.settings_panel = None
        self.tab_widget = None
        self.additional_args_input = None
        self.discord_toggle = None
        self.repos_scroll = None
        self.repos_container = None
        self.repos_layout = None
        
        self.FL_MODS_background = None
        self.FL_MODS = None
    
    def setup_all(self):
        self.set_background()
        self.add_blue_bar()
        self.add_release_panel()
        self.add_info_panel()
        self.add_settings_panel()
        self.add_fl_mods_panel()
    
    def set_background(self):
        self.main.setAutoFillBackground(True)
        palette = self.main.palette()
        image = QImage(resource_path('ui/background.png'))
        brush = QBrush(image)
        palette.setBrush(QPalette.Background, brush)
        self.main.setPalette(palette)
    
    def add_blue_bar(self):
        self.blue_bar = QWidget(self.main)
        self.blue_bar.setGeometry(0, self.main.height() - 90, self.main.width(), 90)
        self.blue_bar.setStyleSheet("background-color: rgba(113, 169, 76, 0.9);")
        
        self.input_field = QLineEdit(self.blue_bar)
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
        self.input_field.textChanged.connect(self.main.on_text_changed)
        
        self.version_combo = QComboBox(self.blue_bar)
        self.version_combo.setGeometry(220, 20, 300, 60)
        self.version_combo.setStyleSheet("""
            QComboBox {
                background-color: white; 
                color: black; 
                font-size: 18px; 
                font-weight: bold;
                border-radius: 5px;
                padding: 5px;
                padding-right: 30px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid darkgray;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid black;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid darkgray;
                background-color: white;
                selection-background-color: lightblue;
                outline: none;
            }
        """)
        self.version_combo.currentIndexChanged.connect(self.main.on_version_changed)
        
        self.progress_bar = QProgressBar(self.blue_bar)
        self.progress_bar.setGeometry(10, 0, self.main.width() - 20, 20)
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
        
        self.download_info_label = QLabel(self.blue_bar)
        self.download_info_label.setGeometry(10, 0, self.main.width() - 20, 20)
        self.download_info_label.setStyleSheet("font-size: 12px; color: black;")
        self.download_info_label.setAlignment(Qt.AlignCenter)
        self.download_info_label.setText("")
        
        self.play_button = QPushButton("Войти в игру", self.blue_bar)
        self.play_button.setGeometry(530, 20, 300, 60)
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
        self.play_button.clicked.connect(self.main.on_play_button_click)
        
        icon_flm = QIcon(resource_path("ui/FLM.png"))
        self.flm_button = QPushButton(self.blue_bar)
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
        self.flm_button.clicked.connect(self.main.on_flm_button_click)
        
        icon_reload = QIcon(resource_path("ui/reload.png"))
        self.reload_button = QPushButton(self.blue_bar)
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
        self.reload_button.clicked.connect(self.main.refresh_versions)
        
        icon_folder = QIcon(resource_path("ui/folder.png"))
        self.folder_button = QPushButton(self.blue_bar)
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
        self.folder_button.clicked.connect(self.main.open_versions_folder)
        
        icon_settings = QIcon(resource_path("ui/settings.png"))
        self.settings_button = QPushButton(self.blue_bar)
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
        self.settings_button.clicked.connect(self.main.open_settings)
    
    def add_release_panel(self):
        self.release_panel = QWidget(self.main)
        self.release_panel.setGeometry(20, 40, 700, self.main.height() - 130)
        self.release_panel.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
        """)
        
        self.release_layout = QVBoxLayout(self.release_panel)
        self.release_layout.setContentsMargins(15, 15, 15, 15)
        self.release_layout.setSpacing(15)
        
        self.scroll_area = QScrollArea(self.main)
        self.scroll_area.setWidget(self.release_panel)
        self.scroll_area.setGeometry(20, 40, 800, self.main.height() - 130)
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
        info_panel = QWidget(self.main)
        info_panel.setGeometry(830, 0, 250, self.main.height() - 90)
        info_panel.setStyleSheet("""
            background-color: rgba(90, 171, 215, 0.9);
            border-top-right-radius: 10px;
        """)
        
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(15)
        
        title_label = QLabel('FLAUNCHER')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 30px; 
            font-weight: bold; 
            color: white;
            margin-bottom: 5px;
        """)
        info_layout.addWidget(title_label)
        
        subtitle_label = QLabel('ЛАУНЧЕР ДЛЯ VOXELCORE')
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
        
        button_voxel = QPushButton("VoxelWorld")
        button_voxel.setStyleSheet(button_style)
        button_voxel.setFixedHeight(40)
        button_voxel.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://voxelworld.ru/profile/84")))
        info_layout.addWidget(button_voxel)
        
        button_freshlend = QPushButton("FreshLend Studio")
        button_freshlend.setStyleSheet(button_style)
        button_freshlend.setFixedHeight(40)
        button_freshlend.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://freshlend.github.io")))
        info_layout.addWidget(button_freshlend)
        
        from utils import VERSION
        version_label = QLabel(f'Версия: {VERSION}')
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            font-size: 14px; 
            color: white;
            margin-top: 20px;
        """)
        info_layout.addWidget(version_label)
        
        info_layout.addStretch(1)
    
    def add_settings_panel(self):
        self.settings_background = QWidget(self.main)
        self.settings_background.setGeometry(0, 0, 1100, self.main.height())
        self.settings_background.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.settings_background.hide()
        
        self.settings_panel = QWidget(self.main)
        self.settings_panel.setGeometry(50, 30, 1000, self.main.height() - 120)
        self.settings_panel.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
        """)
        self.settings_panel.hide()
        
        blue_strip = QWidget(self.settings_panel)
        blue_strip.setGeometry(0, 0, self.settings_panel.width(), 50)
        blue_strip.setStyleSheet("background-color: #0086c7; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        
        blue_layout = QHBoxLayout(blue_strip)
        blue_layout.setContentsMargins(20, 0, 20, 0)
        
        settings_label = QLabel('Настройки')
        settings_label.setAlignment(Qt.AlignCenter)
        settings_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
        """)
        blue_layout.addWidget(settings_label)
        
        close_button = QPushButton("✕")
        close_button.setFixedSize(30, 30)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        close_button.clicked.connect(self.main.open_settings)
        blue_layout.addWidget(close_button)
        
        self.tab_widget = QTabWidget(self.settings_panel)
        self.tab_widget.setGeometry(10, 60, self.settings_panel.width() - 20, self.settings_panel.height() - 70)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #C2C7CB;
                background-color: white;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QTabBar::tab {
                background-color: #F0F0F0;
                border: 1px solid #C4C4C3;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 1px;
                font-size: 14px;
                min-width: 180px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-color: #C2C7CB;
            }
            QTabBar::tab:!selected {
                background-color: #E8E8E8;
            }
            QTabBar::tab:hover {
                background-color: #F8F8F8;
            }
        """)
        
        launch_tab = QWidget()
        launch_layout = QVBoxLayout(launch_tab)
        launch_layout.setContentsMargins(30, 20, 30, 20)
        launch_layout.setSpacing(25)
        
        launch_params_group = QWidget()
        launch_params_layout = QVBoxLayout(launch_params_group)
        launch_params_layout.setContentsMargins(0, 0, 0, 0)
        launch_params_layout.setSpacing(10)
        
        launch_params_label = QLabel('Параметры запуска')
        launch_params_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            color: #333;
            padding-bottom: 5px;
        """)
        launch_params_layout.addWidget(launch_params_label)
        
        params_description = QLabel(
            'Дополнительные аргументы для запуска VoxelCore.'
        )
        params_description.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding-bottom: 8px;
        """)
        params_description.setWordWrap(True)
        launch_params_layout.addWidget(params_description)
        
        self.additional_args_input = QLineEdit()
        self.additional_args_input.setText(self.main.settings["launch_params"]["additional_args"])
        self.additional_args_input.textChanged.connect(self.main.update_launch_params)
        self.additional_args_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCC;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #0086c7;
            }
        """)
        self.additional_args_input.setPlaceholderText("Аргументы:")
        launch_params_layout.addWidget(self.additional_args_input)
        
        launch_layout.addWidget(launch_params_group)
        launch_layout.addStretch(1)
        
        flauncher_tab = QWidget()
        flauncher_layout = QVBoxLayout(flauncher_tab)
        flauncher_layout.setContentsMargins(30, 20, 30, 20)
        flauncher_layout.setSpacing(25)
        
        github_group = QWidget()
        github_layout = QVBoxLayout(github_group)
        github_layout.setContentsMargins(0, 0, 0, 0)
        github_layout.setSpacing(12)
        
        github_label = QLabel('GitHub Репозитории')
        github_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            padding-bottom: 5px;
        """)
        github_layout.addWidget(github_label)
        
        github_description = QLabel(
            'Добавьте другие GitHub репозитории для загрузки версий.\nФормат: owner/repo (например: MihailRis/voxelcore)'
        )
        github_description.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding-bottom: 8px;
        """)
        github_description.setWordWrap(True)
        github_layout.addWidget(github_description)
        
        add_repo_button = QPushButton('Добавить репозиторий')
        add_repo_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 3px;
                text-align: center;
                min-width: 160px;
                max-width: 160px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        add_repo_button.setFixedHeight(35)
        add_repo_button.clicked.connect(self.main.add_github_repository)
        github_layout.addWidget(add_repo_button, alignment=Qt.AlignLeft)
        
        repos_label = QLabel('Добавленные репозитории:')
        repos_label.setStyleSheet("font-size: 14px; color: #333; font-weight: bold;")
        github_layout.addWidget(repos_label)
        
        self.repos_scroll = QScrollArea()
        self.repos_scroll.setWidgetResizable(True)
        self.repos_scroll.setFixedHeight(150)
        self.repos_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #DDD;
                background-color: white;
                border-radius: 3px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F0F0F0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #C0C0C0;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A0A0A0;
            }
        """)
        
        self.repos_container = QWidget()
        self.repos_layout = QVBoxLayout(self.repos_container)
        self.repos_layout.setContentsMargins(5, 5, 5, 5)
        self.repos_layout.setSpacing(3)
        
        self.repos_scroll.setWidget(self.repos_container)
        github_layout.addWidget(self.repos_scroll)
        
        self.load_github_repositories()
        
        flauncher_layout.addWidget(github_group)
        flauncher_layout.addStretch(1)
        
        privacy_tab = QWidget()
        privacy_layout = QVBoxLayout(privacy_tab)
        privacy_layout.setContentsMargins(30, 20, 30, 20)
        privacy_layout.setSpacing(25)
        
        discord_group = QWidget()
        discord_layout = QVBoxLayout(discord_group)
        discord_layout.setContentsMargins(0, 0, 0, 0)
        discord_layout.setSpacing(12)
        
        discord_label = QLabel('Discord RPC')
        discord_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            padding-bottom: 5px;
        """)
        discord_layout.addWidget(discord_label)
        
        discord_description = QLabel(
            'Отображает информацию о вашей активности в Discord.\nВы можете отключить эту функцию, если она вам не нужна.'
        )
        discord_description.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding-bottom: 8px;
        """)
        discord_description.setWordWrap(True)
        discord_layout.addWidget(discord_description)
        
        self.discord_toggle = QPushButton()
        self.update_discord_button_style(self.main.settings.get("discord_rpc_enabled", True))
        self.discord_toggle.setFixedHeight(35)
        self.discord_toggle.clicked.connect(self.main.toggle_discord_rpc)
        discord_layout.addWidget(self.discord_toggle, alignment=Qt.AlignLeft)
        
        privacy_layout.addWidget(discord_group)
        privacy_layout.addStretch(1)
        
        self.tab_widget.addTab(launch_tab, "Запуск VoxelCore")
        self.tab_widget.addTab(flauncher_tab, "Настройки FLauncher")
        self.tab_widget.addTab(privacy_tab, "Конфиденциальность")
    
    def add_fl_mods_panel(self):
        self.FL_MODS_background = QWidget(self.main)
        self.FL_MODS_background.setGeometry(0, 0, 1100, self.main.height())
        self.FL_MODS_background.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.FL_MODS_background.hide()
        
        self.FL_MODS = QWidget(self.main)
        self.FL_MODS.setGeometry(150, 30, 800, self.main.height() - 120)
        self.FL_MODS.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
        """)
        self.FL_MODS.hide()
        
        blue_strip = QWidget(self.FL_MODS)
        blue_strip.setGeometry(0, 0, self.FL_MODS.width(), 50)
        blue_strip.setStyleSheet("background-color: #00aaff; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        
        blue_layout = QHBoxLayout(blue_strip)
        blue_layout.setContentsMargins(20, 0, 20, 0)
        
        FL_MODS_label = QLabel('FLMODS')
        FL_MODS_label.setAlignment(Qt.AlignCenter)
        FL_MODS_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: white;
        """)
        blue_layout.addWidget(FL_MODS_label)
        
        close_button = QPushButton("✕")
        close_button.setFixedSize(30, 30)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        close_button.clicked.connect(self.main.on_flm_button_click)
        blue_layout.addWidget(close_button)
        
        layout = QVBoxLayout(self.FL_MODS)
        layout.setContentsMargins(20, 60, 20, 20)
        layout.setSpacing(20)
        
        text_browser = QTextBrowser()
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
    
    def set_username_from_config(self):
        version = self.version_combo.currentText()
        if version == "Получение версий...":
            return
        
        username = self.main.version_manager.get_username_from_config(version)
        if username:
            self.input_field.setText(username)
        else:
            self.input_field.clear()
            self.input_field.setPlaceholderText("Введите ник...")
    
    def load_github_repositories(self):
        if self.repos_layout:
            for i in reversed(range(self.repos_layout.count())): 
                widget = self.repos_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
        
        for repo in self.main.settings.get("github_repos", []):
            self.add_repository_to_list(repo)
    
    def add_repository_to_list(self, repo):
        repo_widget = QWidget()
        repo_widget.setStyleSheet("background-color: #f5f5f5; border-radius: 3px;")
        
        repo_layout = QHBoxLayout(repo_widget)
        repo_layout.setContentsMargins(10, 5, 10, 5)
        
        repo_label = QLabel(repo)
        repo_label.setStyleSheet("font-size: 14px;")
        repo_layout.addWidget(repo_label)
        
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                color: white;
                background-color: #ff4444;
                border-radius: 10px;
                padding: 0;
                border: none;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        delete_button.clicked.connect(lambda _, r=repo: self.main.remove_github_repository(r))
        repo_layout.addWidget(delete_button)
        
        self.repos_layout.addWidget(repo_widget)
    
    def update_discord_button_style(self, enabled):
        if enabled:
            self.discord_toggle.setText('Отключить Discord RPC')
            self.discord_toggle.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    background-color: #f44336;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 3px;
                    text-align: center;
                    min-width: 160px;
                    max-width: 160px;
                }
                QPushButton:hover {
                    background-color: #da3930;
                }
                QPushButton:pressed {
                    background-color: #c1372f;
                }
            """)
        else:
            self.discord_toggle.setText('Включить Discord RPC')
            self.discord_toggle.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 3px;
                    text-align: center;
                    min-width: 160px;
                    max-width: 160px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
    
    def get_github_releases(self):
        url = f"https://api.github.com/repos/{MAIN_REPO}/releases"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            releases = response.json()
            
            if self.release_layout:
                for i in reversed(range(self.release_layout.count())): 
                    widget = self.release_layout.itemAt(i).widget()
                    if widget:
                        widget.setParent(None)
            
            from utils import get_platform_asset_pattern
            asset_pattern = get_platform_asset_pattern()
            
            platform_names = {
                'win64.zip': 'Windows',
                '.dmg': 'macOS',
                '.AppImage': 'Linux'
            }
            platform_name = platform_names.get(asset_pattern, 'Unknown')
            
            platform_info = QLabel(f'Показываются релизы для платформы: {platform_name}')
            platform_info.setStyleSheet("""
                font-size: 14px;
                color: #333;
                margin: 10px 0;
                padding: 5px;
                background-color: rgba(200, 200, 200, 0.3);
                border-radius: 3px;
            """)
            self.release_layout.addWidget(platform_info)
            
            filtered_releases = 0
            for release in releases[:10]:
                if isinstance(release, dict):
                    assets = release.get('assets', [])
                    has_platform_asset = any(
                        asset_pattern in asset.get('name', '') 
                        for asset in assets
                    )
                    
                    if not has_platform_asset:
                        continue
                    
                    filtered_releases += 1
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
                    
                    version_label = QLabel(f'VoxelCore <a href="{release_url}" style="color: #0066cc;">{version}</a>')
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
                    header_layout.addStretch()
                    release_layout.addLayout(header_layout)
                    
                    release_body = release.get('body', '')
                    if release_body:
                        html_body = markdown.markdown(release_body)
                        html_body = html_body.replace('<a', '<a target="_blank"')
                        
                        release_info_label = QLabel()
                        release_info_label.setOpenExternalLinks(True)
                        release_info_label.setText(html_body)
                        release_info_label.setWordWrap(True)
                        release_info_label.setStyleSheet("""
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
            
            if filtered_releases == 0:
                no_releases_label = QLabel(
                    f'Нет доступных релизов для вашей платформы ({platform_name}).'
                )
                no_releases_label.setStyleSheet("""
                    font-size: 16px; 
                    color: #666;
                    margin: 20px 0;
                """)
                self.release_layout.addWidget(no_releases_label)
            
            all_releases_label = QLabel()
            all_releases_label.setText(
                f'<div style="margin-top: 20px;">'
                f'Посмотреть весь список релизов: '
                f'<a href="https://github.com/{MAIN_REPO}/releases" style="color: #0066cc;">'
                f'https://github.com/{MAIN_REPO}/releases</a></div>'
            )
            all_releases_label.setOpenExternalLinks(True)
            all_releases_label.setStyleSheet("""
                font-size: 16px; 
                color: black;
            """)
            self.release_layout.addWidget(all_releases_label)
            
            self.release_layout.addStretch(1)
            
        except requests.RequestException:
            error_label = QLabel("Не удалось загрузить релизы. Проверьте соединение с интернетом.")
            error_label.setStyleSheet("""
                font-size: 16px; 
                color: red;
                margin: 20px 0;
            """)
            self.release_layout.addWidget(error_label)
        
        except Exception as e:
            error_label = QLabel(f"Ошибка при обработке данных: {str(e)}")
            error_label.setStyleSheet("""
                font-size: 16px; 
                color: red;
                margin: 20px 0;
            """)
            self.release_layout.addWidget(error_label)
    
    def show_settings(self):
        self.settings_background.show()
        self.settings_panel.show()
        self.settings_background.raise_()
        self.settings_panel.raise_()
    
    def hide_settings(self):
        self.settings_background.hide()
        self.settings_panel.hide()
    
    def show_flmods(self):
        self.FL_MODS_background.show()
        self.FL_MODS.show()
        self.FL_MODS_background.raise_()
        self.FL_MODS.raise_()
    
    def hide_flmods(self):
        self.FL_MODS_background.hide()
        self.FL_MODS.hide()