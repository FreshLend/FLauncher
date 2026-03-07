from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QPushButton, 
    QComboBox, QTabWidget, QHBoxLayout, QProgressBar, QTextBrowser, 
    QLineEdit, QSizePolicy, QSpinBox, QCheckBox
)
from PyQt5.QtGui import QPalette, QBrush, QImage, QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QSize, QUrl, QObject, pyqtSignal
from utils import resource_path, MAIN_REPO, VERSION
from github_client import GitHubClient

class ReleaseDisplayWidget(QWidget):
    def __init__(self, release_data, parent=None):
        super().__init__(parent)
        self.setup_ui(release_data)
    
    def setup_ui(self, data):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        header_layout = QHBoxLayout()
        
        version_label = QLabel(
            f'VoxelCore <a href="{data["release_url"]}" style="color: #0066cc;">{data["version"]}</a>'
        )
        version_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 24px; 
            color: black;
            margin-bottom: 5px;
        """)
        version_label.setOpenExternalLinks(True)
        
        date_label = QLabel(f'Дата релиза: {data["date"]}')
        date_label.setStyleSheet("""
            font-size: 12px; 
            color: gray; 
            margin-left: 10px;
        """)
        
        header_layout.addWidget(version_label)
        header_layout.addWidget(date_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        if data.get('body_html'):
            release_info_label = QLabel()
            release_info_label.setOpenExternalLinks(True)
            release_info_label.setText(data['body_html'])
            release_info_label.setWordWrap(True)
            release_info_label.setStyleSheet("""
                font-size: 14px; 
                line-height: 1.5; 
                color: black;
                margin-bottom: 15px;
            """)
            layout.addWidget(release_info_label)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.2); 
            height: 1px;
            margin: 10px 0;
        """)
        layout.addWidget(separator)


