"""
JW Meeting Timer - A cross-platform timer application for managing meeting schedules
"""
import sys
import os
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
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.controllers.meeting_controller import MeetingController
from src.views.main_window import MainWindow
from src.utils.resources import get_icon, apply_stylesheet

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
    main_window.show()
    
    # Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()