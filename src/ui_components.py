import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QPushButton,
    QComboBox, QTabWidget, QHBoxLayout, QProgressBar,
    QLineEdit, QSizePolicy, QSpinBox, QCheckBox
)
from PyQt6.QtGui import (
    QPalette, QBrush, QImage, QIcon, QDesktopServices,
    QPainter, QPainterPath, QColor, QPen
)
from PyQt6.QtCore import Qt, QSize, QUrl, QObject, pyqtSignal, QRectF
from utils import resource_path, MAIN_REPO, VERSION
from flmods import ModsWidget


def _platform_name():
    if sys.platform == 'win32':
        return "Windows"
    if sys.platform == 'darwin':
        return "macOS"

    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("NAME="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        return value
    except Exception:
        pass

    return "Linux"


class FullWidthTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabBar().setExpanding(True)
        self.tabBar().setDrawBase(False)
        self._update_style()

    def _update_style(self):
        count = max(self.count(), 1)
        w = max(self.width() // count - 3, 60)
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: #f5f5f5;
            }}
            QTabBar {{
                background-color: #f5f5f5;
            }}
            QTabBar::tab {{
                background-color: #E4E4E4;
                border: none;
                padding: 10px 0px;
                margin: 0px 2px 0px 0px;
                font-size: 14px;
                color: #333;
                width: {w}px;
            }}
            QTabBar::tab:selected {{
                background-color: #0086c7;
                color: white;
                font-weight: bold;
            }}
            QTabBar::tab:!selected {{
                background-color: #E4E4E4;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #D8D8D8;
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_style()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_style()


class ToggleSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 2

        track_path = QPainterPath()
        track_path.addRoundedRect(rect, radius, radius)

        if self.isChecked():
            color = QColor("#4CAF50")
            if self.underMouse():
                color = QColor("#45a049")
        else:
            color = QColor("#BDBDBD")
            if self.underMouse():
                color = QColor("#A8A8A8")

        painter.fillPath(track_path, color)

        thumb_size = self.height() - 4
        if self.isChecked():
            thumb_x = self.width() - thumb_size - 2
        else:
            thumb_x = 2

        painter.setBrush(QColor("white"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(thumb_x, 2, thumb_size, thumb_size))

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()


class ArrowComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup_open = False

    def showPopup(self):
        super().showPopup()
        self._popup_open = True
        self.update()

    def hidePopup(self):
        super().hidePopup()
        self._popup_open = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(rect), 5, 5)
        painter.fillPath(bg_path, QColor(255, 255, 255))

        font = self.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(30, 30, 30))

        text_rect = rect.adjusted(12, 0, -42, 0)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.currentText()
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(30, 30, 30))

        cx = rect.width() - 20
        cy = rect.height() // 2
        size = 7

        arrow = QPainterPath()
        if self._popup_open:
            arrow.moveTo(cx - size, cy + size // 2)
            arrow.lineTo(cx + size, cy + size // 2)
            arrow.lineTo(cx, cy - size // 2 - 2)
        else:
            arrow.moveTo(cx - size, cy - size // 2)
            arrow.lineTo(cx + size, cy - size // 2)
            arrow.lineTo(cx, cy + size // 2 + 2)
        arrow.closeSubpath()
        painter.drawPath(arrow)

        if self.hasFocus():
            painter.setPen(QPen(QColor(52, 152, 219), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(rect).adjusted(1, 1, -1, -1), 5, 5)


class ReleaseDisplayWidget(QWidget):
    def __init__(self, release_data, parent=None):
        super().__init__(parent)
        self.setup_ui(release_data)

    def setup_ui(self, data):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        version_label = QLabel(
            f'<a href="{data["release_url"]}" style="color: #0066cc; text-decoration: none;">'
            f'VoxelCore {data["version"]}</a>'
        )
        version_label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #222;
            background: transparent;
            border: none;
        """)
        version_label.setOpenExternalLinks(True)

        date_label = QLabel(data["date"])
        date_label.setStyleSheet("""
            font-size: 12px;
            color: #888;
            background: transparent;
            border: none;
        """)

        header_layout.addWidget(version_label)
        header_layout.addStretch(1)
        header_layout.addWidget(date_label)
        layout.addLayout(header_layout)

        if data.get('body_html'):
            release_info_label = QLabel()
            release_info_label.setOpenExternalLinks(True)
            release_info_label.setText(data['body_html'])
            release_info_label.setWordWrap(True)
            release_info_label.setStyleSheet("""
                font-size: 13px;
                line-height: 1.5;
                color: #333;
                background: transparent;
                border: none;
            """)
            layout.addWidget(release_info_label)


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
    mods_target_version_changed = pyqtSignal(str)

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
        self.mods_widget = None
        self.mods_version_combo = None
        self.version_info_label = None

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
        palette.setBrush(QPalette.ColorRole.Window, brush)
        self.main.setPalette(palette)

    def add_bar(self):
        self.bar = QWidget(self.main)
        self.bar.setGeometry(0, self.main.height() - 90, self.main.width(), 90)
        self.bar.setStyleSheet("background-color: rgba(113, 169, 76, 0.9);")

        self.input_field = QLineEdit(self.bar)
        self.input_field.setGeometry(10, 20, 200, 60)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                font-size: 18px;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px;
                border: none;
            }
        """)
        self.input_field.setPlaceholderText("Введите ник...")
        self.input_field.textChanged.connect(self.username_changed)

        self.version_combo = ArrowComboBox(self.bar)
        self.version_combo.setGeometry(220, 20, 300, 60)
        self.version_combo.setStyleSheet("""
            QComboBox QAbstractItemView {
                border: 1px solid #aaa;
                background-color: white;
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
                outline: none;
                padding: 4px;
                min-width: 260px;
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
        self.download_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
                border: none;
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
            background-color: rgba(255, 255, 255, 0.85);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.35);
        """)
        self.release_layout = QVBoxLayout(self.release_panel)
        self.release_layout.setContentsMargins(25, 20, 25, 20)
        self.release_layout.setSpacing(25)
        self.scroll_area = QScrollArea(self.main)
        self.scroll_area.setWidget(self.release_panel)
        self.scroll_area.setGeometry(20, 10, 800, self.main.height() - 110)
        self.scroll_area.setWidgetResizable(True)
        self.release_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
            item = self.release_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        if not releases_data:
            no_releases_label = QLabel('Нет доступных релизов для вашей платформы.')
            no_releases_label.setStyleSheet("""
                font-size: 15px;
                color: #666;
                background: transparent;
                border: none;
                padding: 20px 0;
            """)
            self.release_layout.addWidget(no_releases_label)
            self.release_layout.addStretch(1)
            return

        repos_dict = {}
        for release in releases_data:
            repo = release.get('repo', MAIN_REPO)
            if repo not in repos_dict:
                repos_dict[repo] = []
            repos_dict[repo].append(release)

        for repo, repo_releases in repos_dict.items():
            if len(repos_dict) > 1:
                repo_header = QLabel(f'Репозиторий: {repo}')
                repo_header.setStyleSheet("""
                    font-size: 16px;
                    font-weight: bold;
                    color: #333;
                    background: transparent;
                    border: none;
                    padding: 0 0 5px 0;
                """)
                self.release_layout.addWidget(repo_header)

            for release in repo_releases:
                release_widget = ReleaseDisplayWidget(release)
                self.release_layout.addWidget(release_widget)

        all_releases_label = QLabel()
        all_releases_label.setText(
            f'<div style="margin-top: 10px;">'
            f'Все релизы: '
            f'<a href="https://github.com/{MAIN_REPO}/releases" '
            f'style="color: #0066cc; text-decoration: none;">'
            f'github.com/{MAIN_REPO}/releases</a></div>'
        )
        all_releases_label.setOpenExternalLinks(True)
        all_releases_label.setStyleSheet("""
            font-size: 14px;
            color: #555;
            background: transparent;
            border: none;
        """)
        self.release_layout.addWidget(all_releases_label)
        self.release_layout.addStretch(1)

    def show_rate_limit_warning(self, remaining, limit):
        if remaining < 10:
            limit_info = QLabel(f'Осталось запросов: {remaining}/{limit}')
            limit_info.setStyleSheet("""
                font-size: 12px;
                color: #ff9800;
                background: transparent;
                border: none;
            """)
            self.release_layout.addWidget(limit_info)

    def show_release_error(self, error_message):
        for i in reversed(range(self.release_layout.count())):
            item = self.release_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        error_label = QLabel(error_message)
        error_label.setStyleSheet("""
            font-size: 14px;
            color: #f44336;
            background: transparent;
            border: none;
            padding: 10px 0;
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

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        title_label = QLabel('FLAUNCHER')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 30px;
            font-weight: bold;
            color: white;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel('ЛАУНЧЕР ДЛЯ VOXELCORE')
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            font-size: 13px;
            font-weight: normal;
            color: white;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(subtitle_label)

        info_layout.addLayout(header_layout)

        button_style = """
            QPushButton {
                background-color: rgba(62, 148, 182, 0.85);
                font-size: 16px;
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

        button_freshlend = QPushButton("FreshLend Studio")
        button_freshlend.setStyleSheet(button_style)
        button_freshlend.setFixedHeight(40)
        button_freshlend.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://freshlend.github.io")))
        info_layout.addWidget(button_freshlend)

        button_voxel = QPushButton("VoxelWorld")
        button_voxel.setStyleSheet(button_style)
        button_voxel.setFixedHeight(40)
        button_voxel.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://voxelworld.ru/profile/84")))
        info_layout.addWidget(button_voxel)

        info_layout.addStretch(1)

        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(5, 0, 5, 0)
        bottom_layout.setSpacing(10)

        platform_label = QLabel(_platform_name())
        platform_label.setStyleSheet("""
            font-size: 13px;
            color: white;
            background: transparent;
            border: none;
        """)
        version_label = QLabel(VERSION)
        version_label.setStyleSheet("""
            font-size: 13px;
            color: white;
            background: transparent;
            border: none;
        """)

        bottom_layout.addWidget(platform_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(version_label)
        info_layout.addLayout(bottom_layout)

    def add_settings_panel(self):
        self.settings_background = QWidget(self.main)
        self.settings_background.setGeometry(0, 0, self.main.width(), self.main.height() - 90)
        self.settings_background.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.settings_background.hide()

        self.settings_panel = QWidget(self.main)
        self.settings_panel.setGeometry(0, 0, self.main.width(), self.main.height() - 90)
        self.settings_panel.setStyleSheet("""
            background-color: #f5f5f5;
            border-radius: 0px;
        """)
        self.settings_panel.hide()

        blue_strip = QWidget(self.settings_panel)
        blue_strip.setGeometry(0, 0, self.settings_panel.width(), 50)
        blue_strip.setStyleSheet("background-color: #0086c7;")
        blue_layout = QHBoxLayout(blue_strip)
        blue_layout.setContentsMargins(20, 0, 20, 0)

        settings_label = QLabel('Настройки')
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
            background: transparent;
            border: none;
        """)
        blue_layout.addWidget(settings_label)

        blue_layout.addStretch()

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

        self.tab_widget = FullWidthTabWidget(self.settings_panel)
        self.tab_widget.setGeometry(0, 50, self.settings_panel.width(), self.settings_panel.height() - 50)
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._create_launch_tab()
        self._create_flauncher_tab()
        self._create_privacy_tab()

    def _create_launch_tab(self):
        launch_tab = QWidget()
        launch_tab.setStyleSheet("background-color: #f5f5f5;")

        outer = QVBoxLayout(launch_tab)
        outer.setContentsMargins(30, 25, 30, 25)
        outer.setSpacing(8)

        label = QLabel("Параметры запуска")
        label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #333;
            background: transparent;
            border: none;
        """)
        outer.addWidget(label)

        self.additional_args_input = QLineEdit()
        self.additional_args_input.textChanged.connect(self.launch_params_changed)
        self.additional_args_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCC;
                padding: 8px 12px;
                font-size: 13px;
                background-color: white;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #0086c7;
            }
        """)
        self.additional_args_input.setPlaceholderText(
            "Параметры (e.g. --headless --script content/example/scripts/main.lua)"
        )
        outer.addWidget(self.additional_args_input)

        outer.addStretch(1)

        self.tab_widget.addTab(launch_tab, "Настройки VoxelCore")

    def _create_flauncher_tab(self):
        flauncher_tab = QWidget()
        flauncher_tab.setStyleSheet("background-color: #f5f5f5;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        artifacts_group, artifacts_container = self._create_group_box("Артефакты")
        a_layout = QVBoxLayout(artifacts_container)
        a_layout.setContentsMargins(20, 15, 20, 15)
        a_layout.setSpacing(12)

        row1 = QHBoxLayout()
        row1.setSpacing(15)

        self.artifacts_toggle = ToggleSwitch()
        self.artifacts_toggle.toggled.connect(self.artifacts_toggled.emit)

        artifacts_desc = QLabel("Показывать экспериментальные сборки из GitHub Actions.")
        artifacts_desc.setStyleSheet("""
            font-size: 13px;
            color: #555;
            background: transparent;
            border: none;
        """)
        artifacts_desc.setWordWrap(True)

        row1.addWidget(self.artifacts_toggle, alignment=Qt.AlignmentFlag.AlignVCenter)
        row1.addWidget(artifacts_desc, 1)
        a_layout.addLayout(row1)

        self.artifacts_count_group = QWidget()
        self.artifacts_count_group.setStyleSheet("background: transparent; border: none;")
        count_layout = QHBoxLayout(self.artifacts_count_group)
        count_layout.setContentsMargins(63, 0, 0, 0)
        count_layout.setSpacing(20)

        count_label = QLabel("Количество:")
        count_label.setStyleSheet("font-size: 13px; color: #555; background: transparent; border: none;")

        self.artifacts_count_spin = QSpinBox()
        self.artifacts_count_spin.setRange(1, 50)
        self.artifacts_count_spin.setFixedWidth(80)
        self.artifacts_count_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #CCC;
                padding: 4px 8px;
                font-size: 13px;
                background-color: white;
                border-radius: 3px;
            }
        """)
        self.artifacts_count_spin.valueChanged.connect(self.artifacts_count_changed)

        count_layout.addWidget(count_label)
        count_layout.addWidget(self.artifacts_count_spin)

        if self.settings_manager.system == 'win32':
            self.windows_group = QWidget()
            self.windows_group.setStyleSheet("background: transparent; border: none;")
            w_layout = QHBoxLayout(self.windows_group)
            w_layout.setContentsMargins(0, 0, 0, 0)
            w_layout.setSpacing(20)

            self.msvc_checkbox = QCheckBox("MSVC")
            self.msvc_checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 13px;
                    color: #333;
                    spacing: 6px;
                    background: transparent;
                    border: none;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            self.msvc_checkbox.stateChanged.connect(
                lambda state: self.windows_build_type_changed.emit('msvc', state == Qt.CheckState.Checked.value)
            )
            w_layout.addWidget(self.msvc_checkbox)

            self.clang_checkbox = QCheckBox("CLang")
            self.clang_checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 13px;
                    color: #333;
                    spacing: 6px;
                    background: transparent;
                    border: none;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            self.clang_checkbox.stateChanged.connect(
                lambda state: self.windows_build_type_changed.emit('clang', state == Qt.CheckState.Checked.value)
            )
            w_layout.addWidget(self.clang_checkbox)

            count_layout.addWidget(self.windows_group)

        count_layout.addStretch()
        a_layout.addWidget(self.artifacts_count_group)
        layout.addWidget(artifacts_group)

        github_group, github_container = self._create_group_box("GitHub Репозитории")
        g_layout = QVBoxLayout(github_container)
        g_layout.setContentsMargins(20, 15, 20, 15)
        g_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        github_desc = QLabel("Формат: owner/repo (например MihailRis/voxelcore)")
        github_desc.setStyleSheet("font-size: 13px; color: #555; background: transparent; border: none;")

        add_repo_button = QPushButton("+ Добавить")
        add_repo_button.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                background-color: #4CAF50;
                color: white;
                padding: 6px 15px;
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
        add_repo_button.setFixedHeight(30)
        add_repo_button.clicked.connect(self.add_repo_clicked)

        top_row.addWidget(github_desc)
        top_row.addStretch()
        top_row.addWidget(add_repo_button)
        g_layout.addLayout(top_row)

        self.repos_scroll = QScrollArea()
        self.repos_scroll.setWidgetResizable(True)
        self.repos_scroll.setFixedHeight(120)
        self.repos_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #DDD;
                background-color: white;
                border-radius: 3px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F0F0F0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #C0C0C0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A0A0A0;
            }
        """)

        self.repos_container = QWidget()
        self.repos_container.setStyleSheet("background: transparent; border: none;")
        self.repos_layout = QVBoxLayout(self.repos_container)
        self.repos_layout.setContentsMargins(5, 5, 5, 5)
        self.repos_layout.setSpacing(4)
        self.repos_layout.addStretch()
        self.repos_scroll.setWidget(self.repos_container)
        g_layout.addWidget(self.repos_scroll)
        layout.addWidget(github_group)

        token_group, token_container = self._create_group_box("GitHub Токен")
        t_layout = QVBoxLayout(token_container)
        t_layout.setContentsMargins(20, 15, 20, 15)
        t_layout.setSpacing(10)

        token_desc = QLabel("Токен увеличивает лимит запросов к GitHub API")
        token_desc.setStyleSheet("font-size: 13px; color: #555; background: transparent; border: none;")
        t_layout.addWidget(token_desc)

        token_row = QHBoxLayout()
        token_row.setSpacing(10)

        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.github_token_input.textChanged.connect(self.github_token_changed)
        self.github_token_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCC;
                padding: 6px 10px;
                font-size: 13px;
                background-color: white;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        self.github_token_input.setPlaceholderText("Введите GitHub токен...")

        self.check_token_button = QPushButton("Проверить")
        self.check_token_button.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                background-color: #2196F3;
                color: white;
                padding: 6px 15px;
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
        self.check_token_button.setFixedHeight(30)
        self.check_token_button.clicked.connect(self.check_token_clicked)

        self.refresh_releases_button = QPushButton("Обновить релизы")
        self.refresh_releases_button.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                background-color: #4CAF50;
                color: white;
                padding: 6px 15px;
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
        self.refresh_releases_button.setFixedHeight(30)
        self.refresh_releases_button.clicked.connect(self.refresh_releases_clicked)

        token_row.addWidget(self.github_token_input, 1)
        token_row.addWidget(self.check_token_button)
        token_row.addWidget(self.refresh_releases_button)
        t_layout.addLayout(token_row)

        self.token_status_label = QLabel('')
        self.token_status_label.setStyleSheet("""
            font-size: 12px;
            color: #666;
            padding: 4px 0;
            background: transparent;
            border: none;
        """)
        self.token_status_label.setWordWrap(True)
        t_layout.addWidget(self.token_status_label)
        layout.addWidget(token_group)

        layout.addStretch(1)
        scroll.setWidget(content)

        outer = QVBoxLayout(flauncher_tab)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self.tab_widget.addTab(flauncher_tab, "Настройки FLauncher")

    def _create_privacy_tab(self):
        privacy_tab = QWidget()
        privacy_tab.setStyleSheet("background-color: #f5f5f5;")

        layout = QVBoxLayout(privacy_tab)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        discord_group, discord_container = self._create_group_box("Discord")
        d_layout = QVBoxLayout(discord_container)
        d_layout.setContentsMargins(20, 15, 20, 15)
        d_layout.setSpacing(12)

        row = QHBoxLayout()
        row.setSpacing(15)

        self.discord_toggle = ToggleSwitch()
        self.discord_toggle.toggled.connect(self.discord_toggled.emit)

        discord_desc = QLabel("Отображать вашу активность в Discord")
        discord_desc.setStyleSheet("""
            font-size: 13px;
            color: #555;
            background: transparent;
            border: none;
        """)
        discord_desc.setWordWrap(True)

        row.addWidget(self.discord_toggle, alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(discord_desc, 1)
        d_layout.addLayout(row)

        layout.addWidget(discord_group)
        layout.addStretch(1)

        self.tab_widget.addTab(privacy_tab, "Конфиденциальность")

    def _create_group_box(self, title):
        group_box = QWidget()
        group_box.setObjectName("settingsGroupBox")
        group_box.setStyleSheet("""
            #settingsGroupBox {
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
            font-size: 14px;
            font-weight: bold;
            color: #333;
            background-color: #F5F5F5;
            padding: 8px 15px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            border-bottom: 1px solid #E0E0E0;
        """)
        main_layout.addWidget(title_label)

        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet("background: transparent; border: none;")
        main_layout.addWidget(content_container)
        return group_box, content_container

    def add_fl_mods_panel(self):
        self.FL_MODS_background = QWidget(self.main)
        self.FL_MODS_background.setGeometry(0, 0, self.main.width(), self.main.height() - 90)
        self.FL_MODS_background.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.FL_MODS_background.hide()

        self.FL_MODS = QWidget(self.main)
        self.FL_MODS.setGeometry(0, 0, self.main.width(), self.main.height() - 90)
        self.FL_MODS.setStyleSheet("""
            background-color: #f5f5f5;
            border-radius: 0px;
        """)
        self.FL_MODS.hide()

        blue_strip = QWidget(self.FL_MODS)
        blue_strip.setGeometry(0, 0, self.FL_MODS.width(), 50)
        blue_strip.setStyleSheet("background-color: #00aaff;")
        blue_layout = QHBoxLayout(blue_strip)
        blue_layout.setContentsMargins(20, 0, 20, 0)

        flmods_label = QLabel('FLMODS')
        flmods_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flmods_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
            background: transparent;
            border: none;
        """)
        blue_layout.addWidget(flmods_label)

        version_label = QLabel("Версия игры:")
        version_label.setStyleSheet("color: white; font-size: 14px; margin-left: 30px; background: transparent; border: none;")
        blue_layout.addWidget(version_label)

        self.mods_version_combo = QComboBox()
        self.mods_version_combo.setMinimumWidth(280)
        self.mods_version_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: black;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #aaa;
                background-color: white;
                color: black;
                selection-background-color: #3498db;
                selection-color: white;
                outline: none;
            }
        """)
        self.mods_version_combo.currentTextChanged.connect(self._on_mods_version_changed)
        blue_layout.addWidget(self.mods_version_combo)

        blue_layout.addStretch()

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
        layout.setContentsMargins(0, 50, 0, 0)
        self.mods_widget = ModsWidget(self.settings_manager, self.main.thread_manager)
        layout.addWidget(self.mods_widget)

    def set_available_versions(self, versions, current=None):
        if self.mods_version_combo is None:
            return
        self.mods_version_combo.blockSignals(True)
        self.mods_version_combo.clear()
        for v in versions:
            self.mods_version_combo.addItem(v)
        if current and current in versions:
            self.mods_version_combo.setCurrentText(current)
        elif versions:
            self.mods_version_combo.setCurrentIndex(0)
        self.mods_version_combo.blockSignals(False)
        if self.mods_version_combo.currentText():
            self._on_mods_version_changed(self.mods_version_combo.currentText())

    def _on_mods_version_changed(self, version):
        if not version or version == "Получение версий...":
            self.mods_widget.set_target_version(None)
            return
        self.mods_widget.set_target_version(version)
        self.mods_target_version_changed.emit(version)

    def update_version_info(self, version):
        pass

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
        repo_widget.setStyleSheet("background-color: #f5f5f5; border-radius: 3px; border: none;")
        repo_layout = QHBoxLayout(repo_widget)
        repo_layout.setContentsMargins(10, 4, 10, 4)

        repo_label = QLabel(repo)
        repo_label.setStyleSheet("font-size: 13px; border: none; background: transparent;")
        repo_layout.addWidget(repo_label)

        delete_button = QPushButton("×")
        delete_button.setFixedSize(18, 18)
        delete_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                color: white;
                background-color: #ff4444;
                border-radius: 9px;
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
        self.discord_toggle.blockSignals(True)
        self.discord_toggle.setChecked(enabled)
        self.discord_toggle.blockSignals(False)

    def update_artifacts_button_style(self, enabled):
        self.artifacts_toggle.blockSignals(True)
        self.artifacts_toggle.setChecked(enabled)
        self.artifacts_toggle.blockSignals(False)

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
        self.token_status_label.setStyleSheet(f"color: {color_code}; background: transparent; border: none;")

    def get_mods_widget(self):
        return self.mods_widget

    def update_mods_installed_status(self, installed_mods_set):
        if hasattr(self, 'mods_widget'):
            self.mods_widget.set_installed_items(installed_mods_set)