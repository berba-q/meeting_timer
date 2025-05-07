"""
OnTime - A cross-platform timer application for managing meeting schedules
"""
import sys
import os
import time
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTabWidget, QMessageBox,
    QSplitter, QFrame, QToolBar, QStatusBar, QMenuBar,
    QApplication, QSizePolicy
)
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QSize

class CustomSplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        from src.utils.resources import get_icon
        from src import __version__

        # Set fixed size for splash screen
        self.setFixedSize(400, 300)

        # Create central pixmap with white background
        pixmap = QPixmap(self.size())
        pixmap.fill(QColor("#ffffff"))

        self.setPixmap(pixmap)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: white;")

        # Add widgets over splash
        from PyQt6.QtWidgets import QLabel, QVBoxLayout

        self.icon_label = QLabel(self)
        try:
            app_icon = get_icon("app_icon")
            icon_pixmap = app_icon.pixmap(QSize(96, 96))
            self.icon_label.setPixmap(icon_pixmap)
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            print(f"[WARN] Could not load icon: {e}")
            self.icon_label.setText("⏱️")
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.icon_label.setFont(QFont("Arial", 40))

        self.title_label = QLabel("OnTime Meeting Timer", self)
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Initializing...", self)
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #333;")

        self.version_label = QLabel(f"Version {__version__}", self)
        self.version_label.setFont(QFont("Arial", 10))
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet("color: #888;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addSpacing(10)
        layout.addWidget(self.status_label)
        layout.addSpacing(5)
        layout.addWidget(self.version_label)

        self.witty_lines = [
            "Warming up the mic...",
            "Checking the speaker notes...",
            "Counting backwards from 10...",
            "Synchronizing timers...",
            "Just a moment more..."
        ]
        self._start_witty_messages()

    def _start_witty_messages(self, index=0):
        if index < len(self.witty_lines):
            self.status_label.setText(self.witty_lines[index])
            QTimer.singleShot(2000, lambda: self._start_witty_messages(index + 1))

from datetime import datetime
from pathlib import Path

from src.models.meeting import MeetingType
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.controllers.meeting_controller import MeetingController
from src.controllers.settings_controller import SettingsController
from src.views.main_window import MainWindow
from src.utils.resources import get_icon, apply_stylesheet

def _select_meeting_by_day(controller, main_window):
    """Select the appropriate meeting based on day of week"""
    # Get current date
    now = datetime.now()
    current_day = now.weekday()  # 0 = Monday, 6 = Sunday
    
    # Get settings
    settings = main_window.settings_controller.get_settings()
    midweek_day = settings.midweek_meeting.day.value
    weekend_day = settings.weekend_meeting.day.value
    
    # Determine which meeting to select
    meeting_to_select = None
    
    # Check if today is a meeting day
    if current_day == midweek_day and MeetingType.MIDWEEK in controller.current_meetings:
        meeting_to_select = controller.current_meetings[MeetingType.MIDWEEK]
        #print(f"Selected MIDWEEK meeting based on current day ({current_day})")
    elif current_day == weekend_day and MeetingType.WEEKEND in controller.current_meetings:
        meeting_to_select = controller.current_meetings[MeetingType.WEEKEND]
        #print(f"Selected WEEKEND meeting based on current day ({current_day})")
    else:
        # Find next upcoming meeting
        days_to_midweek = (midweek_day - current_day) % 7
        days_to_weekend = (weekend_day - current_day) % 7
        
        if days_to_midweek <= days_to_weekend and MeetingType.MIDWEEK in controller.current_meetings:
            meeting_to_select = controller.current_meetings[MeetingType.MIDWEEK]
            #print(f"Selected MIDWEEK meeting (next upcoming in {days_to_midweek} days)")
        elif MeetingType.WEEKEND in controller.current_meetings:
            meeting_to_select = controller.current_meetings[MeetingType.WEEKEND]
            #print(f"Selected WEEKEND meeting (next upcoming in {days_to_weekend} days)")
    
    # Default to any available meeting if none selected
    if not meeting_to_select:
        if MeetingType.MIDWEEK in controller.current_meetings:
            meeting_to_select = controller.current_meetings[MeetingType.MIDWEEK]
        elif MeetingType.WEEKEND in controller.current_meetings:
            meeting_to_select = controller.current_meetings[MeetingType.WEEKEND]
    
    if meeting_to_select:
        # Set as current meeting in controller
        controller.set_current_meeting(meeting_to_select)
        
        # Update all views explicitly
        main_window.timer_controller.set_meeting(meeting_to_select)
        
        # Force complete refresh of meeting view
        main_window.meeting_view.set_meeting(None)  # Clear first
        main_window.meeting_view.set_meeting(meeting_to_select)
        
        # Update meeting selection in dropdown
        for i in range(main_window.meeting_selector.count()):
            meeting = main_window.meeting_selector.itemData(i)
            if meeting and meeting.meeting_type == meeting_to_select.meeting_type:
                main_window.meeting_selector.blockSignals(True)
                main_window.meeting_selector.setCurrentIndex(i)
                main_window.meeting_selector.blockSignals(False)
                break
        
        # Update status bar
        main_window.current_part_label.setText(f"Meeting: {meeting_to_select.title}")
        

def main():
    """Application entry point"""
    start_time = time.perf_counter()
    app = QApplication(sys.argv)
    app.setApplicationName("OnTime")
    app.setOrganizationName("OnTime")

    app.setWindowIcon(get_icon("app_icon"))
    apply_stylesheet(app, "light")

    splash = CustomSplashScreen()
    splash.show()
    primary_screen = app.primaryScreen()
    screen_geometry = primary_screen.geometry()
    splash.move(
        screen_geometry.center().x() - splash.width() // 2,
        screen_geometry.center().y() - splash.height() // 2
    )
    app.processEvents()
    splash.raise_()
    splash.activateWindow()

    # Direct initialization
    controller = MeetingController()
    settings_controller = SettingsController(controller.settings_manager)
    controller.load_meetings()
    splash.status_label.setText("Loading complete...")

    main_window = MainWindow(controller, settings_controller)
    _select_meeting_by_day(controller, main_window)
    splash.finish(main_window)
    main_window.show()

    elapsed = time.perf_counter() - start_time
    print(f"[PERF] App ready in {elapsed:.2f} seconds")

    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()