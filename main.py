"""
JW Meeting Timer - A cross-platform timer application for managing meeting schedules
"""
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTabWidget, QMessageBox,
    QSplitter, QFrame, QToolBar, QStatusBar, QMenuBar,
    QApplication, QSizePolicy
)
from PyQt6.QtGui import QAction
#from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
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
        print(f"Selected MIDWEEK meeting based on current day ({current_day})")
    elif current_day == weekend_day and MeetingType.WEEKEND in controller.current_meetings:
        meeting_to_select = controller.current_meetings[MeetingType.WEEKEND]
        print(f"Selected WEEKEND meeting based on current day ({current_day})")
    else:
        # Find next upcoming meeting
        days_to_midweek = (midweek_day - current_day) % 7
        days_to_weekend = (weekend_day - current_day) % 7
        
        if days_to_midweek <= days_to_weekend and MeetingType.MIDWEEK in controller.current_meetings:
            meeting_to_select = controller.current_meetings[MeetingType.MIDWEEK]
            print(f"Selected MIDWEEK meeting (next upcoming in {days_to_midweek} days)")
        elif MeetingType.WEEKEND in controller.current_meetings:
            meeting_to_select = controller.current_meetings[MeetingType.WEEKEND]
            print(f"Selected WEEKEND meeting (next upcoming in {days_to_weekend} days)")
    
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
    # Set up application
    app = QApplication(sys.argv)
    app.setApplicationName("JW Meeting Timer")
    app.setOrganizationName("JW Meeting Timer")
    
    # Set application icon
    app.setWindowIcon(get_icon("app_icon"))
    
    # Apply stylesheet (light theme by default)
    apply_stylesheet(app, "light")
    
    # Initialize controller
    controller = MeetingController()
    
    # Create and show main window
    main_window = MainWindow(controller)
    
    # Load meetings
    controller.load_meetings()
    
    # Force selection of the appropriate meeting based on current day
    _select_meeting_by_day(controller, main_window)
    
    main_window.show()
    
    # Start application event loop
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()