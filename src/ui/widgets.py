from PyQt6.QtWidgets import (
    QWidget, QComboBox, QTabWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout,
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QPen,
)
from PyQt6.QtCore import Qt, QRectF


def parse_color(s):
    if not s or not isinstance(s, str):
        return QColor()
    s = s.strip()
    if s.startswith("rgba(") and s.endswith(")"):
        try:
            parts = [p.strip() for p in s[5:-1].split(",")]
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = int(parts[3]) if len(parts) > 3 else 255
            return QColor(r, g, b, a)
        except Exception:
            return QColor()
    if s.startswith("rgb(") and s.endswith(")"):
        try:
            parts = [p.strip() for p in s[4:-1].split(",")]
            return QColor(int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception:
            return QColor()
    if s.startswith("#") and len(s) == 9:
        try:
            a = int(s[1:3], 16)
            r = int(s[3:5], 16)
            g = int(s[5:7], 16)
            b = int(s[7:9], 16)
            return QColor(r, g, b, a)
        except Exception:
            return QColor()
    return QColor(s)


class FullWidthTabWidget(QTabWidget):
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.tabBar().setExpanding(True)
        self.tabBar().setDrawBase(False)
        self._update_style()

    def set_theme(self, theme):
        self.theme = theme
        self._update_style()

    def _update_style(self):
        count = max(self.count(), 1)
        w = max(self.width() // count - 3, 60)
        t = self.theme
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet(f"""
            QTabWidget {{ background: transparent; border: none; }}
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabWidget > QStackedWidget {{ background: transparent; }}
            QTabWidget > QStackedWidget > QWidget {{ background: transparent; }}
            QTabBar {{ background: transparent; }}
            QTabBar::tab {{
                background-color: {t.get('settings_tab_bg', '#E4E4E4')};
                border: none;
                padding: {int(t.get('settings_tab_padding_v', 10))}px 0px;
                margin: 0px 2px 0px 0px;
                font-size: {int(t.get('settings_tab_font_size', 14))}px;
                font-weight: {t.get('settings_tab_font_weight', 'normal')};
                color: {t.get('settings_tab_text', '#333')};
                width: {w}px;
            }}
            QTabBar::tab:selected {{
                background-color: {t.get('settings_tab_active', '#0086c7')};
                color: {t.get('settings_tab_active_text', 'white')};
                font-weight: {t.get('settings_tab_active_weight', 'bold')};
            }}
            QTabBar::tab:!selected {{
                background-color: {t.get('settings_tab_bg', '#E4E4E4')};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {t.get('settings_tab_hover', '#D8D8D8')};
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_style()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_style()


class ToggleSwitch(QPushButton):
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.setCheckable(True)
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def set_theme(self, theme):
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 2

        track_path = QPainterPath()
        track_path.addRoundedRect(rect, radius, radius)

        on_bg = parse_color(self.theme.get("toggle_on_bg", "#4CAF50"))
        off_bg = parse_color(self.theme.get("toggle_off_bg", "#BDBDBD"))

        if self.isChecked():
            color = on_bg
            if self.underMouse():
                color = color.lighter(110)
        else:
            color = off_bg
            if self.underMouse():
                color = color.lighter(110)

        painter.fillPath(track_path, color)

        thumb_size = self.height() - 4
        if self.isChecked():
            thumb_x = self.width() - thumb_size - 2
        else:
            thumb_x = 2

        thumb_color = parse_color(self.theme.get("toggle_thumb", "white"))
        painter.setBrush(thumb_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(thumb_x, 2, thumb_size, thumb_size))

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()


class ArrowComboBox(QComboBox):
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or {}
        self._popup_open = False

    def set_theme(self, theme):
        self.theme = theme
        self.update()

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
        t = self.theme

        bg_color = parse_color(t.get("combo_bg", "white"))
        text_color = parse_color(t.get("combo_text", "#1e1e1e"))
        arrow_color = parse_color(t.get("combo_arrow", "#1e1e1e"))
        focus_color = parse_color(t.get("combo_focus", "#3498db"))

        radius = int(t.get("combo_radius", 5))
        font_size = int(t.get("combo_font_size", 14))
        font_weight = t.get("combo_font_weight", "bold")

        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(rect), radius, radius)
        painter.fillPath(bg_path, bg_color)

        font = self.font()
        font.setPointSize(font_size)
        font.setBold(font_weight == "bold")
        painter.setFont(font)
        painter.setPen(text_color)

        text_rect = rect.adjusted(12, 0, -42, 0)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.currentText()
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(arrow_color)

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
            painter.setPen(QPen(focus_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(rect).adjusted(1, 1, -1, -1), radius, radius)


class BlurredBackdrop(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.radius = 0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def set_radius(self, radius):
        self.radius = int(radius)
        self.update()

    def paintEvent(self, event):
        if self.pixmap is None or self.pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = QRectF(self.rect())
        r = min(self.radius, rect.width() / 2, rect.height() / 2)
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        painter.setClipPath(path)
        painter.drawPixmap(self.rect(), self.pixmap)


class ReleaseDisplayWidget(QWidget):
    def __init__(self, release_data, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.release_data = release_data
        self.version_label = None
        self.date_label = None
        self.body_label = None
        self._build()
        self._apply_styles()

    def _build(self):
        data = self.release_data
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.version_label = QLabel()
        self.version_label.setOpenExternalLinks(True)

        self.date_label = QLabel(data.get("date", ""))

        header_layout.addWidget(self.version_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.date_label)
        layout.addLayout(header_layout)

        if data.get('body_html'):
            self.body_label = QLabel()
            self.body_label.setOpenExternalLinks(True)
            self.body_label.setText(data['body_html'])
            self.body_label.setWordWrap(True)
            layout.addWidget(self.body_label)

    def _apply_styles(self):
        t = self.theme
        data = self.release_data
        version_color = t.get("release_version", "#0066cc")

        if self.version_label:
            self.version_label.setText(
                f'<a href="{data.get("release_url", "#")}" '
                f'style="color: {version_color}; text-decoration: none;">'
                f'VoxelCore {data.get("version", "")}</a>'
            )
            self.version_label.setStyleSheet(f"""
                font-size: {int(t.get('release_version_size', 22))}px;
                font-weight: {t.get('release_version_weight', 'bold')};
                color: {t.get('release_text', '#222')};
                background: transparent;
                border: none;
            """)

        if self.date_label:
            self.date_label.setStyleSheet(f"""
                font-size: {int(t.get('release_date_size', 12))}px;
                color: {t.get('release_date', '#888')};
                background: transparent;
                border: none;
            """)

        if self.body_label:
            self.body_label.setStyleSheet(f"""
                font-size: {int(t.get('release_text_size', 13))}px;
                line-height: 1.5;
                color: {t.get('release_text', '#333')};
                background: transparent;
                border: none;
            """)

    def apply_theme(self, theme):
        self.theme = theme
        self._apply_styles()