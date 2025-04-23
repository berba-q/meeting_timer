"""
JW Meeting Timer - A cross-platform timer application for managing meeting schedules
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.controllers.meeting_controller import MeetingController
from src.views.main_window import MainWindow

def main():
    """Application entry point"""
    # Set up application
    app = QApplication(sys.argv)
    app.setApplicationName("JW Meeting Timer")
    app.setOrganizationName("JW Meeting Timer")
    
    # Set application icon
    if os.path.exists("assets/icons/app_icon.png"):
        app.setWindowIcon(QIcon("assets/icons/app_icon.png"))
    
    # Initialize controller
    controller = MeetingController()
    
    # Create and show main window
    main_window = MainWindow(controller)
    main_window.show()
    
    # Start application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()