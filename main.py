"""
OnTime - A cross-platform timer application for managing meeting schedules
"""
import sys
import os
import time
import logging
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

from src.utils.translator import load_translation

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
            logging.getLogger("OnTime").warning("Could not load icon: %s", e)
            self.icon_label.setText("⏱️")
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.icon_label.setFont(QFont("Arial", 40))

        self.title_label = QLabel("OnTime Meeting Timer", self)
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel(self.tr("Initializing..."), self)
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #333;")

        self.version_label = QLabel(self.tr("Version") + f" {__version__}", self)
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
            self.tr("Warming up the mic..."),
            self.tr("Checking the speaker notes..."),
            self.tr("Counting backwards from 10..."),
            self.tr("Synchronizing timers..."),
            self.tr("Just a moment more...")
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
from src.controllers.timer_controller import TimerController
from src.controllers.settings_controller import SettingsController
from src.views.main_window import MainWindow
from src.utils.resources import get_icon, apply_stylesheet, get_system_theme

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
        # Clear meeting view safely
        if main_window._is_component_ready('meeting_view'):
            main_window.meeting_view.set_meeting(None)
        else:
            main_window._store_pending_action('meeting_view', 'set_meeting', None)
        if main_window._is_component_ready('meeting_view'):
            main_window.meeting_view.set_meeting(meeting_to_select)
        else:
            main_window._store_pending_action('meeting_view', 'set_meeting', meeting_to_select)
        
        # Update meeting selection in dropdown
        for i in range(main_window.meeting_selector.count()):
            meeting = main_window.meeting_selector.itemData(i)
            if meeting and meeting.meeting_type == meeting_to_select.meeting_type:
                main_window.meeting_selector.blockSignals(True)
                main_window.meeting_selector.setCurrentIndex(i)
                main_window.meeting_selector.blockSignals(False)
                break
        
        # Update status bar
        main_window.current_part_label.setText(
            main_window.tr("Meeting:") + f" {meeting_to_select.title}"
        )
        

def _log_system_info(logger):
    """Log system information in the background after startup."""
    from src.utils.helpers import get_system_info
    for key, value in get_system_info().items():
        logger.info("  %s: %s", key, value)


def _run_startup_cleanup(controller, main_window):
    """Run data cleanup in a background thread after startup."""
    from pathlib import Path
    from src.utils.data_cleanup import CleanupWorker

    settings = controller.settings_manager.settings
    if not settings.data_cleanup.enabled:
        return

    # Build set of active meeting filenames (never delete these)
    active_files = set()
    for meeting in controller.current_meetings.values():
        date_str = meeting.date.strftime("%Y-%m-%d")
        filename = f"{meeting.meeting_type.value}_{date_str}_{meeting.language}.json"
        active_files.add(filename)

    # Resolve cache dir (same path used by epub_scraper and scraper)
    try:
        from platformdirs import user_cache_dir
    except ImportError:
        def user_cache_dir(appname, appauthor=None):
            return str(Path.home() / ".meeting_timer_cache")

    meetings_dir = Path(controller.meetings_dir)
    cache_dir = Path(user_cache_dir("MeetingTimer"))

    worker = CleanupWorker(
        meetings_dir=meetings_dir,
        cache_dir=cache_dir,
        retention_days=settings.data_cleanup.retention_days,
        active_meeting_files=active_files,
        parent=main_window
    )

    def on_cleanup_finished(result):
        if result.has_removals:
            main_window._show_toast_notification(
                main_window.tr("Data Cleanup"),
                result.summary(),
                icon="toast-shredder"
            )
        if result.errors:
            main_window._show_toast_notification(
                main_window.tr("Cleanup Errors"),
                main_window.tr(f"{len(result.errors)} file(s) could not be removed"),
                icon="toast-info"
            )
        worker.deleteLater()

    worker.finished.connect(on_cleanup_finished)
    worker.start()


def main():
    """Application entry point"""
    start_time = time.perf_counter()

    from src.config import USER_DATA_DIR
    from src.utils.helpers import setup_logging, setup_crash_handlers

    # Initialize logging and crash handlers
    log_dir = USER_DATA_DIR / "logs"
    setup_logging(log_dir=log_dir)
    setup_crash_handlers(log_dir=log_dir)
    logger = logging.getLogger("OnTime")

    app = QApplication(sys.argv)
    app.setApplicationName("OnTime")
    app.setOrganizationName("OnTime")
    app.setWindowIcon(get_icon("app_icon"))

    from src import __version__
    logger.info("OnTime Meeting Timer v%s starting", __version__)

    # Initialize controllers first so we can load saved theme
    controller = MeetingController()
    settings_controller = SettingsController(controller.settings_manager)
    timer_controller = TimerController(settings_controller)

    # Load saved theme preference (resolve "system" to actual theme)
    saved_theme = settings_controller.get_settings().display.theme
    if saved_theme == "system":
        saved_theme = get_system_theme()
    apply_stylesheet(app, saved_theme)

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

    # Load meetings
    controller.load_meetings()

    # Load saved language
    saved_language = settings_controller.get_settings().language
    if saved_language == "en":
        logger.info("Using default English interface")
    else:
        if not load_translation(app, saved_language):
            QMessageBox.information(
                None,
                "Language Fallback",
                f"The selected language '{saved_language}' is not available.\nThe application will use English instead."
            )
            load_translation(app, "en")
        else:
            logger.info("Loaded translation for %s", saved_language)

    splash.status_label.setText(splash.tr("Loading complete..."))

    # Pass both MeetingController and its TimerController to MainWindow
    main_window = MainWindow(
        controller,
        timer_controller,
        settings_controller
    )
    splash.finish(main_window)
    _select_meeting_by_day(controller, main_window)
    main_window.show()

    elapsed = time.perf_counter() - start_time
    logger.info("App ready in %.2f seconds", elapsed)

    # Defer expensive system info logging until after the window is visible
    QTimer.singleShot(0, lambda: _log_system_info(logger))

    # Run data cleanup in background (non-blocking, off main thread)
    QTimer.singleShot(0, lambda: _run_startup_cleanup(controller, main_window))

    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()