class UIComponents(QObject):
    username_changed = pyqtSignal(str)
    version_selected = pyqtSignal(str)
    play_clicked = pyqtSignal()
    flm_clicked = pyqtSignal()
    reload_clicked = pyqtSignal()
    folder_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    
    artifacts_toggled = pyqtSignal(bool)
    artifacts_count_changed = pyqtSignal(int)
    windows_build_type_changed = pyqtSignal(str, bool)
    discord_toggled = pyqtSignal(bool)
    launch_params_changed = pyqtSignal(str)
    github_token_changed = pyqtSignal(str)
    check_token_clicked = pyqtSignal()
    refresh_releases_clicked = pyqtSignal()
    add_repo_clicked = pyqtSignal()
    remove_repo_clicked = pyqtSignal(str)
    
    def __init__(self, main_window, settings_manager):
        super().__init__()
        self.main = main_window
        self.settings_manager = settings_manager
        
        self.input_field = None
        self.version_combo = None
        self.progress_bar = None
        self.download_info_label = None
        self.cancel_button = None
        self.play_button = None
        self.flm_button = None
        self.reload_button = None
        self.folder_button = None
        self.settings_button = None
        self.bar = None
        
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
        
        self.artifacts_toggle = None
        self.artifacts_count_spin = None
        self.artifacts_count_group = None
        self.windows_group = None
        self.github_token_input = None
        self.check_token_button = None
        self.refresh_releases_button = None
        self.token_status_label = None
    
    def setup_all(self):
        self.set_background()
        self.add_bar()
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
    
    def add_bar(self):
        self.bar = QWidget(self.main)
        self.bar.setGeometry(0, self.main.height() - 90, self.main.width(), 90)
        self.bar.setStyleSheet("background-color: rgba(113, 169, 76, 0.9);")
        
        self.input_field = QLineEdit(self.bar)
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
        self.input_field.textChanged.connect(self.username_changed)
        
        self.version_combo = QComboBox(self.bar)
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
        self.version_combo.currentIndexChanged.connect(
            lambda i: self.version_selected.emit(self.version_combo.currentText()) if i >= 0 else None
        )
        
        self.progress_bar = QProgressBar(self.bar)
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
        
        self.download_info_label = QLabel(self.bar)
        self.download_info_label.setGeometry(10, 0, self.main.width() - 20, 20)
        self.download_info_label.setStyleSheet("font-size: 12px; color: black;")
        self.download_info_label.setAlignment(Qt.AlignCenter)
        self.download_info_label.setText("")
        
        self.cancel_button = QPushButton("Отмена", self.bar)
        self.cancel_button.setGeometry(1000, 0, 80, 20)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.cancel_button.hide()
        
        self.play_button = QPushButton("Войти в игру", self.bar)
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
        self.play_button.clicked.connect(self.play_clicked)
        
        icon_flm = QIcon(resource_path("ui/FLM.png"))
        self.flm_button = QPushButton(self.bar)
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
        self.flm_button.clicked.connect(self.flm_clicked)
        
        icon_reload = QIcon(resource_path("ui/reload.png"))
        self.reload_button = QPushButton(self.bar)
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
        self.reload_button.clicked.connect(self.reload_clicked)
        
        icon_folder = QIcon(resource_path("ui/folder.png"))
        self.folder_button = QPushButton(self.bar)
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
        self.folder_button.clicked.connect(self.folder_clicked)
        
        icon_settings = QIcon(resource_path("ui/settings.png"))
        self.settings_button = QPushButton(self.bar)
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
        self.settings_button.clicked.connect(self.settings_clicked)
    
    def add_release_panel(self):
        self.release_panel = QWidget(self.main)
        self.release_panel.setGeometry(20, 10, 700, self.main.height() - 110)
        self.release_panel.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.55);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.25);
        """)
        
        self.release_layout = QVBoxLayout(self.release_panel)
        self.release_layout.setContentsMargins(20, 20, 20, 20)
        self.release_layout.setSpacing(15)
        
        self.scroll_area = QScrollArea(self.main)
        self.scroll_area.setWidget(self.release_panel)
        self.scroll_area.setGeometry(20, 10, 800, self.main.height() - 110)
        self.scroll_area.setWidgetResizable(True)
        
        self.release_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(200, 200, 200, 0.35);
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 100, 100, 0.5);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(100, 100, 100, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    def display_releases(self, releases_data):
        for i in reversed(range(self.release_layout.count())): 
            widget = self.release_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not releases_data:
            no_releases_label = QLabel(
                f'Нет доступных релизов для вашей платформы.'
            )
            no_releases_label.setStyleSheet("""
                font-size: 16px; 
                color: #666;
                margin: 20px 0;
            """)
            self.release_layout.addWidget(no_releases_label)
            self.release_layout.addStretch(1)
            return
        
        if releases_data and len(releases_data) > 0:
            platform_info = QLabel(f'Показываются релизы для платформы: {releases_data[0].get("platform_name", "Unknown")}')
            platform_info.setStyleSheet("""
                font-size: 14px;
                color: #333;
                margin: 10px 0;
                padding: 5px;
                background-color: rgba(200, 200, 200, 0.3);
                border-radius: 3px;
            """)
            self.release_layout.addWidget(platform_info)
        
        repos_dict = {}
        for release in releases_data:
            repo = release.get('repo', MAIN_REPO)
            if repo not in repos_dict:
                repos_dict[repo] = []
            repos_dict[repo].append(release)
        
        for repo, repo_releases in repos_dict.items():
            if len(repos_dict) > 1:
                repo_header = QLabel(f'📦 Репозиторий: {repo}')
                repo_header.setStyleSheet("""
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                    margin: 15px 0 5px 0;
                    padding: 5px;
                    background-color: rgba(0, 134, 199, 0.1);
                    border-left: 3px solid #0086c7;
                """)
                self.release_layout.addWidget(repo_header)
            
            for release in repo_releases:
                release_widget = ReleaseDisplayWidget(release)
                self.release_layout.addWidget(release_widget)
        
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
    
    def show_rate_limit_warning(self, remaining, limit):
        if remaining < 10:
            limit_info = QLabel(f'⚠️ Осталось запросов: {remaining}/{limit}')
            limit_info.setStyleSheet("""
                font-size: 12px;
                color: #ff9800;
                margin: 5px 0;
                padding: 5px;
                background-color: rgba(255, 152, 0, 0.1);
                border-radius: 3px;
            """)
            self.release_layout.addWidget(limit_info)
    
    def show_release_error(self, error_message):
        for i in reversed(range(self.release_layout.count())): 
            widget = self.release_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        error_label = QLabel(error_message)
        error_label.setStyleSheet("""
            font-size: 14px; 
            color: #f44336;
            margin: 20px 0;
            padding: 10px;
            background-color: rgba(244, 67, 54, 0.1);
            border-radius: 5px;
        """)
        error_label.setWordWrap(True)
        self.release_layout.addWidget(error_label)
        self.release_layout.addStretch(1)
    
    def add_info_panel(self):
        info_panel = QWidget(self.main)
        info_panel.setGeometry(830, 10, 250, self.main.height() - 110)
        info_panel.setStyleSheet("""
            background-color: rgba(90, 171, 215, 0.5);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        """)
        
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(15, 20, 15, 20)
        info_layout.setSpacing(15)
        
        title_label = QLabel('FLAUNCHER')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 32px;
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
            margin-bottom: 20px;
        """)
        info_layout.addWidget(subtitle_label)
        
        button_style = """
            QPushButton {
                background-color: rgba(62, 148, 182, 0.85);
                font-size: 18px;
                color: white;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background-color: rgba(72, 158, 192, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(52, 138, 172, 1.0);
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
        
        version_label = QLabel(f'Версия: {VERSION}')
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            font-size: 14px;
            color: white;
            margin-top: 25px;
            padding: 5px;
            background-color: rgba(0, 0, 0, 0.25);
            border-radius: 5px;
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
        close_button.clicked.connect(self.settings_clicked)
        blue_layout.addWidget(close_button)
        
        self.tab_widget = QTabWidget(self.settings_panel)
        self.tab_widget.setGeometry(10, 60, self.settings_panel.width() - 20, self.settings_panel.height() - 70)
        
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
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
                font-weight: bold;
            }
            QTabBar::tab:!selected {
                background-color: #E8E8E8;
            }
            QTabBar::tab:hover {
                background-color: #F8F8F8;
            }
        """)
        
        self._create_launch_tab()
        self._create_artifacts_tab()
        self._create_flauncher_tab()
        self._create_privacy_tab()
    
    def _create_launch_tab(self):
        launch_tab = QWidget()
        launch_layout = QVBoxLayout(launch_tab)
        launch_layout.setContentsMargins(30, 20, 30, 20)
        launch_layout.setSpacing(20)
        
        launch_params_group, launch_params_container = self._create_group_box("Параметры запуска")
        launch_params_layout = QVBoxLayout(launch_params_container)
        launch_params_layout.setContentsMargins(20, 20, 20, 20)
        launch_params_layout.setSpacing(15)
        
        params_description = QLabel(
            'Дополнительные аргументы командной строки для запуска VoxelCore.\n'
            'Например: --headless --script res/content/Neutron-Server/scripts/main.lua'
        )
        params_description.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 5px;
            background-color: #f5f5f5;
            border-radius: 3px;
        """)
        params_description.setWordWrap(True)
        launch_params_layout.addWidget(params_description)
        
        self.additional_args_input = QLineEdit()
        self.additional_args_input.textChanged.connect(self.launch_params_changed)
        self.additional_args_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCC;
                padding: 10px 12px;
                font-size: 14px;
                background-color: white;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #0086c7;
            }
        """)
        self.additional_args_input.setPlaceholderText("Введите аргументы запуска...")
        launch_params_layout.addWidget(self.additional_args_input)
        
        launch_layout.addWidget(launch_params_group)
        launch_layout.addStretch(1)
        
        self.tab_widget.addTab(launch_tab, "🚀 Запуск VoxelCore")
    
    def _create_artifacts_tab(self):
        artifacts_tab = QWidget()
        
        artifacts_scroll = QScrollArea()
        artifacts_scroll.setWidgetResizable(True)
        artifacts_scroll.setFrameShape(QFrame.NoFrame)
        artifacts_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        artifacts_content = QWidget()
        artifacts_layout = QVBoxLayout(artifacts_content)
        artifacts_layout.setContentsMargins(30, 20, 30, 20)
        artifacts_layout.setSpacing(20)
        
        artifacts_enable_group, artifacts_enable_container = self._create_group_box("Артефакты")
        artifacts_enable_layout = QVBoxLayout(artifacts_enable_container)
        artifacts_enable_layout.setContentsMargins(20, 20, 20, 20)
        artifacts_enable_layout.setSpacing(15)
        
        artifacts_description = QLabel(
            'Показывать артефакты из GitHub Actions.\n'
            'Это экспериментальные версии и они могут быть нестабильными.\n'
            'Рекомендуется использовать только для тестирования новых функций.'
        )
        artifacts_description.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 10px;
            background-color: #fff3e0;
            border-left: 3px solid #ff9800;
            border-radius: 3px;
        """)
        artifacts_description.setWordWrap(True)
        artifacts_enable_layout.addWidget(artifacts_description)
        
        self.artifacts_toggle = QPushButton()
        self.artifacts_toggle.setFixedHeight(40)
        self.artifacts_toggle.setFixedWidth(200)
        self.artifacts_toggle.clicked.connect(lambda: self.artifacts_toggled.emit(
            not self.settings_manager.settings["artifacts"]["enabled"]
        ))
        artifacts_enable_layout.addWidget(self.artifacts_toggle, alignment=Qt.AlignCenter)
        
        artifacts_layout.addWidget(artifacts_enable_group)
        
        self.artifacts_count_group, artifacts_count_container = self._create_group_box("Количество отображаемых артефактов")
        artifacts_count_layout = QVBoxLayout(artifacts_count_container)
        artifacts_count_layout.setContentsMargins(20, 20, 20, 20)
        artifacts_count_layout.setSpacing(15)
        
        count_info = QLabel(
            'Выберите, сколько артефактов показывать в списке версий.\n'
            'Большое количество может замедлить загрузку.'
        )
        count_info.setStyleSheet("font-size: 13px; color: #666;")
        count_info.setWordWrap(True)
        artifacts_count_layout.addWidget(count_info)
        
        count_input_layout = QHBoxLayout()
        self.artifacts_count_spin = QSpinBox()
        self.artifacts_count_spin.setRange(1, 50)
        self.artifacts_count_spin.setSuffix(" артефактов")
        self.artifacts_count_spin.setFixedWidth(130)
        self.artifacts_count_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #CCC;
                padding: 8px;
                font-size: 14px;
                background-color: white;
                border-radius: 3px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
            }
        """)
        self.artifacts_count_spin.valueChanged.connect(self.artifacts_count_changed)
        count_input_layout.addWidget(self.artifacts_count_spin)
        
        count_hint = QLabel('(максимум 50)')
        count_hint.setStyleSheet("font-size: 13px; color: #999;")
        count_input_layout.addWidget(count_hint)
        count_input_layout.addStretch()
        
        artifacts_count_layout.addLayout(count_input_layout)
        artifacts_layout.addWidget(self.artifacts_count_group)
        
        if self.settings_manager.system == 'win32':
            self.windows_group, windows_container = self._create_group_box("Типы сборок для Windows")
            windows_layout = QVBoxLayout(windows_container)
            windows_layout.setContentsMargins(20, 20, 20, 20)
            windows_layout.setSpacing(15)
            
            windows_info = QLabel(
                'Выберите, какие типы сборок будут отображаться в списке версий.'
            )
            windows_info.setStyleSheet("font-size: 13px; color: #666;")
            windows_info.setWordWrap(True)
            windows_layout.addWidget(windows_info)
            
            checkboxes_layout = QHBoxLayout()
            checkboxes_layout.setSpacing(30)
            
            self.msvc_checkbox = QCheckBox("MSVC Build")
            self.msvc_checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    color: #333;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            self.msvc_checkbox.stateChanged.connect(
                lambda state: self.windows_build_type_changed.emit('msvc', state == Qt.Checked)
            )
            checkboxes_layout.addWidget(self.msvc_checkbox)
            
            self.clang_checkbox = QCheckBox("CLang Build")
            self.clang_checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    color: #333;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            self.clang_checkbox.stateChanged.connect(
                lambda state: self.windows_build_type_changed.emit('clang', state == Qt.Checked)
            )
            checkboxes_layout.addWidget(self.clang_checkbox)
            checkboxes_layout.addStretch()
            
            windows_layout.addLayout(checkboxes_layout)
            artifacts_layout.addWidget(self.windows_group)
        
        artifacts_layout.addStretch(1)
        
        artifacts_scroll.setWidget(artifacts_content)
        
        artifacts_tab_layout = QVBoxLayout(artifacts_tab)
        artifacts_tab_layout.setContentsMargins(0, 0, 0, 0)
        artifacts_tab_layout.addWidget(artifacts_scroll)
        
        self.tab_widget.addTab(artifacts_tab, "📦 Артефакты")
    
    def _create_flauncher_tab(self):
        flauncher_tab = QWidget()
        flauncher_scroll = QScrollArea()
        flauncher_scroll.setWidgetResizable(True)
        flauncher_scroll.setFrameShape(QFrame.NoFrame)
        flauncher_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        flauncher_content = QWidget()
        flauncher_layout = QVBoxLayout(flauncher_content)
        flauncher_layout.setContentsMargins(30, 20, 30, 20)
        flauncher_layout.setSpacing(20)
        
        github_group, github_container = self._create_group_box("GitHub Репозитории")
        github_layout = QVBoxLayout(github_container)
        github_layout.setContentsMargins(20, 20, 20, 20)
        github_layout.setSpacing(15)
        
        github_description = QLabel(
            'Добавьте другие GitHub репозитории для загрузки версий.\n'
            'Формат: owner/repo (например: MihailRis/voxelcore)'
        )
        github_description.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 3px;
        """)
        github_description.setWordWrap(True)
        github_layout.addWidget(github_description)
        
        add_repo_button = QPushButton('➕ Добавить репозиторий')
        add_repo_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 3px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        add_repo_button.setFixedHeight(40)
        add_repo_button.clicked.connect(self.add_repo_clicked)
        github_layout.addWidget(add_repo_button, alignment=Qt.AlignCenter)
        
        repos_label = QLabel('Добавленные репозитории:')
        repos_label.setStyleSheet("font-size: 14px; color: #333; font-weight: bold; margin-top: 10px;")
        github_layout.addWidget(repos_label)
        
        self.repos_scroll = QScrollArea()
        self.repos_scroll.setWidgetResizable(True)
        self.repos_scroll.setFixedHeight(200)
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
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A0A0A0;
            }
        """)
        
        self.repos_container = QWidget()
        self.repos_layout = QVBoxLayout(self.repos_container)
        self.repos_layout.setContentsMargins(5, 5, 5, 5)
        self.repos_layout.setSpacing(5)
        self.repos_layout.addStretch()
        
        self.repos_scroll.setWidget(self.repos_container)
        github_layout.addWidget(self.repos_scroll)
        
        flauncher_layout.addWidget(github_group)
        
        github_token_group, github_token_container = self._create_group_box("GitHub Токен")
        github_token_layout = QVBoxLayout(github_token_container)
        github_token_layout.setContentsMargins(20, 20, 20, 20)
        github_token_layout.setSpacing(15)
        
        token_description = QLabel(
            'Токен для доступа к GitHub API. Нужен для увеличения лимита запросов.\n'
            'Создать токен: Settings → Developer settings → Personal access tokens'
        )
        token_description.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 10px;
            background-color: #e3f2fd;
            border-left: 3px solid #2196F3;
            border-radius: 3px;
        """)
        token_description.setWordWrap(True)
        github_token_layout.addWidget(token_description)
        
        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.Password)
        self.github_token_input.textChanged.connect(self.github_token_changed)
        self.github_token_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCC;
                padding: 10px 12px;
                font-size: 14px;
                background-color: white;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        self.github_token_input.setPlaceholderText("Введите GitHub токен...")
        github_token_layout.addWidget(self.github_token_input)
        
        token_buttons_layout = QHBoxLayout()
        token_buttons_layout.setSpacing(10)
        
        self.check_token_button = QPushButton('✓ Проверить токен')
        self.check_token_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.check_token_button.setFixedHeight(40)
        self.check_token_button.clicked.connect(self.check_token_clicked)
        token_buttons_layout.addWidget(self.check_token_button)
        
        self.refresh_releases_button = QPushButton('↻ Обновить панель релизов')
        self.refresh_releases_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.refresh_releases_button.setFixedHeight(40)
        self.refresh_releases_button.clicked.connect(self.refresh_releases_clicked)
        token_buttons_layout.addWidget(self.refresh_releases_button)
        token_buttons_layout.addStretch()
        
        github_token_layout.addLayout(token_buttons_layout)
        
        self.token_status_label = QLabel('')
        self.token_status_label.setStyleSheet("""
            font-size: 13px;
            color: #666;
            margin-top: 5px;
            padding: 8px;
            background-color: #f5f5f5;
            border-radius: 3px;
        """)
        self.token_status_label.setWordWrap(True)
        github_token_layout.addWidget(self.token_status_label)
        
        flauncher_layout.addWidget(github_token_group)
        flauncher_layout.addStretch(1)
        
        flauncher_scroll.setWidget(flauncher_content)
        
        flauncher_tab_layout = QVBoxLayout(flauncher_tab)
        flauncher_tab_layout.setContentsMargins(0, 0, 0, 0)
        flauncher_tab_layout.addWidget(flauncher_scroll)
        
        self.tab_widget.addTab(flauncher_tab, "⚙️ Настройки FLauncher")
    
    def _create_privacy_tab(self):
        privacy_tab = QWidget()
        privacy_layout = QVBoxLayout(privacy_tab)
        privacy_layout.setContentsMargins(30, 20, 30, 20)
        privacy_layout.setSpacing(20)
        
        discord_group, discord_container = self._create_group_box("Discord RPC")
        discord_layout = QVBoxLayout(discord_container)
        discord_layout.setContentsMargins(20, 20, 20, 20)
        discord_layout.setSpacing(15)
        
        discord_description = QLabel(
            'Discord Rich Presence отображает информацию о вашей активности в Discord.\n'
            'Друзья смогут видеть, во что вы играете и сколько времени.'
        )
        discord_description.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 3px;
        """)
        discord_description.setWordWrap(True)
        discord_layout.addWidget(discord_description)
        
        self.discord_toggle = QPushButton()
        self.discord_toggle.setFixedHeight(40)
        self.discord_toggle.setFixedWidth(200)
        self.discord_toggle.clicked.connect(
            lambda: self.discord_toggled.emit(not self.settings_manager.settings.get("discord_rpc_enabled", True))
        )
        discord_layout.addWidget(self.discord_toggle, alignment=Qt.AlignCenter)
        
        privacy_layout.addWidget(discord_group)
        privacy_layout.addStretch(1)
        
        self.tab_widget.addTab(privacy_tab, "🔒 Конфиденциальность")
    
    def _create_group_box(self, title):
        group_box = QWidget()
        group_box.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
            }
        """)
        
        main_layout = QVBoxLayout(group_box)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            background-color: #F5F5F5;
            padding: 10px 15px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            border-bottom: 1px solid #E0E0E0;
        """)
        main_layout.addWidget(title_label)
        
        content_container = QWidget()
        content_container.setObjectName("content_container")
        main_layout.addWidget(content_container)
        
        return group_box, content_container
    
    def add_fl_mods_panel(self):
        self.FL_MODS_background = QWidget(self.main)
        self.FL_MODS_background.setGeometry(0, 0, 1100, self.main.height())
        self.FL_MODS_background.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.FL_MODS_background.hide()
        
        self.FL_MODS = QWidget(self.main)
        self.FL_MODS.setGeometry(50, 30, 1000, self.main.height() - 120)
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
        
        flmods_label = QLabel('FLMODS')
        flmods_label.setAlignment(Qt.AlignCenter)
        flmods_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: white;
        """)
        blue_layout.addWidget(flmods_label)
        
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
        close_button.clicked.connect(self.flm_clicked)
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
    
    def set_username_from_config(self, username):
        if username:
            self.input_field.setText(username)
        else:
            self.input_field.clear()
            self.input_field.setPlaceholderText("Введите ник...")
    
    def load_github_repositories(self, repos):
        if self.repos_layout:
            for i in reversed(range(self.repos_layout.count())): 
                widget = self.repos_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
        
        for repo in repos:
            self._add_repository_to_list(repo)
    
    def _add_repository_to_list(self, repo):
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
        delete_button.clicked.connect(lambda _, r=repo: self.remove_repo_clicked.emit(r))
        repo_layout.addWidget(delete_button)
        
        self.repos_layout.insertWidget(self.repos_layout.count() - 1, repo_widget)
    
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
    
    def update_artifacts_button_style(self, enabled):
        if enabled:
            self.artifacts_toggle.setText('Отключить артефакты')
            self.artifacts_toggle.setStyleSheet("""
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
            self.artifacts_toggle.setText('Включить артефакты')
            self.artifacts_toggle.setStyleSheet("""
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
    
    def set_cancel_button_visible(self, visible):
        if hasattr(self, 'cancel_button'):
            if visible:
                self.cancel_button.show()
                self.cancel_button.setEnabled(True)
            else:
                self.cancel_button.hide()
    
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
    
    def update_token_status(self, status_text, color_code):
        self.token_status_label.setText(status_text)
        self.token_status_label.setStyleSheet(f"color: {color_code};")
