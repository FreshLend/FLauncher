import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QPushButton,
    QComboBox, QHBoxLayout, QProgressBar,
    QLineEdit, QSizePolicy, QSpinBox, QCheckBox,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect,
)
from PyQt6.QtGui import (
    QPalette, QBrush, QImage, QPixmap, QIcon, QDesktopServices,
    QPainter, QColor,
)
from PyQt6.QtCore import Qt, QSize, QUrl, QObject, pyqtSignal

from utils import resource_path, MAIN_REPO, VERSION, get_platform_name
from flmods import ModsWidget
from ui.widgets import (
    ArrowComboBox, ToggleSwitch, FullWidthTabWidget,
    BlurredBackdrop, ReleaseDisplayWidget, parse_color,
)
from i18n import tr, i18n


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
    theme_selected = pyqtSignal(str)
    language_selected = pyqtSignal(str)
    open_themes_folder_clicked = pyqtSignal()

    def __init__(self, main_window, settings_manager, theme_manager):
        super().__init__()
        self.main = main_window
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.theme = theme_manager.current

        self.bar = None
        self._background_pixmap = None
        self._blur_backdrops = {}
        self._blur_targets = []
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
        self.release_panel = None
        self.release_layout = None
        self.scroll_area = None
        self.info_panel = None
        self.info_buttons = []
        self.bottom_platform_label = None
        self.bottom_version_label = None
        self.header_title = None
        self.header_subtitle = None
        self.settings_background = None
        self.settings_panel = None
        self.settings_header_strip = None
        self.settings_header_label = None
        self.settings_close_btn = None
        self.tab_widget = None
        self.additional_args_input = None
        self.discord_toggle = None
        self.repos_scroll = None
        self.repos_container = None
        self.repos_layout = None
        self.FL_MODS_background = None
        self.FL_MODS = None
        self.flmods_header_strip = None
        self.flmods_header_label = None
        self.flmods_version_label = None
        self.flmods_close_btn = None
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
        self.theme_combo = None
        self.language_combo = None
        self.reload_theme_btn = None
        self.open_themes_button = None
        self.launch_params_label = None
        self._settings_open = False
        self.launch_tab = None
        self.flauncher_tab = None
        self.privacy_tab = None
        self.group_boxes = []
        self.add_repo_button = None
        self.settings_labels = []
        self.theme_desc_label = None
        self.language_desc_label = None
        self.artifacts_desc_label = None
        self.count_label = None
        self.github_desc_label = None
        self.token_desc_label = None
        self.discord_desc_label = None
        self.msvc_checkbox = None
        self.clang_checkbox = None
        self._last_releases_data = None

    def setup_all(self):
        self.set_background()
        self.add_bar()
        self.add_release_panel()
        self.add_info_panel()
        self.add_settings_panel()
        self.add_fl_mods_panel()

        self._blur_targets = [
            (self.bar, "bar_bg", "bar_blur", "bar_radius"),
            (self.scroll_area, "release_panel_bg", "release_panel_blur", "release_panel_radius"),
            (self.info_panel, "info_panel_bg", "info_panel_blur", "info_panel_radius"),
            (self.settings_panel, "settings_bg", "settings_blur", "settings_panel_radius"),
            (self.FL_MODS, "flmods_bg", "flmods_blur", "bar_radius"),
        ]

        self._apply_layout()
        self._update_all_blurs()

    def retranslate_ui(self):
        self.input_field.setPlaceholderText(tr("input.nick_placeholder"))
        self.play_button.setText(tr("button.play"))
        self.cancel_button.setText(tr("button.cancel"))
        self.header_title.setText(tr("info.title"))
        self.header_subtitle.setText(tr("info.subtitle"))
        self.settings_header_label.setText(tr("settings.title"))

        self.flmods_header_label.setText(tr("flmods.title"))
        self.flmods_version_label.setText(tr("flmods.version_label"))

        self.tab_widget.setTabText(0, tr("settings.tab.voxelcore"))
        self.tab_widget.setTabText(1, tr("settings.tab.flauncher"))
        self.tab_widget.setTabText(2, tr("settings.tab.privacy"))

        self.launch_params_label.setText(tr("settings.launch_params"))
        self.additional_args_input.setPlaceholderText(tr("settings.launch_params_hint"))

        self.reload_theme_btn.setToolTip(tr("settings.reload_tooltip"))
        self.open_themes_button.setText(tr("settings.open_folder"))

        if self.theme_desc_label:
            self.theme_desc_label.setText(tr("settings.theme_desc"))
        if self.language_desc_label:
            self.language_desc_label.setText(tr("settings.language_desc"))
        if self.artifacts_desc_label:
            self.artifacts_desc_label.setText(tr("settings.artifacts_desc"))
        if self.count_label:
            self.count_label.setText(tr("settings.artifacts_count"))
        if self.github_desc_label:
            self.github_desc_label.setText(tr("settings.repos_desc"))
        if self.token_desc_label:
            self.token_desc_label.setText(tr("settings.token_desc"))
        if self.discord_desc_label:
            self.discord_desc_label.setText(tr("settings.discord_desc"))

        self.add_repo_button.setText(tr("settings.repos_add"))
        self.github_token_input.setPlaceholderText(tr("settings.token_placeholder"))
        self.check_token_button.setText(tr("settings.token_check"))
        self.refresh_releases_button.setText(tr("settings.token_refresh"))

        for group, title_label, content, key in self.group_boxes:
            title_label.setText(tr(key))

        if self.mods_widget is not None:
            self.mods_widget.retranslate()

        if self._last_releases_data is not None:
            self.display_releases(self._last_releases_data)

    def apply_theme(self):
        self.theme = self.theme_manager.current
        self.set_background()
        self._apply_bar_theme()
        self._apply_release_panel_theme()
        self._apply_info_panel_theme()
        self._apply_settings_panel_theme()
        self._apply_flmods_theme()
        self._refresh_releases_display()
        self._apply_layout()
        self._update_settings_backdrop()
        self._update_all_blurs()

        if getattr(self, "_settings_open", False):
            self.settings_background.raise_()
            self.settings_panel.raise_()
            if self.theme.get("layout", {}).get("mode", "bar") == "centered":
                self.bar.raise_()

        if self.version_combo:
            self.version_combo.set_theme(self.theme)
        if self.artifacts_toggle:
            self.artifacts_toggle.set_theme(self.theme)
        if self.discord_toggle:
            self.discord_toggle.set_theme(self.theme)

    def _refresh_releases_display(self):
        for i in range(self.release_layout.count()):
            item = self.release_layout.itemAt(i)
            w = item.widget()
            if isinstance(w, ReleaseDisplayWidget):
                w.apply_theme(self.theme)

    def _apply_layout(self):
        t = self.theme
        layout = t.get("layout", {})
        mode = layout.get("mode", "bar")
        W = self.main.width()
        H = self.main.height()
        settings_open = getattr(self, "_settings_open", False)
        settings_mode = layout.get("settings_mode", "fullscreen")

        if mode == "centered":
            panel_w = int(layout.get("panel_w", 380))
            panel_h = int(layout.get("panel_h", 400))
            panel_y = int(layout.get("panel_y", 30))

            if settings_open and settings_mode == "right":
                left_margin = int(layout.get("panel_left_margin", 30))
                bar_x = left_margin
                bar_y = panel_y
            elif settings_open and settings_mode == "left":
                right_margin = int(layout.get("panel_right_margin", 30))
                bar_x = W - panel_w - right_margin
                bar_y = panel_y
            else:
                bar_x = (W - panel_w) // 2
                bar_y = panel_y
            bar_w = panel_w
            bar_h = panel_h
            content_y = 0
            content_h = H
        else:
            bar_h = int(layout.get("bar_height", 90))
            bar_pos = layout.get("bar_position", "bottom")
            if bar_pos == "top":
                bar_x = 0
                bar_y = 0
                content_y = bar_h
            else:
                bar_x = 0
                bar_y = H - bar_h
                content_y = 0
            bar_w = W
            content_h = H - bar_h

        self.bar.setGeometry(bar_x, bar_y, bar_w, bar_h)

        def resolve(spec, parent_w, parent_h):
            x, y, w, h = spec
            if w < 0:
                w = parent_w + w
            if h < 0:
                h = parent_h + h
            return int(x), int(y), int(w), int(h)

        def set_widget(widget, key, parent_w, parent_h, base_y=0):
            if widget is None or key not in layout:
                return
            x, y, w, h = resolve(layout[key], parent_w, parent_h)
            widget.setGeometry(x, base_y + y, w, h)

        set_widget(self.input_field, "nick_input", bar_w, bar_h)
        set_widget(self.version_combo, "version_combo", bar_w, bar_h)
        set_widget(self.play_button, "play_button", bar_w, bar_h)
        set_widget(self.flm_button, "flm_button", bar_w, bar_h)
        set_widget(self.reload_button, "reload_button", bar_w, bar_h)
        set_widget(self.folder_button, "folder_button", bar_w, bar_h)
        set_widget(self.settings_button, "settings_button", bar_w, bar_h)

        for btn in (self.flm_button,):
            if btn is not None:
                s = btn.size()
                m = min(s.width(), s.height())
                sz = max(int(m * 0.85), 16)
                btn.setIconSize(QSize(sz, sz))

        for btn in (self.reload_button, self.folder_button, self.settings_button):
            if btn is not None:
                s = btn.size()
                m = min(s.width(), s.height())
                sz = max(int(m * 0.55), 16)
                btn.setIconSize(QSize(sz, sz))

        if "progress_bar" in layout:
            x, y, w, h = resolve(layout["progress_bar"], bar_w, bar_h)
            self.progress_bar.setGeometry(x, y, w, h)

        if "progress_label" in layout:
            x, y, w, h = resolve(layout["progress_label"], bar_w, bar_h)
            self.download_info_label.setGeometry(x, y, w, h)
        elif "progress_bar" in layout:
            x, y, w, h = resolve(layout["progress_bar"], bar_w, bar_h)
            self.download_info_label.setGeometry(x, y, w, h)

        set_widget(self.cancel_button, "cancel_button", bar_w, bar_h)

        hide_releases = layout.get("hide_releases", False)
        if hide_releases:
            self.scroll_area.hide()
        else:
            self.scroll_area.show()
            if "release_scroll" in layout:
                x, y, w, h = resolve(layout["release_scroll"], W, content_h)
                self.scroll_area.setGeometry(x, content_y + y, w, h)

        hide_info = layout.get("hide_info", False)
        if hide_info:
            self.info_panel.hide()
        else:
            self.info_panel.show()
            if "info_panel" in layout:
                x, y, w, h = resolve(layout["info_panel"], W, content_h)
                self.info_panel.setGeometry(x, content_y + y, w, h)

        side_settings = (
            mode == "centered"
            and settings_mode in ("right", "left")
            and settings_open
        )

        if side_settings:
            right_w = int(layout.get("settings_right_w", 640))
            right_margin = int(layout.get("settings_right_margin", 30))
            top_m = int(layout.get("settings_top_margin", 30))
            bottom_m = int(layout.get("settings_bottom_margin", 30))
            if settings_mode == "right":
                sx = W - right_w - right_margin
            else:
                sx = right_margin
            sy = top_m
            sw = right_w
            sh = H - top_m - bottom_m
            self.settings_panel.setGeometry(sx, sy, sw, sh)
            self.settings_header_strip.setGeometry(0, 0, sw, 50)
            self.settings_close_btn.move(sw - 50, 10)
            self.tab_widget.setGeometry(0, 50, sw, sh - 50)
        else:
            self.settings_panel.setGeometry(0, content_y, W, content_h)
            self.settings_header_strip.setGeometry(0, 0, W, 50)
            self.settings_close_btn.move(W - 50, 10)
            self.tab_widget.setGeometry(0, 50, W, content_h - 50)

        backdrop = layout.get("settings_backdrop", "dim")
        if side_settings and backdrop != "none":
            self.settings_background.setGeometry(0, 0, W, H)
        else:
            self.settings_background.setGeometry(0, content_y, W, content_h)

        self.FL_MODS_background.setGeometry(0, content_y, W, content_h)
        self.FL_MODS.setGeometry(0, content_y, W, content_h)
        self.flmods_header_strip.setGeometry(0, 0, W, 50)
        self.flmods_close_btn.move(W - 50, 10)

        if mode == "centered":
            self.bar.raise_()

        self._update_all_blurs()

    def set_background(self):
        self.main.setAutoFillBackground(True)
        palette = self.main.palette()

        bg_path = None
        try:
            bg_path = self.theme_manager.get_background()
        except Exception:
            bg_path = None

        image = QImage()
        if bg_path:
            image = QImage(str(bg_path))
        if image.isNull():
            image = QImage(resource_path('ui/images/background.png'))

        brush = QBrush(image)
        palette.setBrush(QPalette.ColorRole.Window, brush)
        self.main.setPalette(palette)

        self._background_pixmap = QPixmap.fromImage(image)
        self._update_all_blurs()

    def add_bar(self):
        t = self.theme
        self.bar = QWidget(self.main)
        self.bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.bar.setAutoFillBackground(False)

        self.input_field = QLineEdit(self.bar)
        self.input_field.setPlaceholderText(tr("input.nick_placeholder"))
        self.input_field.textChanged.connect(self.username_changed)

        self.version_combo = ArrowComboBox(self.bar, theme=t)
        self.version_combo.currentIndexChanged.connect(
            lambda i: self.version_selected.emit(self.version_combo.currentText()) if i >= 0 else None
        )

        self.progress_bar = QProgressBar(self.bar)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        self.download_info_label = QLabel(self.bar)
        self.download_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.download_info_label.setText("")

        self.cancel_button = QPushButton(tr("button.cancel"), self.bar)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.cancel_button.hide()

        self.play_button = QPushButton(tr("button.play"), self.bar)
        self.play_button.clicked.connect(self.play_clicked)

        icon_flm = QIcon(resource_path("ui/images/FLM.png"))
        self.flm_button = QPushButton(self.bar)
        self.flm_button.setIcon(icon_flm)
        self.flm_button.setIconSize(QSize(60, 60))
        self.flm_button.clicked.connect(self.flm_clicked)

        icon_reload = QIcon(resource_path("ui/images/reload.png"))
        self.reload_button = QPushButton(self.bar)
        self.reload_button.setIcon(icon_reload)
        self.reload_button.setIconSize(QSize(30, 30))
        self.reload_button.clicked.connect(self.reload_clicked)

        icon_folder = QIcon(resource_path("ui/images/folder.png"))
        self.folder_button = QPushButton(self.bar)
        self.folder_button.setIcon(icon_folder)
        self.folder_button.setIconSize(QSize(30, 30))
        self.folder_button.clicked.connect(self.folder_clicked)

        icon_settings = QIcon(resource_path("ui/images/settings.png"))
        self.settings_button = QPushButton(self.bar)
        self.settings_button.setIcon(icon_settings)
        self.settings_button.setIconSize(QSize(30, 30))
        self.settings_button.clicked.connect(self.settings_clicked)

        for btn in (self.flm_button, self.reload_button, self.folder_button, self.settings_button):
            btn.setFlat(False)
            btn.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            btn.setAutoFillBackground(False)

        self._apply_bar_theme()

    def _apply_bar_theme(self):
        t = self.theme
        layout = t.get("layout", {})
        mode = layout.get("mode", "bar")
        bar_radius = int(t.get("bar_radius", 0))
        input_radius = int(t.get("input_radius", 5))
        combo_radius = int(t.get("combo_radius", 5))
        blur_r = int(t.get("bar_blur", 0))
        bar_bg = t.get("bar_bg", "#71A94C")
        bar_text = t.get("bar_text", "black")
        bar_border = t.get("bar_border", "transparent")
        bar_border_width = int(t.get("bar_border_width", 0))
        accent = t.get("accent", "#3498db")

        if blur_r > 0:
            if mode == "centered":
                self.bar.setStyleSheet(f"""
                    background: transparent;
                    border-radius: {bar_radius}px;
                    border: {bar_border_width}px solid {bar_border};
                """)
            else:
                self.bar.setStyleSheet("background: transparent;")
        else:
            if mode == "centered":
                self.bar.setStyleSheet(f"""
                    background-color: {bar_bg};
                    border-radius: {bar_radius}px;
                    border: {bar_border_width}px solid {bar_border};
                """)
            else:
                self.bar.setStyleSheet(f"background-color: {bar_bg};")

        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {t.get('input_bg', 'white')};
                color: {t.get('input_text', 'black')};
                font-size: {int(t.get('input_font_size', 18))}px;
                font-weight: {t.get('input_font_weight', 'bold')};
                border-radius: {input_radius}px;
                padding: {int(t.get('input_padding_v', 5))}px {int(t.get('input_padding_h', 8))}px;
                border: {int(t.get('input_border_width', 1))}px solid {t.get('input_border', 'transparent')};
            }}
        """)

        self.version_combo.setStyleSheet(f"""
            QComboBox {{ background: transparent; border: none; padding: 0; }}
            QComboBox::drop-down {{ border: none; background: transparent; width: 0px; }}
            QComboBox QAbstractItemView {{
                border: {int(t.get('combo_border_width', 1))}px solid #aaa;
                background-color: {t.get('combo_bg', 'white')};
                color: {t.get('combo_text', 'black')};
                selection-background-color: {accent};
                selection-color: white;
                outline: none;
                padding: 4px;
                min-width: 260px;
                border-radius: {combo_radius}px;
            }}
        """)

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: {int(t.get('progress_border_width', 1))}px solid {t.get('progress_border', 'grey')};
                border-radius: {int(t.get('progress_radius', 5))}px;
                text-align: center;
                background-color: {t.get('progress_track', 'white')};
            }}
            QProgressBar::chunk {{
                background-color: {t.get('progress_chunk', '#05B8CC')};
                width: 10px;
            }}
        """)

        progress_text = t.get("progress_text_color", bar_text)
        progress_size = int(t.get("progress_text_size", 13))
        progress_weight = t.get("progress_text_weight", "bold")
        self.download_info_label.setStyleSheet(f"""
            font-size: {progress_size}px;
            font-weight: {progress_weight};
            color: {progress_text};
            background: transparent;
            border: none;
        """)
        self.download_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.get('cancel_bg', '#ff4444')};
                color: {t.get('cancel_text', 'white')};
                border: none;
                border-radius: {int(t.get('cancel_radius', 3))}px;
                font-size: {int(t.get('cancel_font_size', 11))}px;
            }}
            QPushButton:hover {{ background-color: {t.get('cancel_hover', '#ff5555')}; }}
            QPushButton:disabled {{ background-color: #cccccc; }}
        """)

        self.play_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.get('play_bg', 'rgb(236, 193, 63)')};
                color: {t.get('play_text', 'white')};
                font-size: {int(t.get('play_font_size', 18))}px;
                font-weight: {t.get('play_font_weight', 'bold')};
                border-radius: {int(t.get('play_radius', 5))}px;
                border: {int(t.get('play_border_width', 0))}px solid {t.get('play_border', 'transparent')};
            }}
            QPushButton:hover {{ background-color: {t.get('play_hover', 'rgb(246, 203, 73)')}; }}
            QPushButton:pressed {{ background-color: {t.get('play_pressed', 'rgb(226, 183, 53)')}; }}
        """)

        icon_bg = t.get("icon_bg", "transparent")
        icon_border = t.get("icon_border", "transparent")
        icon_border_width = int(t.get("icon_border_width", 1))
        icon_radius = int(t.get("icon_radius", 5))
        icon_hover = t.get("icon_hover", "rgba(255, 255, 255, 25)")
        icon_pressed = t.get("icon_pressed", icon_hover)

        icon_style = f"""
            QPushButton {{
                border: {icon_border_width}px solid {icon_border};
                background-color: {icon_bg};
                padding: 0;
                outline: none;
                border-radius: {icon_radius}px;
            }}
            QPushButton:flat {{
                background-color: {icon_bg};
                border: {icon_border_width}px solid {icon_border};
            }}
            QPushButton:hover {{
                background-color: {icon_hover};
                border: {icon_border_width}px solid {icon_border};
            }}
            QPushButton:pressed {{
                background-color: {icon_pressed};
                border: {icon_border_width}px solid {icon_border};
            }}
        """
        for btn in (self.flm_button, self.reload_button, self.folder_button, self.settings_button):
            btn.setStyleSheet(icon_style)

        defaults = {
            "flm": "ui/images/FLM.png",
            "reload": "ui/images/reload.png",
            "folder": "ui/images/folder.png",
            "settings": "ui/images/settings.png",
        }
        buttons = {
            "flm": self.flm_button,
            "reload": self.reload_button,
            "folder": self.folder_button,
            "settings": self.settings_button,
        }
        icons = t.get("icons") or {}
        for name, btn in buttons.items():
            if btn is None:
                continue
            path = None
            rel = icons.get(name)
            if rel:
                path = self.theme_manager.resolve_file(rel)
            if path:
                btn.setIcon(QIcon(str(path)))
            else:
                btn.setIcon(QIcon(resource_path(defaults[name])))

    def _blur_pixmap(self, pixmap, radius):
        if pixmap is None or pixmap.isNull() or radius <= 0:
            return pixmap

        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(pixmap)
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(radius)
        blur.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
        item.setGraphicsEffect(blur)
        scene.addItem(item)

        result = QImage(pixmap.size(), QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter)
        painter.end()

        scene.removeItem(item)
        return QPixmap.fromImage(result)

    def _ensure_blur_backdrop(self, widget):
        if widget in self._blur_backdrops:
            bd = self._blur_backdrops[widget]
            try:
                bd.isVisible()
                return bd
            except RuntimeError:
                del self._blur_backdrops[widget]
        bd = BlurredBackdrop(widget)
        bd.hide()
        self._blur_backdrops[widget] = bd
        return bd

    def _update_widget_blur(self, widget, bg_key, blur_key, radius_key):
        if widget is None:
            return

        t = self.theme
        blur_r = int(t.get(blur_key, 0))
        bd = self._ensure_blur_backdrop(widget)

        if blur_r <= 0 or self._background_pixmap is None or self._background_pixmap.isNull():
            bd.hide()
            return

        if widget is self.settings_panel and not getattr(self, "_settings_open", False):
            bd.hide()
            return

        bg = self._background_pixmap

        try:
            top_left = widget.mapTo(self.main, widget.rect().topLeft())
            x, y = top_left.x(), top_left.y()
        except Exception:
            bd.hide()
            return

        w = widget.width()
        h = widget.height()

        if w <= 0 or h <= 0:
            bd.hide()
            return

        bg_w = bg.width()
        bg_h = bg.height()

        crop_x = max(0, min(x, bg_w))
        crop_y = max(0, min(y, bg_h))
        crop_w = max(0, min(w, bg_w - crop_x))
        crop_h = max(0, min(h, bg_h - crop_y))

        if crop_w <= 0 or crop_h <= 0:
            bd.hide()
            return

        cropped = bg.copy(crop_x, crop_y, crop_w, crop_h)
        if cropped.width() != w or cropped.height() != h:
            cropped = cropped.scaled(
                w, h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        blurred = self._blur_pixmap(cropped, blur_r)

        overlay = parse_color(t.get(bg_key, "transparent"))
        if overlay.isValid() and overlay.alpha() > 0:
            p = QPainter(blurred)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            p.fillRect(blurred.rect(), overlay)
            p.end()

        radius = int(t.get(radius_key, 0))
        bd.set_radius(radius)
        bd.set_pixmap(blurred)
        bd.setGeometry(0, 0, w, h)
        bd.show()
        bd.lower()

    def _update_all_blurs(self):
        for widget, bg_key, blur_key, radius_key in self._blur_targets:
            self._update_widget_blur(widget, bg_key, blur_key, radius_key)

    def add_release_panel(self):
        self.release_panel = QWidget(self.main)
        self.release_layout = QVBoxLayout(self.release_panel)
        self.release_layout.setContentsMargins(25, 20, 25, 20)
        self.release_layout.setSpacing(25)
        self.scroll_area = QScrollArea(self.main)
        self.scroll_area.setWidget(self.release_panel)
        self.scroll_area.setWidgetResizable(True)
        self.release_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scroll_area.setAutoFillBackground(False)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: rgba(200, 200, 200, 0.35);
                width: 8px;
                margin: 0px;
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
        self._apply_release_panel_theme()

    def _apply_release_panel_theme(self):
        t = self.theme
        blur_r = int(t.get("release_panel_blur", 0))
        radius = int(t.get("release_panel_radius", 15))
        border_w = int(t.get("release_panel_border_width", 1))
        border_c = t.get("release_panel_border", "rgba(255, 255, 255, 89)")

        if blur_r > 0:
            self.release_panel.setStyleSheet(f"""
                background: transparent;
                border-radius: {radius}px;
                border: {border_w}px solid {border_c};
            """)
        else:
            self.release_panel.setStyleSheet(f"""
                background-color: {t.get('release_panel_bg', 'rgba(255, 255, 255, 217)')};
                border-radius: {radius}px;
                border: {border_w}px solid {border_c};
            """)

        if hasattr(self, "_blur_targets") and self._blur_targets:
            self._update_all_blurs()

    def display_releases(self, releases_data):
        self._last_releases_data = list(releases_data) if releases_data else []

        for i in reversed(range(self.release_layout.count())):
            item = self.release_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        t = self.theme

        if not releases_data:
            no_releases_label = QLabel(tr("releases.empty"))
            no_releases_label.setStyleSheet(f"""
                font-size: 15px;
                color: {t.get('release_text', '#666')};
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
                repo_header = QLabel(tr("releases.repo", repo=repo))
                repo_header.setStyleSheet(f"""
                    font-size: {int(t.get('release_version_size', 16))}px;
                    font-weight: bold;
                    color: {t.get('release_text', '#333')};
                    background: transparent;
                    border: none;
                    padding: 0 0 5px 0;
                """)
                self.release_layout.addWidget(repo_header)

            for release in repo_releases:
                release_widget = ReleaseDisplayWidget(release, theme=t)
                self.release_layout.addWidget(release_widget)

        all_releases_label = QLabel()
        all_releases_label.setText(
            f'<div style="margin-top: 10px;">'
            f'{tr("releases.all_link")}'
            f'<a href="https://github.com/{MAIN_REPO}/releases" '
            f'style="color: {t.get("release_version", "#0066cc")}; text-decoration: none;">'
            f'github.com/{MAIN_REPO}/releases</a></div>'
        )
        all_releases_label.setOpenExternalLinks(True)
        all_releases_label.setStyleSheet(f"""
            font-size: {int(t.get('release_text_size', 14))}px;
            color: {t.get('release_text', '#555')};
            background: transparent;
            border: none;
        """)
        self.release_layout.addWidget(all_releases_label)
        self.release_layout.addStretch(1)

    def show_rate_limit_warning(self, remaining, limit):
        if remaining < 10:
            limit_info = QLabel(tr("releases.rate_limit", remaining=remaining, limit=limit))
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
        self.info_panel = QWidget(self.main)
        info_layout = QVBoxLayout(self.info_panel)
        info_layout.setContentsMargins(15, 20, 15, 20)
        info_layout.setSpacing(15)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        self.header_title = QLabel(tr("info.title"))
        self.header_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.header_title)

        self.header_subtitle = QLabel(tr("info.subtitle"))
        self.header_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.header_subtitle)

        info_layout.addLayout(header_layout)

        button_freshlend = QPushButton("FreshLend Studio")
        button_freshlend.setFixedHeight(40)
        button_freshlend.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://freshlend.github.io")))
        info_layout.addWidget(button_freshlend)
        self.info_buttons.append(button_freshlend)

        button_voxel = QPushButton("VoxelWorld")
        button_voxel.setFixedHeight(40)
        button_voxel.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://voxelworld.ru/profile/84")))
        info_layout.addWidget(button_voxel)
        self.info_buttons.append(button_voxel)

        info_layout.addStretch(1)

        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(5, 0, 5, 0)
        bottom_layout.setSpacing(10)

        self.bottom_platform_label = QLabel(get_platform_name())
        self.bottom_version_label = QLabel(VERSION)

        bottom_layout.addWidget(self.bottom_platform_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.bottom_version_label)
        info_layout.addLayout(bottom_layout)

        self._apply_info_panel_theme()

    def _apply_info_panel_theme(self):
        t = self.theme
        text_color = t.get("info_text", "white")
        blur_r = int(t.get("info_panel_blur", 0))
        radius = int(t.get("info_panel_radius", 15))
        border_w = int(t.get("info_panel_border_width", 1))
        border_c = t.get("info_panel_border", "rgba(255, 255, 255, 51)")

        if blur_r > 0:
            self.info_panel.setStyleSheet(f"""
                background: transparent;
                border-radius: {radius}px;
                border: {border_w}px solid {border_c};
            """)
        else:
            self.info_panel.setStyleSheet(f"""
                background-color: {t.get('info_panel_bg', 'rgba(90, 171, 215, 128)')};
                border-radius: {radius}px;
                border: {border_w}px solid {border_c};
            """)

        self.header_title.setStyleSheet(f"""
            font-size: {int(t.get('info_title_size', 30))}px;
            font-weight: {t.get('info_title_weight', 'bold')};
            color: {text_color};
            background: transparent;
            border: none;
        """)

        self.header_subtitle.setStyleSheet(f"""
            font-size: {int(t.get('info_subtitle_size', 13))}px;
            font-weight: normal;
            color: {text_color};
            background: transparent;
            border: none;
        """)

        btn_style = f"""
            QPushButton {{
                background-color: {t.get('info_btn_bg', 'rgba(62, 148, 182, 217)')};
                font-size: {int(t.get('info_btn_font_size', 16))}px;
                color: {text_color};
                padding: 10px;
                border-radius: {int(t.get('info_btn_radius', 8))}px;
                border: {int(t.get('info_btn_border_width', 1))}px solid {t.get('info_btn_border', 'rgba(255, 255, 255, 77)')};
            }}
            QPushButton:hover {{
                background-color: {t.get('info_btn_hover', 'rgba(72, 158, 192, 242)')};
                border: {int(t.get('info_btn_border_width', 1))}px solid {t.get('info_btn_border_hover', 'rgba(255, 255, 255, 128)')};
            }}
            QPushButton:pressed {{
                background-color: {t.get('info_btn_pressed', 'rgba(52, 138, 172, 255)')};
            }}
        """
        for btn in self.info_buttons:
            btn.setStyleSheet(btn_style)

        bottom_style = f"""
            font-size: {int(t.get('info_meta_size', 13))}px;
            color: {text_color};
            background: transparent;
            border: none;
        """
        self.bottom_platform_label.setStyleSheet(bottom_style)
        self.bottom_version_label.setStyleSheet(bottom_style)

    def add_settings_panel(self):
        t = self.theme

        self.settings_background = QWidget(self.main)
        self.settings_background.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.settings_background.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        self.settings_background.hide()

        self.settings_panel = QWidget(self.main)
        self.settings_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.settings_panel.setAutoFillBackground(False)
        self.settings_panel.hide()

        self.settings_header_strip = QWidget(self.settings_panel)
        self.settings_header_strip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.settings_header_strip.setAutoFillBackground(False)
        blue_layout = QHBoxLayout(self.settings_header_strip)
        blue_layout.setContentsMargins(20, 0, 20, 0)

        self.settings_header_label = QLabel(tr("settings.title"))
        self.settings_header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blue_layout.addWidget(self.settings_header_label)

        blue_layout.addStretch()

        self.settings_close_btn = QPushButton("✕", self.settings_panel)
        self.settings_close_btn.setFixedSize(30, 30)
        self.settings_close_btn.clicked.connect(self.settings_clicked)

        self.tab_widget = FullWidthTabWidget(self.settings_panel, theme=t)
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._create_launch_tab()
        self._create_flauncher_tab()
        self._create_privacy_tab()

        self._apply_settings_panel_theme()

    def _update_settings_backdrop(self):
        layout = self.theme.get("layout", {})
        mode = layout.get("mode", "bar")
        settings_mode = layout.get("settings_mode", "fullscreen")
        backdrop = layout.get("settings_backdrop", "dim")

        if not getattr(self, "_settings_open", False):
            self.settings_background.hide()
            return

        side = mode == "centered" and settings_mode in ("right", "left")

        if side or backdrop == "none":
            self.settings_background.hide()
        else:
            self.settings_background.show()

    def _apply_settings_panel_theme(self):
        t = self.theme
        layout = t.get("layout", {})
        mode = layout.get("mode", "bar")
        settings_mode = layout.get("settings_mode", "fullscreen")
        side = mode == "centered" and settings_mode in ("right", "left")
        panel_radius = int(t.get("settings_panel_radius", t.get("bar_radius", 15)))
        header_text = t.get("settings_header_text", "#ffffff")
        blur_r = int(t.get("settings_blur", 0))

        self.settings_background.setStyleSheet(
            f"background-color: {t.get('settings_backdrop_color', 'rgba(0, 0, 0, 128)')};"
        )

        self.settings_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.settings_panel.setAutoFillBackground(False)
        self.settings_header_strip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.settings_header_strip.setAutoFillBackground(False)

        panel_border = t.get("settings_panel_border", "transparent")
        panel_border_width = int(t.get("settings_panel_border_width", 0))

        if side:
            if blur_r > 0:
                self.settings_panel.setStyleSheet(f"""
                    background: transparent;
                    border: {panel_border_width}px solid {panel_border};
                    border-radius: {panel_radius}px;
                """)
            else:
                self.settings_panel.setStyleSheet(f"""
                    background-color: {t.get('settings_bg', 'rgba(255, 255, 255, 210)')};
                    border: {panel_border_width}px solid {panel_border};
                    border-radius: {panel_radius}px;
                """)
            self.settings_header_strip.setStyleSheet(f"""
                background-color: {t.get('settings_header', 'rgba(235, 235, 235, 150)')};
                border-top-left-radius: {panel_radius}px;
                border-top-right-radius: {panel_radius}px;
            """)
        else:
            if blur_r > 0:
                self.settings_panel.setStyleSheet("background: transparent;")
            else:
                self.settings_panel.setStyleSheet(f"""
                    background-color: {t.get('settings_bg', '#f5f5f5')};
                    border-radius: 0px;
                """)
            self.settings_header_strip.setStyleSheet(
                f"background-color: {t.get('settings_header', '#0086c7')};"
            )

        self._apply_settings_header_theme(header_text)
        self._apply_settings_tabs_theme()
        self._apply_settings_groups_theme(side)
        self._apply_settings_inputs_theme()
        self._apply_settings_checkboxes_theme()
        self._apply_settings_buttons_theme()

        for lbl in self.settings_labels:
            lbl.setStyleSheet(f"""
                font-size: {int(t.get('group_title_size', 13))}px;
                color: {t.get('group_title_text', '#555')};
                background: transparent;
                border: none;
            """)

        if self.launch_params_label:
            self.launch_params_label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.launch_params_label.setStyleSheet(f"""
                font-size: 15px;
                font-weight: bold;
                color: {t.get('group_title_text', '#333')};
                background-color: {t.get('group_title_bg', '#F5F5F5')};
                padding: 8px 15px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            """)

        if self.discord_toggle:
            self.discord_toggle.set_theme(t)
        if self.artifacts_toggle:
            self.artifacts_toggle.set_theme(t)

    def _apply_settings_header_theme(self, header_text):
        t = self.theme
        self.settings_header_label.setStyleSheet(f"""
            font-size: {int(t.get('settings_header_size', 20))}px;
            font-weight: {t.get('settings_header_weight', 'bold')};
            color: {header_text};
            background: transparent;
            border: none;
        """)

        close_hover = t.get("settings_close_hover_bg", "rgba(0, 0, 0, 40)")
        close_size = int(t.get("settings_close_size", 20))
        self.settings_close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {header_text};
                font-size: {close_size}px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {close_hover};
                border-radius: 15px;
            }}
        """)

    def _apply_settings_tabs_theme(self):
        t = self.theme
        if self.tab_widget:
            self.tab_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.tab_widget.setAutoFillBackground(False)
            self.tab_widget.set_theme(t)

        for tab in (self.launch_tab, self.flauncher_tab, self.privacy_tab):
            if tab:
                tab.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                tab.setAutoFillBackground(False)
                tab.setStyleSheet("background: transparent; border: none;")
                for sa in tab.findChildren(QScrollArea):
                    sa.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                    sa.setAutoFillBackground(False)
                    sa.viewport().setAutoFillBackground(False)
                    sa.viewport().setStyleSheet("background: transparent;")

    def _apply_settings_groups_theme(self, side):
        t = self.theme
        for group, title_label, content, key in self.group_boxes:
            group.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            group.setAutoFillBackground(False)
            content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            content.setAutoFillBackground(False)
            title_label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            title_label.setAutoFillBackground(False)

            group_radius = int(t.get("group_radius", 5))
            group.setStyleSheet(f"""
                #settingsGroupBox {{
                    background-color: {t.get('group_body_bg', 'white')};
                    border: {int(t.get('group_border_width', 1))}px solid {t.get('group_border', '#E0E0E0')};
                    border-radius: {group_radius}px;
                }}
            """)
            title_label.setStyleSheet(f"""
                font-size: {int(t.get('group_title_size', 14))}px;
                font-weight: {t.get('group_title_weight', 'bold')};
                color: {t.get('group_title_text', '#333')};
                background-color: {t.get('group_title_bg', '#F5F5F5')};
                padding: {int(t.get('group_title_padding_v', 8))}px {int(t.get('group_title_padding_h', 15))}px;
                border-top-left-radius: {group_radius}px;
                border-top-right-radius: {group_radius}px;
                border-bottom: {int(t.get('group_border_width', 1))}px solid {t.get('group_border', '#E0E0E0')};
            """)

    def _apply_settings_inputs_theme(self):
        t = self.theme
        input_qss = f"""
            QLineEdit {{
                border: {int(t.get('input_field_border_width', 1))}px solid {t.get('input_field_border', '#CCC')};
                padding: {int(t.get('input_field_padding_v', 6))}px {int(t.get('input_field_padding_h', 10))}px;
                font-size: {int(t.get('input_field_font_size', 13))}px;
                background-color: {t.get('input_field_bg', 'white')};
                color: {t.get('input_field_text', 'black')};
                border-radius: {int(t.get('input_field_radius', 3))}px;
            }}
            QLineEdit:focus {{
                border: {int(t.get('input_field_border_width', 1))}px solid {t.get('input_field_focus', '#0086c7')};
            }}
        """
        if self.additional_args_input:
            self.additional_args_input.setStyleSheet(input_qss)
        if self.github_token_input:
            self.github_token_input.setStyleSheet(input_qss)

        combo_qss = f"""
            QComboBox {{
                border: {int(t.get('input_field_border_width', 1))}px solid {t.get('input_field_border', '#CCC')};
                padding: {int(t.get('input_field_padding_v', 6))}px {int(t.get('input_field_padding_h', 10))}px;
                font-size: {int(t.get('input_field_font_size', 13))}px;
                background-color: {t.get('input_field_bg', 'white')};
                color: {t.get('input_field_text', 'black')};
                border-radius: {int(t.get('input_field_radius', 3))}px;
            }}
            QComboBox:focus {{
                border: {int(t.get('input_field_border_width', 1))}px solid {t.get('input_field_focus', '#0086c7')};
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background-color: {t.get('input_field_bg', 'white')};
                color: {t.get('input_field_text', 'black')};
                selection-background-color: {t.get('accent', '#3498db')};
                selection-color: white;
                outline: none;
                border: {int(t.get('input_field_border_width', 1))}px solid {t.get('input_field_border', '#CCC')};
            }}
        """
        if self.theme_combo:
            self.theme_combo.setStyleSheet(combo_qss)
        if self.language_combo:
            self.language_combo.setStyleSheet(combo_qss)

        if self.artifacts_count_spin:
            self.artifacts_count_spin.setStyleSheet(f"""
                QSpinBox {{
                    border: {int(t.get('input_field_border_width', 1))}px solid {t.get('input_field_border', '#CCC')};
                    padding: 4px 8px;
                    font-size: {int(t.get('input_field_font_size', 13))}px;
                    background-color: {t.get('input_field_bg', 'white')};
                    color: {t.get('input_field_text', 'black')};
                    border-radius: {int(t.get('input_field_radius', 3))}px;
                }}
                QSpinBox::up-button, QSpinBox::down-button {{
                    background-color: {t.get('group_title_bg', '#F0F0F0')};
                    border: none;
                    width: 18px;
                }}
            """)

        if self.repos_scroll:
            self.repos_scroll.setStyleSheet(f"""
                QScrollArea {{
                    border: {int(t.get('group_border_width', 1))}px solid {t.get('group_border', '#DDD')};
                    background-color: {t.get('group_body_bg', 'white')};
                    border-radius: {int(t.get('group_radius', 3))}px;
                }}
                QScrollBar:vertical {{
                    border: none;
                    background-color: {t.get('group_title_bg', '#F0F0F0')};
                    width: 10px;
                    margin: 0px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: #C0C0C0;
                    min-height: 20px;
                    border-radius: 5px;
                }}
            """)

    def _apply_settings_checkboxes_theme(self):
        t = self.theme
        checkbox_qss = f"""
            QCheckBox {{
                font-size: {int(t.get('checkbox_font_size', 13))}px;
                color: {t.get('checkbox_text', '#333')};
                spacing: 6px;
                background: transparent;
                border: none;
            }}
            QCheckBox::indicator {{
                width: {int(t.get('checkbox_size', 16))}px;
                height: {int(t.get('checkbox_size', 16))}px;
                border: {int(t.get('checkbox_border_width', 1))}px solid {t.get('checkbox_border', '#999')};
                border-radius: 3px;
                background-color: {t.get('input_field_bg', 'white')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {t.get('checkbox_checked_bg', '#2ecc71')};
                border: {int(t.get('checkbox_border_width', 1))}px solid {t.get('checkbox_checked_border', '#27ae60')};
            }}
        """
        for cb in (self.msvc_checkbox, self.clang_checkbox):
            if cb:
                cb.setStyleSheet(checkbox_qss)

    def _apply_settings_buttons_theme(self):
        t = self.theme

        if self.open_themes_button:
            self.open_themes_button.setStyleSheet(f"""
                QPushButton {{
                    font-size: {int(t.get('open_themes_btn_font_size', 13))}px;
                    font-weight: {t.get('open_themes_btn_font_weight', 'normal')};
                    background-color: {t.get('open_themes_btn_bg', '#3498db')};
                    color: {t.get('open_themes_btn_text', 'white')};
                    padding: 6px 15px;
                    border: {int(t.get('open_themes_btn_border_width', 0))}px solid {t.get('open_themes_btn_border', 'transparent')};
                    border-radius: {int(t.get('open_themes_btn_radius', 3))}px;
                }}
                QPushButton:hover {{ background-color: {t.get('open_themes_btn_hover', '#2980b9')}; }}
                QPushButton:pressed {{ background-color: {t.get('open_themes_btn_pressed', '#1f5f8f')}; }}
            """)

        if self.refresh_releases_button:
            self.refresh_releases_button.setStyleSheet(f"""
                QPushButton {{
                    font-size: {int(t.get('refresh_releases_btn_font_size', 13))}px;
                    font-weight: {t.get('refresh_releases_btn_font_weight', 'normal')};
                    background-color: {t.get('refresh_releases_btn_bg', '#4CAF50')};
                    color: {t.get('refresh_releases_btn_text', 'white')};
                    padding: 6px 15px;
                    border: {int(t.get('refresh_releases_btn_border_width', 0))}px solid {t.get('refresh_releases_btn_border', 'transparent')};
                    border-radius: {int(t.get('refresh_releases_btn_radius', 3))}px;
                }}
                QPushButton:hover {{ background-color: {t.get('refresh_releases_btn_hover', '#45a049')}; }}
                QPushButton:pressed {{ background-color: {t.get('refresh_releases_btn_pressed', '#3d8b40')}; }}
            """)

        if self.add_repo_button:
            self.add_repo_button.setStyleSheet(f"""
                QPushButton {{
                    font-size: {int(t.get('add_repo_btn_font_size', 13))}px;
                    font-weight: {t.get('add_repo_btn_font_weight', 'normal')};
                    background-color: {t.get('add_repo_btn_bg', '#4CAF50')};
                    color: {t.get('add_repo_btn_text', 'white')};
                    padding: 6px 15px;
                    border: {int(t.get('add_repo_btn_border_width', 0))}px solid {t.get('add_repo_btn_border', 'transparent')};
                    border-radius: {int(t.get('add_repo_btn_radius', 3))}px;
                }}
                QPushButton:hover {{ background-color: {t.get('add_repo_btn_hover', '#45a049')}; }}
                QPushButton:pressed {{ background-color: {t.get('add_repo_btn_pressed', '#3d8b40')}; }}
            """)

        if self.check_token_button:
            self.check_token_button.setStyleSheet(f"""
                QPushButton {{
                    font-size: {int(t.get('check_token_btn_font_size', 13))}px;
                    font-weight: {t.get('check_token_btn_font_weight', 'normal')};
                    background-color: {t.get('check_token_btn_bg', '#2196F3')};
                    color: {t.get('check_token_btn_text', 'white')};
                    padding: 6px 15px;
                    border: {int(t.get('check_token_btn_border_width', 0))}px solid {t.get('check_token_btn_border', 'transparent')};
                    border-radius: {int(t.get('check_token_btn_radius', 3))}px;
                }}
                QPushButton:hover {{ background-color: {t.get('check_token_btn_hover', '#1976D2')}; }}
                QPushButton:pressed {{ background-color: {t.get('check_token_btn_pressed', '#0D47A1')}; }}
            """)

        if self.reload_theme_btn:
            self.reload_theme_btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: {int(t.get('reload_theme_btn_font_size', 16))}px;
                    font-weight: bold;
                    background-color: {t.get('reload_theme_btn_bg', 'white')};
                    color: {t.get('reload_theme_btn_text', 'black')};
                    border: {int(t.get('reload_theme_btn_border_width', 1))}px solid {t.get('reload_theme_btn_border', '#CCC')};
                    border-radius: {int(t.get('reload_theme_btn_radius', 3))}px;
                }}
                QPushButton:hover {{
                    background-color: {t.get('reload_theme_btn_hover', '#3498db')};
                    color: {t.get('reload_theme_btn_hover_text', 'white')};
                    border: {int(t.get('reload_theme_btn_border_width', 1))}px solid {t.get('reload_theme_btn_hover', '#3498db')};
                }}
                QPushButton:pressed {{
                    background-color: {t.get('reload_theme_btn_pressed', '#2980b9')};
                    color: {t.get('reload_theme_btn_hover_text', 'white')};
                }}
                QToolTip {{
                    background-color: {t.get('tooltip_bg', 'white')};
                    color: {t.get('tooltip_text', 'black')};
                    border: {int(t.get('tooltip_border_width', 1))}px solid {t.get('tooltip_border', '#CCC')};
                    padding: 6px 10px;
                    border-radius: {int(t.get('tooltip_radius', 4))}px;
                }}
            """)

    def _create_launch_tab(self):
        t = self.theme
        self.launch_tab = QWidget()

        outer = QVBoxLayout(self.launch_tab)
        outer.setContentsMargins(30, 25, 30, 25)
        outer.setSpacing(8)

        self.launch_params_label = QLabel(tr("settings.launch_params"))
        outer.addWidget(self.launch_params_label)

        self.additional_args_input = QLineEdit()
        self.additional_args_input.textChanged.connect(self.launch_params_changed)
        self.additional_args_input.setPlaceholderText(tr("settings.launch_params_hint"))
        outer.addWidget(self.additional_args_input)
        outer.addStretch(1)

        self.tab_widget.addTab(self.launch_tab, tr("settings.tab.voxelcore"))

    def _create_flauncher_tab(self):
        t = self.theme
        self.flauncher_tab = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        scroll.setAutoFillBackground(False)
        scroll.viewport().setAutoFillBackground(False)
        scroll.viewport().setStyleSheet("background: transparent;")
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)

        content = QWidget()
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content.setAutoFillBackground(False)
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        theme_group, theme_container, theme_title = self._create_group_box("settings.theme_group")
        th_layout = QVBoxLayout(theme_container)
        th_layout.setContentsMargins(20, 15, 20, 15)
        th_layout.setSpacing(10)

        self.theme_desc_label = QLabel(tr("settings.theme_desc"))
        self.theme_desc_label.setWordWrap(True)
        self.settings_labels.append(self.theme_desc_label)
        th_layout.addWidget(self.theme_desc_label)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(10)

        self.theme_combo = QComboBox()
        self._populate_theme_combo()
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)

        self.reload_theme_btn = QPushButton("↻")
        self.reload_theme_btn.setFixedSize(30, 30)
        self.reload_theme_btn.setToolTip(tr("settings.reload_tooltip"))
        self.reload_theme_btn.clicked.connect(self._on_reload_theme)

        self.open_themes_button = QPushButton(tr("settings.open_folder"))
        self.open_themes_button.setFixedHeight(30)
        self.open_themes_button.clicked.connect(self._on_open_themes_folder)

        theme_row.addWidget(self.theme_combo, 1)
        theme_row.addWidget(self.reload_theme_btn)
        theme_row.addWidget(self.open_themes_button)
        th_layout.addLayout(theme_row)

        layout.addWidget(theme_group)

        language_group, language_container, language_title = self._create_group_box("settings.language_group")
        l_layout = QVBoxLayout(language_container)
        l_layout.setContentsMargins(20, 15, 20, 15)
        l_layout.setSpacing(10)

        self.language_desc_label = QLabel(tr("settings.language_desc"))
        self.language_desc_label.setWordWrap(True)
        self.settings_labels.append(self.language_desc_label)
        l_layout.addWidget(self.language_desc_label)

        self.language_combo = QComboBox()
        for code, name in i18n.available():
            self.language_combo.addItem(name, code)
        current_lang = self.settings_manager.get_language()
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
        self.language_combo.currentIndexChanged.connect(self._on_language_combo_changed)
        l_layout.addWidget(self.language_combo)
        layout.addWidget(language_group)

        artifacts_group, artifacts_container, artifacts_title = self._create_group_box("settings.artifacts_group")
        a_layout = QVBoxLayout(artifacts_container)
        a_layout.setContentsMargins(20, 15, 20, 15)
        a_layout.setSpacing(12)

        row1 = QHBoxLayout()
        row1.setSpacing(15)

        self.artifacts_toggle = ToggleSwitch(theme=t)
        self.artifacts_toggle.toggled.connect(self.artifacts_toggled.emit)

        self.artifacts_desc_label = QLabel(tr("settings.artifacts_desc"))
        self.artifacts_desc_label.setWordWrap(True)
        self.settings_labels.append(self.artifacts_desc_label)

        row1.addWidget(self.artifacts_toggle, alignment=Qt.AlignmentFlag.AlignVCenter)
        row1.addWidget(self.artifacts_desc_label, 1)
        a_layout.addLayout(row1)

        self.artifacts_count_group = QWidget()
        self.artifacts_count_group.setStyleSheet("background: transparent; border: none;")
        count_layout = QHBoxLayout(self.artifacts_count_group)
        count_layout.setContentsMargins(63, 0, 0, 0)
        count_layout.setSpacing(20)

        self.count_label = QLabel(tr("settings.artifacts_count"))
        self.settings_labels.append(self.count_label)

        self.artifacts_count_spin = QSpinBox()
        self.artifacts_count_spin.setRange(1, 50)
        self.artifacts_count_spin.setFixedWidth(80)
        self.artifacts_count_spin.valueChanged.connect(self.artifacts_count_changed)

        count_layout.addWidget(self.count_label)
        count_layout.addWidget(self.artifacts_count_spin)

        if self.settings_manager.system == 'win32':
            self.windows_group = QWidget()
            self.windows_group.setStyleSheet("background: transparent; border: none;")
            w_layout = QHBoxLayout(self.windows_group)
            w_layout.setContentsMargins(0, 0, 0, 0)
            w_layout.setSpacing(20)

            self.msvc_checkbox = QCheckBox("MSVC")
            self.msvc_checkbox.stateChanged.connect(
                lambda state: self.windows_build_type_changed.emit('msvc', state == Qt.CheckState.Checked.value)
            )
            w_layout.addWidget(self.msvc_checkbox)

            self.clang_checkbox = QCheckBox("CLang")
            self.clang_checkbox.stateChanged.connect(
                lambda state: self.windows_build_type_changed.emit('clang', state == Qt.CheckState.Checked.value)
            )
            w_layout.addWidget(self.clang_checkbox)

            count_layout.addWidget(self.windows_group)

        count_layout.addStretch()
        a_layout.addWidget(self.artifacts_count_group)
        layout.addWidget(artifacts_group)

        github_group, github_container, github_title = self._create_group_box("settings.repos_group")
        g_layout = QVBoxLayout(github_container)
        g_layout.setContentsMargins(20, 15, 20, 15)
        g_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.github_desc_label = QLabel(tr("settings.repos_desc"))
        self.settings_labels.append(self.github_desc_label)

        self.add_repo_button = QPushButton(tr("settings.repos_add"))
        self.add_repo_button.setFixedHeight(30)
        self.add_repo_button.clicked.connect(self.add_repo_clicked)

        top_row.addWidget(self.github_desc_label)
        top_row.addStretch()
        top_row.addWidget(self.add_repo_button)
        g_layout.addLayout(top_row)

        self.repos_scroll = QScrollArea()
        self.repos_scroll.setWidgetResizable(True)
        self.repos_scroll.setFixedHeight(120)

        self.repos_container = QWidget()
        self.repos_container.setStyleSheet("background: transparent; border: none;")
        self.repos_layout = QVBoxLayout(self.repos_container)
        self.repos_layout.setContentsMargins(5, 5, 5, 5)
        self.repos_layout.setSpacing(4)
        self.repos_layout.addStretch()
        self.repos_scroll.setWidget(self.repos_container)
        g_layout.addWidget(self.repos_scroll)
        layout.addWidget(github_group)

        token_group, token_container, token_title = self._create_group_box("settings.token_group")
        t_layout = QVBoxLayout(token_container)
        t_layout.setContentsMargins(20, 15, 20, 15)
        t_layout.setSpacing(10)

        self.token_desc_label = QLabel(tr("settings.token_desc"))
        self.settings_labels.append(self.token_desc_label)
        t_layout.addWidget(self.token_desc_label)

        token_row = QHBoxLayout()
        token_row.setSpacing(10)

        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.github_token_input.textChanged.connect(self.github_token_changed)
        self.github_token_input.setPlaceholderText(tr("settings.token_placeholder"))

        self.check_token_button = QPushButton(tr("settings.token_check"))
        self.check_token_button.setFixedHeight(30)
        self.check_token_button.clicked.connect(self.check_token_clicked)

        self.refresh_releases_button = QPushButton(tr("settings.token_refresh"))
        self.refresh_releases_button.setFixedHeight(30)
        self.refresh_releases_button.clicked.connect(self.refresh_releases_clicked)

        token_row.addWidget(self.github_token_input, 1)
        token_row.addWidget(self.check_token_button)
        token_row.addWidget(self.refresh_releases_button)
        t_layout.addLayout(token_row)

        self.token_status_label = QLabel('')
        self.token_status_label.setWordWrap(True)
        t_layout.addWidget(self.token_status_label)
        layout.addWidget(token_group)

        layout.addStretch(1)
        scroll.setWidget(content)

        outer = QVBoxLayout(self.flauncher_tab)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self.tab_widget.addTab(self.flauncher_tab, tr("settings.tab.flauncher"))

    def _create_privacy_tab(self):
        t = self.theme
        self.privacy_tab = QWidget()

        layout = QVBoxLayout(self.privacy_tab)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        discord_group, discord_container, discord_title = self._create_group_box("settings.discord_group")
        d_layout = QVBoxLayout(discord_container)
        d_layout.setContentsMargins(20, 15, 20, 15)
        d_layout.setSpacing(12)

        row = QHBoxLayout()
        row.setSpacing(15)

        self.discord_toggle = ToggleSwitch(theme=t)
        self.discord_toggle.toggled.connect(self.discord_toggled.emit)

        self.discord_desc_label = QLabel(tr("settings.discord_desc"))
        self.discord_desc_label.setWordWrap(True)
        self.settings_labels.append(self.discord_desc_label)

        row.addWidget(self.discord_toggle, alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.discord_desc_label, 1)
        d_layout.addLayout(row)

        layout.addWidget(discord_group)
        layout.addStretch(1)

        self.tab_widget.addTab(self.privacy_tab, tr("settings.tab.privacy"))

    def _create_group_box(self, title_key):
        group_box = QWidget()
        group_box.setObjectName("settingsGroupBox")
        group_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        main_layout = QVBoxLayout(group_box)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_label = QLabel(tr(title_key))
        title_label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        main_layout.addWidget(title_label)

        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content_container.setStyleSheet("background: transparent; border: none;")
        main_layout.addWidget(content_container)

        self.group_boxes.append((group_box, title_label, content_container, title_key))
        return group_box, content_container, title_label

    def _populate_theme_combo(self):
        if self.theme_combo is None:
            return
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        for key, label in self.theme_manager.all_labels():
            self.theme_combo.addItem(label, key)
        current_key = self.theme_manager.current_key
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current_key:
                self.theme_combo.setCurrentIndex(i)
                break
        self.theme_combo.blockSignals(False)

    def _on_theme_combo_changed(self, index):
        if index < 0:
            return
        key = self.theme_combo.itemData(index)
        if not key:
            return
        if key == self.theme_manager.current_key:
            return
        self.theme_selected.emit(key)

    def _on_language_combo_changed(self, index):
        if index < 0 or self.language_combo is None:
            return
        code = self.language_combo.itemData(index)
        if not code:
            return
        if code == self.settings_manager.get_language():
            return
        self.language_selected.emit(code)

    def _on_reload_theme(self):
        saved_key = self.theme_manager.current_key

        self.theme_manager.reload()

        if saved_key in self.theme_manager.themes:
            self.theme_manager.current_key = saved_key
        elif self.theme_manager.themes:
            self.theme_manager.current_key = next(iter(self.theme_manager.themes))

        self.theme = self.theme_manager.current

        self._populate_theme_combo()

        i18n.set_theme_overrides(
            self.theme_manager.get_text_overrides(i18n.current())
        )
        self.retranslate_ui()

        self.apply_theme()

        widgets = [
            self.main,
            self.bar,
            self.release_panel,
            self.info_panel,
            self.settings_panel,
            self.settings_header_strip,
            self.FL_MODS,
            self.flmods_header_strip,
        ]
        for w in widgets:
            if w is None:
                continue
            try:
                w.style().unpolish(w)
                w.style().polish(w)
                w.update()
            except Exception:
                pass

    def refresh_themes_combo(self):
        if self.theme_combo is None:
            return
        self.theme_manager.reload()

        if self.theme_manager.current_key not in self.theme_manager.themes \
           and self.theme_manager.themes:
            self.theme_manager.current_key = next(iter(self.theme_manager.themes))

        self.theme = self.theme_manager.current

        i18n.set_theme_overrides(
            self.theme_manager.get_text_overrides(i18n.current())
        )
        self.retranslate_ui()

        self._populate_theme_combo()

    def _on_open_themes_folder(self):
        self.open_themes_folder_clicked.emit()

    def add_fl_mods_panel(self):
        self.FL_MODS_background = QWidget(self.main)
        self.FL_MODS_background.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.FL_MODS_background.hide()

        self.FL_MODS = QWidget(self.main)
        self.FL_MODS.hide()

        self.flmods_header_strip = QWidget(self.FL_MODS)
        blue_layout = QHBoxLayout(self.flmods_header_strip)
        blue_layout.setContentsMargins(20, 0, 20, 0)

        self.flmods_header_label = QLabel(tr("flmods.title"))
        self.flmods_header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blue_layout.addWidget(self.flmods_header_label)

        self.flmods_version_label = QLabel(tr("flmods.version_label"))
        blue_layout.addWidget(self.flmods_version_label)

        self.mods_version_combo = QComboBox()
        self.mods_version_combo.setMinimumWidth(280)
        self.mods_version_combo.currentTextChanged.connect(self._on_mods_version_changed)
        blue_layout.addWidget(self.mods_version_combo)

        blue_layout.addStretch()

        self.flmods_close_btn = QPushButton("✕", self.FL_MODS)
        self.flmods_close_btn.setFixedSize(30, 30)
        self.flmods_close_btn.clicked.connect(self.flm_clicked)

        layout = QVBoxLayout(self.FL_MODS)
        layout.setContentsMargins(0, 50, 0, 0)
        self.mods_widget = ModsWidget(
            self.settings_manager,
            self.main.thread_manager,
            theme_manager=self.theme_manager,
        )
        layout.addWidget(self.mods_widget)

        self._apply_flmods_theme()

    def _apply_flmods_theme(self):
        t = self.theme
        flmods_blur = int(t.get("flmods_blur", 0))

        if flmods_blur > 0:
            self.FL_MODS.setStyleSheet("background: transparent;")
        else:
            self.FL_MODS.setStyleSheet(f"""
                background-color: {t.get('flmods_bg', t.get('settings_bg', '#f5f5f5'))};
                border-radius: 0px;
            """)
        self.flmods_header_strip.setStyleSheet(
            f"background-color: {t.get('flmods_header', '#00aaff')};"
        )
        self.flmods_header_label.setStyleSheet(f"""
            font-size: {int(t.get('flmods_header_size', 20))}px;
            font-weight: {t.get('flmods_header_weight', 'bold')};
            color: {t.get('flmods_header_text', 'white')};
            background: transparent;
            border: none;
        """)
        self.flmods_version_label.setStyleSheet(
            f"color: {t.get('flmods_header_text', 'white')}; "
            f"font-size: 14px; margin-left: 30px; background: transparent; border: none;"
        )
        self.mods_version_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {t.get('combo_bg', 'white')};
                color: {t.get('combo_text', 'black')};
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid #aaa;
                background-color: {t.get('combo_bg', 'white')};
                color: {t.get('combo_text', 'black')};
                selection-background-color: {t.get('accent', '#3498db')};
                selection-color: white;
                outline: none;
            }}
        """)
        self.flmods_close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {t.get('flmods_header_text', 'white')};
                font-size: 20px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }}
        """)

        if self.mods_widget is not None:
            try:
                self.mods_widget.theme_manager = self.theme_manager
                self.mods_widget.apply_theme()
                self.mods_widget.installed_sidebar.apply_theme()
            except Exception:
                pass

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
        if not version or version == tr("status.getting_versions"):
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
            self.input_field.setPlaceholderText(tr("input.nick_placeholder"))

    def load_github_repositories(self, repos):
        if self.repos_layout:
            for i in reversed(range(self.repos_layout.count())):
                widget = self.repos_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
        for repo in repos:
            self._add_repository_to_list(repo)

    def _add_repository_to_list(self, repo):
        t = self.theme
        repo_widget = QWidget()
        repo_widget.setStyleSheet(
            f"background-color: {t.get('group_title_bg', '#f5f5f5')}; border-radius: 3px; border: none;"
        )
        repo_layout = QHBoxLayout(repo_widget)
        repo_layout.setContentsMargins(10, 4, 10, 4)

        repo_label = QLabel(repo)
        repo_label.setStyleSheet(
            f"font-size: 13px; border: none; background: transparent; color: {t.get('group_title_text', '#333')};"
        )
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
        self._settings_open = True
        self._apply_layout()
        self._update_settings_backdrop()

        self.settings_background.raise_()
        self.settings_panel.show()
        self.settings_panel.raise_()

        layout = self.theme.get("layout", {})
        if layout.get("mode", "bar") == "centered":
            self.bar.raise_()

        self._update_all_blurs()

    def hide_settings(self):
        self._settings_open = False
        self._apply_layout()
        self._update_settings_backdrop()
        self.settings_panel.hide()
        self._update_all_blurs()

    def show_flmods(self):
        self.FL_MODS_background.show()
        self.FL_MODS.show()
        self.FL_MODS_background.raise_()
        self.FL_MODS.raise_()
        self._update_all_blurs()

    def hide_flmods(self):
        self.FL_MODS_background.hide()
        self.FL_MODS.hide()
        self._update_all_blurs()

    def update_token_status(self, status_text, color_code):
        self.token_status_label.setText(status_text)
        self.token_status_label.setStyleSheet(f"color: {color_code}; background: transparent; border: none;")

    def get_mods_widget(self):
        return self.mods_widget

    def update_mods_installed_status(self, installed_mods_set):
        if hasattr(self, 'mods_widget'):
            self.mods_widget.set_installed_items(installed_mods_set)