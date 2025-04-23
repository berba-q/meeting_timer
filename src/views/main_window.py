"""
Main application window for the JW Meeting Timer.
"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTabWidget, QAction, QMessageBox,
    QSplitter, QFrame, QToolBar, QStatusBar, QMenuBar
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QAction

from src.controllers.meeting_controller import MeetingController
from src.controllers.timer_controller import TimerController
from src.controllers.settings_controller import SettingsController
from src.models.settings import SettingsManager, TimerDisplayMode
from src.models.meeting import Meeting, MeetingType
from src.views.timer_view import TimerView
from src.views.meeting_view import MeetingView
from src.views.settings_view import SettingsDialog
from src.views.secondary_display import SecondaryDisplay


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, meeting_controller: MeetingController):
        super().__init__()
        
        # Initialize controllers
        self.meeting_controller = meeting_controller
        self.settings_controller = SettingsController(self.meeting_controller.settings_manager)
        self.timer_controller = TimerController()
        
        # Secondary display window
        self.secondary_display = None
        
        # Setup UI
        self.setWindowTitle("JW Meeting Timer")
        self.setMinimumSize(1000, 700)
        
        # Create UI components
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Connect signals
        self._connect_signals()
        
        # Load meetings
        self.meeting_controller.load_meetings()
    
    def _create_menu_bar(self):
        """Create the application menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Create new meeting
        new_meeting_action = QAction("&New Meeting", self)
        new_meeting_action.setShortcut("Ctrl+N")
        new_meeting_action.triggered.connect(self._create_new_meeting)
        file_menu.addAction(new_meeting_action)
        
        # Open meeting
        open_meeting_action = QAction("&Open Meeting", self)
        open_meeting_action.setShortcut("Ctrl+O")
        open_meeting_action.triggered.connect(self._open_meeting)
        file_menu.addAction(open_meeting_action)
        
        file_menu.addSeparator()
        
        # Update meetings from web
        update_meetings_action = QAction("&Update Meetings from Web", self)
        update_meetings_action.setShortcut("F5")
        update_meetings_action.triggered.connect(self._update_meetings)
        file_menu.addAction(update_meetings_action)
        
        file_menu.addSeparator()
        
        # Settings
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        # Toggle secondary display
        toggle_secondary_action = QAction("Toggle &Secondary Display", self)
        toggle_secondary_action.setShortcut("F10")
        toggle_secondary_action.triggered.connect(self._toggle_secondary_display)
        toggle_secondary_action.setCheckable(True)
        toggle_secondary_action.setChecked(
            self.settings_controller.get_settings().display.use_secondary_screen
        )
        view_menu.addAction(toggle_secondary_action)
        
        # Switch display mode
        switch_display_mode_action = QAction("Switch Display &Mode", self)
        switch_display_mode_action.setShortcut("F9")
        switch_display_mode_action.triggered.connect(self._toggle_display_mode)
        view_menu.addAction(switch_display_mode_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # About
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bar(self):
        """Create the main toolbar"""
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        
        # Timer controls
        self.start_button = QPushButton("Start Meeting")
        self.start_button.clicked.connect(self._start_meeting)
        tool_bar.addWidget(self.start_button)
        
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self._toggle_pause_resume)
        self.pause_resume_button.setEnabled(False)
        tool_bar.addWidget(self.pause_resume_button)
        
        tool_bar.addSeparator()
        
        # Part navigation
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self._previous_part)
        self.prev_button.setEnabled(False)
        tool_bar.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self._next_part)
        self.next_button.setEnabled(False)
        tool_bar.addWidget(self.next_button)
        
        tool_bar.addSeparator()
        
        # Time adjustment
        self.decrease_button = QPushButton("-1 Minute")
        self.decrease_button.clicked.connect(lambda: self._adjust_time(-1))
        self.decrease_button.setEnabled(False)
        tool_bar.addWidget(self.decrease_button)
        
        self.increase_button = QPushButton("+1 Minute")
        self.increase_button.clicked.connect(lambda: self._adjust_time(1))
        self.increase_button.setEnabled(False)
        tool_bar.addWidget(self.increase_button)
        
        tool_bar.addSeparator()
        
        # Meeting selector
        self.meeting_selector = QComboBox()
        self.meeting_selector.currentIndexChanged.connect(self._meeting_selected)
        tool_bar.addWidget(QLabel("Current Meeting:"))
        tool_bar.addWidget(self.meeting_selector)
    
    def _create_central_widget(self):
        """Create the central widget with timer and meeting views"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Splitter for timer and parts
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        
        # Timer view
        self.timer_view = TimerView(self.timer_controller)
        splitter.addWidget(self.timer_view)
        
        # Meeting view
        self.meeting_view = MeetingView(self.meeting_controller, self.timer_controller)
        splitter.addWidget(self.meeting_view)
        
        # Set initial sizes
        splitter.setSizes([300, 400])
        
        main_layout.addWidget(splitter)
    
    def _create_status_bar(self):
        """Create the status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Current part label
        self.current_part_label = QLabel("No meeting selected")
        status_bar.addWidget(self.current_part_label)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        status_bar.addWidget(spacer)
        
        # Meeting overtime indicator
        self.meeting_overtime_label = QLabel()
        self.meeting_overtime_label.setVisible(False)
        status_bar.addPermanentWidget(self.meeting_overtime_label)
        
        # Display mode indicator
        self.display_mode_label = QLabel()
        self._update_display_mode_label()
        status_bar.addPermanentWidget(self.display_mode_label)
        
        # Secondary display indicator
        self.secondary_display_label = QLabel()
        self._update_secondary_display_label()
        status_bar.addPermanentWidget(self.secondary_display_label)
    
    def _connect_signals(self):
        """Connect controller signals to UI handlers"""
        # Meeting controller signals
        self.meeting_controller.meetings_loaded.connect(self._meetings_loaded)
        self.meeting_controller.meeting_updated.connect(self._meeting_updated)
        self.meeting_controller.error_occurred.connect(self._show_error)
        
        # Timer controller signals
        self.timer_controller.part_changed.connect(self._part_changed)
        self.timer_controller.meeting_started.connect(self._meeting_started)
        self.timer_controller.meeting_ended.connect(self._meeting_ended)
        self.timer_controller.transition_started.connect(self._transition_started)
        self.timer_controller.meeting_overtime.connect(self._meeting_overtime)
        
        # Settings controller signals
        self.settings_controller.settings_changed.connect(self._settings_changed)
        self.settings_controller.display_mode_changed.connect(self._display_mode_changed)
    
    def _meetings_loaded(self, meetings):
        """Handle loaded meetings"""
        # Update meeting selector
        self.meeting_selector.clear()
        
        if not meetings:
            self.meeting_selector.addItem("No meetings available")
            return
        
        for meeting_type, meeting in meetings.items():
            date_str = meeting.date.strftime("%Y-%m-%d")
            self.meeting_selector.addItem(f"{meeting.title} ({date_str})", meeting)
    
    def _meeting_selected(self, index):
        """Handle meeting selection change"""
        if index < 0 or self.meeting_selector.count() == 0:
            return
        
        meeting = self.meeting_selector.itemData(index)
        if meeting:
            self.meeting_controller.set_current_meeting(meeting)
            self.timer_controller.set_meeting(meeting)
            self.meeting_view.set_meeting(meeting)
            
            # Update status bar
            self.current_part_label.setText(f"Meeting: {meeting.title}")
    
    def _meeting_updated(self, meeting):
        """Handle meeting update"""
        self.meeting_view.set_meeting(meeting)
    
    def _part_changed(self, part, index):
        """Handle part change"""
        self.current_part_label.setText(f"Current part: {part.title} ({part.duration_minutes} min)")
        self.meeting_view.highlight_part(index)
    
    def _meeting_started(self):
        """Handle meeting start"""
        self.start_button.setText("Stop Meeting")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self._stop_meeting)
        
        # Enable controls
        self.pause_resume_button.setEnabled(True)
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.decrease_button.setEnabled(True)
        self.increase_button.setEnabled(True)
    
    def _meeting_overtime(self, total_overtime_seconds):
        """Handle meeting overtime notification"""
        # Only show if there's actual overtime
        if total_overtime_seconds > 0:
            # Format the overtime
            minutes = total_overtime_seconds // 60
            seconds = total_overtime_seconds % 60
            
            # Update and show the label
            self.meeting_overtime_label.setText(f"Meeting Overtime: {minutes:02d}:{seconds:02d}")
            self.meeting_overtime_label.setStyleSheet("color: red; font-weight: bold;")
            self.meeting_overtime_label.setVisible(True)
    
    def _transition_started(self, transition_msg):
        """Handle chairman transition period"""
        # Update the current part label
        self.current_part_label.setText(f"⏳ {transition_msg} (1:00)")
        
        # Also update the part_label in the timer view
        self.timer_view.part_label.setText(transition_msg)
        
        # Update secondary display if available
        if self.secondary_display:
            self.secondary_display.current_part_label.setText(transition_msg)
    
    def _meeting_ended(self):
        """Handle meeting end"""
        self.start_button.setText("Start Meeting")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self._start_meeting)
        
        # Disable controls
        self.pause_resume_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.decrease_button.setEnabled(False)
        self.increase_button.setEnabled(False)
        
        # Reset pause/resume button
        self.pause_resume_button.setText("Pause")
        
        # Reset overtime indicator
        self.meeting_overtime_label.setVisible(False)
    
    def _settings_changed(self):
        """Handle settings changes"""
        # Update display mode label
        self._update_display_mode_label()
        
        # Update secondary display
        self._update_secondary_display_label()
        self._update_secondary_display()
    
    def _display_mode_changed(self, mode):
        """Handle display mode change"""
        self.timer_view.set_display_mode(mode)
        if self.secondary_display:
            self.secondary_display.timer_view.set_display_mode(mode)
        self._update_display_mode_label()
    
    def _update_display_mode_label(self):
        """Update the display mode indicator in the status bar"""
        mode = self.settings_controller.get_settings().display.display_mode
        mode_text = "Digital" if mode == TimerDisplayMode.DIGITAL else "Analog"
        self.display_mode_label.setText(f"Display Mode: {mode_text}")
    
    def _update_secondary_display_label(self):
        """Update the secondary display indicator in the status bar"""
        settings = self.settings_controller.get_settings()
        if settings.display.use_secondary_screen and settings.display.secondary_screen_index is not None:
            self.secondary_display_label.setText("Secondary Display: Active")
        else:
            self.secondary_display_label.setText("Secondary Display: Inactive")
    
    def _start_meeting(self):
        """Start the current meeting"""
        if not self.meeting_controller.current_meeting:
            QMessageBox.warning(self, "No Meeting Selected", 
                                "Please select a meeting to start.")
            return
        
        self.timer_controller.start_meeting()
    
    def _stop_meeting(self):
        """Stop the current meeting"""
        self.timer_controller.stop_meeting()
    
    def _toggle_pause_resume(self):
        """Toggle between pause and resume"""
        if self.timer_controller.timer.state == TimerState.RUNNING:
            self.timer_controller.pause_timer()
            self.pause_resume_button.setText("Resume")
        else:
            self.timer_controller.resume_timer()
            self.pause_resume_button.setText("Pause")
    
    def _next_part(self):
        """Move to the next part"""
        self.timer_controller.next_part()
    
    def _previous_part(self):
        """Move to the previous part"""
        self.timer_controller.previous_part()
    
    def _adjust_time(self, minutes_delta):
        """Adjust timer by adding/removing minutes"""
        self.timer_controller.adjust_time(minutes_delta)
    
    def _create_new_meeting(self):
        """Create a new custom meeting"""
        # This would open a dialog to create a new meeting
        pass
    
    def _open_meeting(self):
        """Open an existing meeting file"""
        # This would open a file dialog to select a meeting file
        pass
    
    def _update_meetings(self):
        """Update meetings from web"""
        self.meeting_controller.update_meetings_from_web()
    
    def _open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.settings_controller, self)
        dialog.exec()
    
    def _toggle_secondary_display(self):
        """Toggle the secondary display window"""
        settings = self.settings_controller.get_settings()
        new_state = not settings.display.use_secondary_screen
        
        self.settings_controller.toggle_secondary_screen(new_state)
        self._update_secondary_display()
    
    def _update_secondary_display(self):
        """Update secondary display based on settings"""
        settings = self.settings_controller.get_settings()
        
        if settings.display.use_secondary_screen and settings.display.secondary_screen_index is not None:
            # Create secondary window if it doesn't exist
            if not self.secondary_display:
                self.secondary_display = SecondaryDisplay(self.timer_controller)
            
            # Show and position on the correct screen
            self.secondary_display.show()
            self._position_secondary_display()
        elif self.secondary_display:
            # Hide the secondary display
            self.secondary_display.hide()
    
    def _position_secondary_display(self):
        """Position the secondary display on the correct screen"""
        if not self.secondary_display:
            return
        
        settings = self.settings_controller.get_settings()
        screens = self.settings_controller.get_all_screens()
        
        if settings.display.secondary_screen_index is not None and 0 <= settings.display.secondary_screen_index < len(screens):
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.screens()[settings.display.secondary_screen_index]
            geometry = screen.geometry()
            
            # Center on the selected screen
            self.secondary_display.setGeometry(geometry)
            self.secondary_display.showFullScreen()
    
    def _toggle_display_mode(self):
        """Toggle between digital and analog display modes"""
        settings = self.settings_controller.get_settings()
        current_mode = settings.display.display_mode
        
        if current_mode == TimerDisplayMode.DIGITAL:
            self.settings_controller.set_display_mode(TimerDisplayMode.ANALOG)
        else:
            self.settings_controller.set_display_mode(TimerDisplayMode.DIGITAL)
    
    def _show_about(self):
        """Show the about dialog"""
        QMessageBox.about(
            self, 
            "About JW Meeting Timer",
            "JW Meeting Timer\n\n"
            "A cross-platform timer application for managing JW meeting schedules.\n\n"
            "Version 1.0.0\n"
            "© 2023 Open Source"
        )
    
    def _show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Close secondary display if it exists
        if self.secondary_display:
            self.secondary_display.close()
        
        # Accept the event to close the main window
        event.accept()