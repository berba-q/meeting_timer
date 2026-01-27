"""
In-app toast notification widget for displaying messages.
Supports localization via Qt's tr() system - pass translated strings when calling show_toast().
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QGraphicsOpacityEffect, QPushButton
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPainterPath


class ToastNotification(QWidget):
    """A toast notification widget that appears at the top of the parent window."""

    closed = pyqtSignal()

    def __init__(self, parent=None, duration=5000):
        super().__init__(parent)
        self.duration = duration
        self._setup_ui()
        self._setup_animations()

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out)

        # Start hidden
        self.hide()

    def _setup_ui(self):
        """Setup the toast UI."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Icon label (emoji)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(16)
        self.icon_label.setFont(icon_font)
        layout.addWidget(self.icon_label)

        # Text container
        text_container = QVBoxLayout()
        text_container.setSpacing(2)

        # Title label
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        text_container.addWidget(self.title_label)

        # Message label
        self.message_label = QLabel()
        message_font = QFont()
        message_font.setPointSize(11)
        self.message_label.setFont(message_font)
        self.message_label.setWordWrap(True)
        text_container.addWidget(self.message_label)

        layout.addLayout(text_container, 1)

        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.fade_out)
        layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignTop)

        # Set minimum size
        self.setMinimumWidth(300)
        self.setMaximumWidth(450)

        # Apply default styling
        self._apply_styling()

    def _apply_styling(self):
        """Apply styling to the toast."""
        self.setStyleSheet("""
            ToastNotification {
                background-color: rgba(50, 50, 50, 240);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QPushButton {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.6);
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)

    def _setup_animations(self):
        """Setup fade animations."""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        # Fade in animation
        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(200)
        self.fade_in_anim.setStartValue(0)
        self.fade_in_anim.setEndValue(1)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Fade out animation
        self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(300)
        self.fade_out_anim.setStartValue(1)
        self.fade_out_anim.setEndValue(0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_anim.finished.connect(self._on_fade_out_finished)

    def show_toast(self, title: str, message: str, icon: str = ""):
        """Show the toast with given title and message.

        Args:
            title: The toast title (should be pre-translated via tr())
            message: The toast message (should be pre-translated via tr())
            icon: Optional emoji icon to display
        """
        # Stop any existing animations/timers
        self.hide_timer.stop()
        self.fade_in_anim.stop()
        self.fade_out_anim.stop()

        # Set content
        self.title_label.setText(title)
        self.message_label.setText(message)
        self.icon_label.setText(icon if icon else "")
        self.icon_label.setVisible(bool(icon))

        # Adjust size
        self.adjustSize()

        # Position at top center of parent
        self._position_toast()

        # Show and animate
        self.show()
        self.raise_()
        self.fade_in_anim.start()

        # Start auto-hide timer
        self.hide_timer.start(self.duration)

    def _position_toast(self):
        """Position the toast at the top center of the parent window."""
        if self.parent():
            parent = self.parent()
            parent_rect = parent.rect()

            # Calculate position - top center with some margin
            x = (parent_rect.width() - self.width()) // 2
            y = 20  # Margin from top

            self.move(x, y)

    def fade_out(self):
        """Start the fade out animation."""
        self.hide_timer.stop()
        self.fade_out_anim.start()

    def _on_fade_out_finished(self):
        """Handle fade out completion."""
        self.hide()
        self.closed.emit()

    def paintEvent(self, event):
        """Custom paint for rounded background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw rounded rectangle background
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        painter.fillPath(path, QColor(50, 50, 50, 240))
        painter.setPen(QColor(255, 255, 255, 25))
        painter.drawPath(path)


class ToastManager(QWidget):
    """Manages toast notifications for a parent window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.toast = None
        self.setVisible(False)  # Manager widget is invisible

    def show_toast(self, title: str, message: str, icon: str = "", duration: int = 5000):
        """Show a toast notification.

        Args:
            title: The toast title (should be pre-translated via tr())
            message: The toast message (should be pre-translated via tr())
            icon: Optional emoji icon
            duration: How long to show the toast (ms)
        """
        # Create toast if needed, or reuse existing
        if not self.toast:
            self.toast = ToastNotification(self.parent(), duration=duration)
        else:
            self.toast.duration = duration

        self.toast.show_toast(title, message, icon)

    def hide_toast(self):
        """Hide the current toast."""
        if self.toast:
            self.toast.fade_out()
