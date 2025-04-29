"""
Main application window for the JW Meeting Timer.
"""
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTabWidget, QMessageBox,
    QSplitter, QFrame, QToolBar, QStatusBar, QMenuBar,
    QApplication, QSizePolicy
)
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtWidgets import QDialog

from src.utils.screen_handler import ScreenHandler
from src.controllers.meeting_controller import MeetingController
from src.controllers.timer_controller import TimerController
from src.controllers.settings_controller import SettingsController
from src.models.settings import SettingsManager, TimerDisplayMode, MeetingSourceMode
from src.models.meeting import Meeting, MeetingType
from src.models.timer import TimerState
from src.views.timer_view import TimerView
from src.views.meeting_view import MeetingView
from src.views.settings_view import SettingsDialog
from src.views.secondary_display import SecondaryDisplay
from src.views.weekend_song_editor import WeekendSongEditorDialog


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
        
        # Apply current theme
        self._apply_current_theme()
        
        # Create UI components
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Connect signals
        self._connect_signals()
        
        # Initialize timer to show current time
        self._initialize_timer_display()
        
        # Load meetings
        self.meeting_controller.load_meetings()
    
    def _initialize_timer_display(self):
        """Initialize timer to show current time and meeting countdown"""
        # Update the meeting selector with available meetings
        self._update_meeting_selector()
        
        # Auto-select the appropriate meeting based on current day
        self._auto_select_current_meeting()
        
        # If we have a current meeting, initialize the countdown
        if self.meeting_controller.current_meeting:
            meeting = self.meeting_controller.current_meeting
            self.timer_controller.set_meeting(meeting)
            
            # Force refresh of the meeting view
            self.meeting_view.set_meeting(meeting)
            
            # Ensure the status bar shows the correct meeting
            self.current_part_label.setText(f"Meeting: {meeting.title}")
            
            # Debug output
            print(f"Selected meeting in _initialize_timer_display: {meeting.title}, Type: {meeting.meeting_type.value}")
            print(f"Sections: {[s.title for s in meeting.sections]}")
    
    def _auto_select_current_meeting(self):
        """Automatically select the appropriate meeting based on the current day"""
        if not self.meeting_controller.current_meetings:
            return
        
        # Get current date and settings
        now = datetime.now()
        current_day = now.weekday()  # 0 = Monday, 6 = Sunday
        settings = self.settings_controller.get_settings()
        
        # Get configured days from settings
        midweek_day = settings.midweek_meeting.day.value  # Day of week (0-6)
        weekend_day = settings.weekend_meeting.day.value  # Day of week (0-6)
        
        meeting_to_select = None
        
        # First check if today is either meeting day
        if current_day == midweek_day and MeetingType.MIDWEEK in self.meeting_controller.current_meetings:
            meeting_to_select = self.meeting_controller.current_meetings[MeetingType.MIDWEEK]
            print(f"Auto-selecting midweek meeting for today (day {current_day})")
        elif current_day == weekend_day and MeetingType.WEEKEND in self.meeting_controller.current_meetings:
            meeting_to_select = self.meeting_controller.current_meetings[MeetingType.WEEKEND]
            print(f"Auto-selecting weekend meeting for today (day {current_day})")
        else:
            # If today isn't a meeting day, find the next meeting day
            days_to_midweek = (midweek_day - current_day) % 7
            days_to_weekend = (weekend_day - current_day) % 7
            
            # Choose the closest upcoming meeting
            if days_to_midweek < days_to_weekend:
                if MeetingType.MIDWEEK in self.meeting_controller.current_meetings:
                    meeting_to_select = self.meeting_controller.current_meetings[MeetingType.MIDWEEK]
                    print(f"Auto-selecting next midweek meeting in {days_to_midweek} days")
            else:
                if MeetingType.WEEKEND in self.meeting_controller.current_meetings:
                    meeting_to_select = self.meeting_controller.current_meetings[MeetingType.WEEKEND]
                    print(f"Auto-selecting next weekend meeting in {days_to_weekend} days")
        
        # If we found a meeting to select, update the selector and set current meeting
        if meeting_to_select:
            # Find the meeting in the selector
            found = False
            for i in range(self.meeting_selector.count()):
                meeting = self.meeting_selector.itemData(i)
                if meeting and meeting.meeting_type == meeting_to_select.meeting_type:
                    print(f"Found meeting in selector at index {i}: {meeting.title}")
                    # Temporarily disconnect signals to avoid recursive updates
                    self.meeting_selector.blockSignals(True)
                    self.meeting_selector.setCurrentIndex(i)
                    self.meeting_selector.blockSignals(False)
                    found = True
                    break
            
            if found:
                # Manually update everything with the selected meeting
                self.meeting_controller.set_current_meeting(meeting_to_select)
                self.timer_controller.set_meeting(meeting_to_select) 
                self.meeting_view.set_meeting(meeting_to_select)
            else:
                print("Warning: Selected meeting not found in selector")
            
    def _update_countdown(self, seconds_remaining: int, message: str):
        """Update the countdown message in the main window"""
        # Update status bar with countdown message
        if seconds_remaining > 0:
            # Show countdown in status bar
            self.current_part_label.setText(message)
            
            # If the secondary display exists, update it too
            if self.secondary_display:
                # Update the info label with just the countdown message
                self.secondary_display.info_label1.setText(message)
                self.secondary_display.info_label1.setStyleSheet("""
                    color: #4a90e2; 
                    font-size: 80px;
                    font-weight: bold;
                """)
                # Clear the second label during countdown
                self.secondary_display.info_label2.setText("")
                # Set flag to track that we're showing countdown
                self.secondary_display.show_countdown = True
        else:
            # Reset status bar when countdown ends
            if self.meeting_controller.current_meeting:
                meeting_title = self.meeting_controller.current_meeting.title
                self.current_part_label.setText(f"Meeting: {meeting_title}")
            else:
                self.current_part_label.setText("No meeting selected")
    
    def _update_meeting_selector(self):
        """Update the meeting selector dropdown with available meetings"""
        self.meeting_selector.clear()
        
        meetings = self.meeting_controller.current_meetings
        if not meetings:
            self.meeting_selector.addItem("No meetings available")
            return
        
        # Add each meeting to the selector
        for meeting_type, meeting in meetings.items():
            date_str = meeting.date.strftime("%Y-%m-%d")
            self.meeting_selector.addItem(f"{meeting.title} ({date_str})", meeting)
        
        # Select the first item
        if self.meeting_selector.count() > 0:
            self.meeting_selector.setCurrentIndex(0)
        
    def _show_secondary_display(self):
        """Show the secondary display on the configured screen"""
        settings = self.settings_controller.get_settings()
        
        # Create secondary window if it doesn't exist
        if not self.secondary_display:
            from src.views.secondary_display import SecondaryDisplay
            self.secondary_display = SecondaryDisplay(self.timer_controller)
            
            # Apply styling to ensure visibility
            self._apply_secondary_display_theme()
        
        # Use our ScreenHandler to position the window on the correct screen
        screen = ScreenHandler.get_configured_screen(settings, is_primary=False)
        if screen:
            # Set the geometry of the secondary display
            self.secondary_display.setGeometry(screen.geometry())
            self.secondary_display.showFullScreen()
            self.secondary_display.activateWindow()
        
        # Update status bar indicator
        self.secondary_display_label.setText("Secondary Display: Active")
        
        # Update toggle action state
        self.toggle_secondary_action.setChecked(True)
        
    def showEvent(self, event):
        """Override show event to initialize screens when window is shown"""
        super().showEvent(event)
        
        # This is the right time to initialize screens, after the window is fully created
        # and about to become visible
        self._initialize_screens()
    
    def _create_menu_bar(self):
        """Create the application menu bar"""
        from src.utils.resources import get_icon
        
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Create new meeting
        new_meeting_action = QAction(get_icon("clock"), "&New Meeting", self)
        new_meeting_action.setShortcut("Ctrl+N")
        new_meeting_action.triggered.connect(self._create_new_meeting)
        file_menu.addAction(new_meeting_action)
        
        # Open meeting
        open_meeting_action = QAction(get_icon("clock"), "&Open Meeting", self)
        open_meeting_action.setShortcut("Ctrl+O")
        open_meeting_action.triggered.connect(self._open_meeting)
        file_menu.addAction(open_meeting_action)
        
        # Edit current meeting
        edit_meeting_action = QAction(get_icon("edit"), "&Edit Current Meeting", self)
        edit_meeting_action.setShortcut("Ctrl+E")
        edit_meeting_action.triggered.connect(self._edit_current_meeting)
        file_menu.addAction(edit_meeting_action)
        edit_songs_action = QAction(get_icon("music"), "Edit Weekend &Songs", self)
        edit_songs_action.setShortcut("Ctrl+Shift+S")
        edit_songs_action.triggered.connect(self._edit_weekend_meeting_songs)
        file_menu.addAction(edit_songs_action)
        
        file_menu.addSeparator()
        
        # Update meetings from web
        update_meetings_action = QAction(get_icon("increase"), "&Update Meetings from Web", self)
        update_meetings_action.setShortcut("F5")
        update_meetings_action.triggered.connect(self._update_meetings)
        file_menu.addAction(update_meetings_action)
        
        file_menu.addSeparator()
        
        # Settings
        settings_action = QAction(get_icon("settings"), "&Settings", self)
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
        self.toggle_secondary_action = QAction("Toggle &Secondary Display", self)
        self.toggle_secondary_action.setShortcut("F10")
        self.toggle_secondary_action.triggered.connect(self._toggle_secondary_display)
        self.toggle_secondary_action.setCheckable(True)
        self.toggle_secondary_action.setChecked(
            self.settings_controller.get_settings().display.use_secondary_screen
        )
        view_menu.addAction(self.toggle_secondary_action)
        
        # Switch display mode
        switch_display_mode_action = QAction("Switch Display &Mode", self)
        switch_display_mode_action.setShortcut("F9")
        switch_display_mode_action.triggered.connect(self._toggle_display_mode)
        view_menu.addAction(switch_display_mode_action)
        
        # Switch theme
        self.theme_menu = view_menu.addMenu("&Theme")
        
        # Light theme action
        self.light_theme_action = QAction("&Light Theme", self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self._set_theme("light"))
        self.theme_menu.addAction(self.light_theme_action)
        
        # Dark theme action
        self.dark_theme_action = QAction("&Dark Theme", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(lambda: self._set_theme("dark"))
        self.theme_menu.addAction(self.dark_theme_action)
        
        # Set initial theme selection
        current_theme = self.settings_controller.get_settings().display.theme
        if current_theme == "dark":
            self.dark_theme_action.setChecked(True)
        else:
            self.light_theme_action.setChecked(True)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # About
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bar(self):
        """Create the main toolbar"""
        from src.utils.resources import get_icon
        
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(32, 32))
        tool_bar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        
        # Timer controls
        self.start_button = QPushButton("Start Meeting")
        self.start_button.setIcon(get_icon("play"))
        self.start_button.setIconSize(QSize(24, 24))
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self._start_meeting)
        tool_bar.addWidget(self.start_button)
        
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.setIcon(get_icon("pause"))
        self.pause_resume_button.setIconSize(QSize(24, 24))
        self.pause_resume_button.setObjectName("pauseButton")
        self.pause_resume_button.clicked.connect(self._toggle_pause_resume)
        self.pause_resume_button.setEnabled(False)
        tool_bar.addWidget(self.pause_resume_button)
        
        tool_bar.addSeparator()
        
        # Part navigation
        self.prev_button = QPushButton("Previous")
        self.prev_button.setIcon(get_icon("previous"))
        self.prev_button.setIconSize(QSize(24, 24))
        self.prev_button.clicked.connect(self._previous_part)
        self.prev_button.setEnabled(False)
        tool_bar.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.setIcon(get_icon("next"))
        self.next_button.setIconSize(QSize(24, 24))
        self.next_button.clicked.connect(self._next_part)
        self.next_button.setEnabled(False)
        tool_bar.addWidget(self.next_button)
        
        tool_bar.addSeparator()
        
        # Time adjustment
        self.decrease_button = QPushButton("-1 Minute")
        self.decrease_button.setIcon(get_icon("decrease"))
        self.decrease_button.setIconSize(QSize(24, 24))
        self.decrease_button.clicked.connect(lambda: self._adjust_time(-1))
        self.decrease_button.setEnabled(False)
        tool_bar.addWidget(self.decrease_button)
        
        self.increase_button = QPushButton("+1 Minute")
        self.increase_button.setIcon(get_icon("increase"))
        self.increase_button.setIconSize(QSize(24, 24))
        self.increase_button.clicked.connect(lambda: self._adjust_time(1))
        self.increase_button.setEnabled(False)
        tool_bar.addWidget(self.increase_button)
        
        tool_bar.addSeparator()
        
        # Meeting selector
        self.meeting_selector = QComboBox()
        self.meeting_selector.currentIndexChanged.connect(self._meeting_selected)
        tool_bar.addWidget(QLabel("Current Meeting:"))
        tool_bar.addWidget(self.meeting_selector)
        
        # Settings button
        settings_button = QPushButton("")
        settings_button.setIcon(get_icon("settings"))
        settings_button.clicked.connect(self._open_settings)
        tool_bar.addWidget(settings_button)
    
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
        
        # Predicted end time label
        self.predicted_end_time_label = QLabel()
        self.predicted_end_time_label.setVisible(False)
        status_bar.addPermanentWidget(self.predicted_end_time_label)
        
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
        self.meeting_controller.part_updated.connect(self._part_updated)
        
        # Timer controller signals
        self.timer_controller.part_changed.connect(self._part_changed)
        self.timer_controller.meeting_started.connect(self._meeting_started)
        self.timer_controller.meeting_ended.connect(self._meeting_ended)
        self.timer_controller.transition_started.connect(self._transition_started)
        self.timer_controller.meeting_overtime.connect(self._meeting_overtime)
        self.timer_controller.predicted_end_time_updated.connect(self._update_predicted_end_time)
        self.timer_controller.timer.meeting_countdown_updated.connect(self._update_countdown)
        
        # Settings controller signals
        self.settings_controller.settings_changed.connect(self._settings_changed)
        self.settings_controller.display_mode_changed.connect(self._display_mode_changed)
        self.settings_controller.theme_changed.connect(self._theme_changed)
    
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
            # Update the current meeting in the controller
            self.meeting_controller.set_current_meeting(meeting)
            
            # Make sure the timer controller and meeting view are updated with the selected meeting
            self.timer_controller.set_meeting(meeting)
            # Force recreate the parts view by setting it to None then to the meeting
            self.meeting_view.set_meeting(None)
            self.meeting_view.set_meeting(meeting)
            
            # Make sure the timer controller is updated with the selected meeting
            self.timer_controller.set_meeting(meeting)
            
            # Initialize the meeting countdown
            self.timer_controller._initialize_meeting_countdown()
            
            # Update status bar
            self.current_part_label.setText(f"Meeting: {meeting.title}")
            
            # Log the selection for debugging
            print(f"Selected meeting: {meeting.title}, Type: {meeting.meeting_type.value}")

    
    def _meeting_updated(self, meeting):
        """Handle meeting update"""
        self.meeting_view.set_meeting(meeting)
    
    def _part_changed(self, part, index):
        """Handle part change"""
        self.current_part_label.setText(f"Current part: {part.title} ({part.duration_minutes} min)")
        self.meeting_view.highlight_part(index)
        
    def _part_updated(self, part, section_index, part_index):
        """Handle a part being updated"""
        # Update the timer controller if needed
        if self.timer_controller.current_part_index != -1:
            # Check if the updated part is the current part
            global_part_index = self._get_global_part_index(section_index, part_index)
            if global_part_index == self.timer_controller.current_part_index:
                # Update the timer with the new duration if it has changed
                current_part = self.timer_controller.parts_list[global_part_index]
                if current_part.duration_minutes != part.duration_minutes:
                    # Adjust the timer duration
                    # This requires additional logic to handle currently running timers
                    # For now, just update the display
                    self.timer_controller.part_changed.emit(part, global_part_index)
    
    def _meeting_started(self):
        """Handle meeting start"""
        from src.utils.resources import get_icon
        
        self.start_button.setText("Stop Meeting")
        self.start_button.setIcon(get_icon("stop"))
        self.start_button.setObjectName("stopButton")  # Change style
        self.start_button.setStyleSheet("")  # Force style refresh
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self._stop_meeting)
    
    
        
        # Enable controls
        self.pause_resume_button.setEnabled(True)
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.decrease_button.setEnabled(True)
        self.increase_button.setEnabled(True)
        
        # If secondary display exists, update it too
        if self.secondary_display:
            # Hide countdown, show meeting info
            self.secondary_display.info_label1(False)
            self.secondary_display.info_label1(True)
            self.secondary_display.info_label2(True)
    
    def _meeting_ended(self):
        """Handle meeting end"""
        from src.utils.resources import get_icon
        
        self.start_button.setText("Start Meeting")
        self.start_button.setIcon(get_icon("play"))
        self.start_button.setObjectName("startButton")  # Change style
        self.start_button.setStyleSheet("")  # Force style refresh
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
        self.pause_resume_button.setIcon(get_icon("pause"))
        self.pause_resume_button.setObjectName("pauseButton")  # Change style
        self.pause_resume_button.setStyleSheet("")  # Force style refresh
        
        # Reset overtime indicator
        self.meeting_overtime_label.setVisible(False)
        
        # Reset predicted end time
        self.predicted_end_time_label.setVisible(False)
    
    def _transition_started(self, transition_msg):
        """Handle chairman transition period"""
        # Update the current part label
        self.current_part_label.setText(f"⏳ {transition_msg} (1:00)")
        
        # Also update the part_label in the timer view
        self.timer_view.part_label.setText(transition_msg)
        
        # Update secondary display if available
        if self.secondary_display:
            self.secondary_display.next_part_label.setText(transition_msg)
    
    def _get_global_part_index(self, section_index, part_index):
        """Helper method to get global part index from section and part indices"""
        if not self.meeting_controller.current_meeting:
            return -1
        
        meeting = self.meeting_controller.current_meeting
        global_index = 0
        
        for i in range(section_index):
            global_index += len(meeting.sections[i].parts)
        
        global_index += part_index
        return global_index
    
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
        
        # Check if secondary display exists before trying to update it
        if self.secondary_display:
            # Check what attributes are available
            if hasattr(self.secondary_display, 'timer_view'):
                # Old implementation with timer_view
                self.secondary_display.timer_view.set_display_mode(mode)
            else:
                # New implementation with direct timer label
                # No need to change display mode as it's always digital
                pass
                
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
    
    def _apply_current_theme(self):
        """Apply the current theme from settings"""
        from src.utils.resources import apply_stylesheet
        
        theme = self.settings_controller.get_settings().display.theme
        apply_stylesheet(QApplication.instance(), theme)
    
    def _set_theme(self, theme: str):
        """Set the application theme"""
        # Update theme in settings
        self.settings_controller.set_theme(theme)
        
        # Update menu checkboxes
        self.light_theme_action.setChecked(theme == "light")
        self.dark_theme_action.setChecked(theme == "dark")
        
        # Apply the theme
        self._apply_current_theme()
    
    def _theme_changed(self, theme: str):
        """Handle theme change from settings"""
        # Update menu checkboxes
        self.light_theme_action.setChecked(theme == "light")
        self.dark_theme_action.setChecked(theme == "dark")
        
        # Apply the theme
        self._apply_current_theme()
        
        # Update secondary display if open
        if self.secondary_display:
            self._apply_secondary_display_theme()
    
    def _apply_secondary_display_theme(self):
        """Apply high-contrast styling to the secondary display regardless of theme"""
        if not self.secondary_display:
            return
        
        # Always apply a black background with white text for maximum visibility
        self.secondary_display.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #000000;
                color: #ffffff;
            }
            
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            
            QFrame {
                background-color: rgba(50, 50, 50, 180);
                border: 2px solid #ffffff;
                border-radius: 15px;
            }
            
            TimerView {
                background-color: #000000;
                border: 2px solid #333333;
            }
            
            TimerView QLabel {
                color: #ffffff;
                font-weight: bold;
            }
        """)
        
        # Ensure timer display is properly styled
        if hasattr(self.secondary_display, 'timer_view') and hasattr(self.secondary_display.timer_view, 'timer_label'):
            self.secondary_display.timer_view.timer_label.setStyleSheet("color: #ffffff; font-weight: bold;")
    
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
        from src.utils.resources import get_icon
        
        if self.timer_controller.timer.state == TimerState.RUNNING:
            self.timer_controller.pause_timer()
            self.pause_resume_button.setText("Resume")
            self.pause_resume_button.setIcon(get_icon("play"))
            self.pause_resume_button.setObjectName("startButton")  # Change style
            self.pause_resume_button.setStyleSheet("")  # Force style refresh
        else:
            self.timer_controller.resume_timer()
            self.pause_resume_button.setText("Pause")
            self.pause_resume_button.setIcon(get_icon("pause"))
            self.pause_resume_button.setObjectName("pauseButton")  # Change style
            self.pause_resume_button.setStyleSheet("")  # Force style refresh
    
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
        # Show the meeting editor dialog
        self.meeting_controller.show_meeting_editor(self)
    
    def _open_meeting(self):
        """Open an existing meeting file"""
        from PyQt6.QtWidgets import QFileDialog
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Meeting",
            str(self.meeting_controller.meetings_dir),
            "Meeting Files (*.json)"
        )
        
        if file_path:
            try:
                # Load meeting
                meeting = self.meeting_controller._load_meeting_file(file_path)
                if meeting:
                    # Set as current meeting
                    self.meeting_controller.set_current_meeting(meeting)
                    
                    # Update meeting view
                    self.meeting_view.set_meeting(meeting)
                    
                    # Add to recent meetings
                    if file_path not in self.meeting_controller.settings_manager.settings.recent_meetings:
                        self.meeting_controller.settings_manager.settings.recent_meetings.append(file_path)
                        self.meeting_controller.settings_manager.save_settings()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load meeting: {str(e)}")
    
    def _update_meetings(self):
        """Update meetings from web with enhanced weekend meeting handling"""
        # Check meeting source mode
        mode = self.settings_controller.get_settings().meeting_source.mode
        if mode == MeetingSourceMode.WEB_SCRAPING:
            # Show a progress dialog
            from PyQt6.QtWidgets import QProgressDialog
            progress = QProgressDialog("Updating meetings from wol.jw.org...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Updating Meetings")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            try:
                # Use web scraping
                meetings = self.meeting_controller.update_meetings_from_web()
                
                # Process weekend meeting to ensure songs are properly displayed
                if MeetingType.WEEKEND in meetings:
                    weekend_meeting = meetings[MeetingType.WEEKEND]
                    self._process_weekend_meeting_songs(weekend_meeting)
                
                progress.close()
                
                # Show a success message
                QMessageBox.information(self, "Update Complete", 
                                       "Meetings have been successfully updated.")
            except Exception as e:
                progress.close()
                QMessageBox.warning(self, "Update Failed", 
                                  f"Failed to update meetings: {str(e)}")
        else:
            # Show options dialog as before
            from PyQt6.QtWidgets import QMenu
            
            menu = QMenu(self)
            web_action = menu.addAction("Update from Web")
            web_action.triggered.connect(self.meeting_controller.update_meetings_from_web)
            
            edit_action = menu.addAction("Edit Current Meeting")
            edit_action.triggered.connect(lambda: self._edit_current_meeting())
            
            menu.addSeparator()
            
            create_action = menu.addAction("Create New Meeting")
            create_action.triggered.connect(self._create_new_meeting)
            
            # Position menu below the update button
            menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
            
    def _process_weekend_meeting_songs(self, meeting: Meeting):
        """Process weekend meeting to ensure songs are properly displayed"""
        # Flag to track if we need to prompt the user
        missing_songs = False
        
        for section in meeting.sections:
            for part in section.parts:
                if "song" in part.title.lower() and "song" == part.title.strip().lower():
                    # Found a generic song without a number
                    missing_songs = True
        
        # If there are missing songs, prompt the user
        if missing_songs:
            reply = QMessageBox.question(
                self, "Update Weekend Songs", 
                "Some weekend meeting songs need to be added manually. Would you like to edit them now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Show the meeting editor
                self.meeting_controller.show_meeting_editor(self, meeting)
    
    def _edit_current_meeting(self):
        """Edit the currently selected meeting"""
        if not self.meeting_controller.current_meeting:
            QMessageBox.warning(self, "No Meeting Selected", 
                            "Please select a meeting to edit.")
            return
        
        # Show the meeting editor dialog with the current meeting
        self.meeting_controller.show_meeting_editor(
            self, self.meeting_controller.current_meeting
        )
    
    def _edit_weekend_meeting_songs(self):
        """Edit weekend meeting songs"""
        current_meeting = self.meeting_controller.current_meeting
        
        # Check if we have a weekend meeting selected
        if not current_meeting or current_meeting.meeting_type != MeetingType.WEEKEND:
            QMessageBox.warning(self, "Not a Weekend Meeting", 
                            "Please select a weekend meeting first.")
            return
        
        # Show the weekend song editor dialog
        from src.views.weekend_song_editor import WeekendSongEditorDialog
        dialog = WeekendSongEditorDialog(current_meeting, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save the updated meeting
            self.meeting_controller.save_meeting(current_meeting)
            
            # Update the meeting display
            self.meeting_view.set_meeting(current_meeting)
            
            # Show confirmation message
            QMessageBox.information(self, "Songs Updated", 
                                "Weekend meeting songs have been updated.")
    
    def _open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.settings_controller, self)
        dialog.exec()
    
    def _initialize_screens(self):
        """Initialize screen handling during application startup"""
        # Get the current settings
        settings = self.settings_controller.get_settings()
        
        # Position main window on the primary screen
        self._position_main_window()
        
        # Show secondary display if enabled in settings
        if settings.display.use_secondary_screen:
            # Delay the creation of secondary display slightly to ensure
            # the main window is fully displayed first
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._show_secondary_display)
    
    def _position_main_window(self):
        """Position the main window on the primary screen from settings"""
        settings = self.settings_controller.get_settings()
        #primary_index = settings.display.primary_screen_index
        
        # Get the screen by index
        screen = ScreenHandler.get_configured_screen(settings, is_primary=True)
        if screen:
            # Center the window on the selected primary screen
            geometry = screen.availableGeometry()
            self.setGeometry(
                geometry.x() + (geometry.width() - self.width()) // 2,
                geometry.y() + (geometry.height() - self.height()) // 2,
                self.width(),
                self.height()
            )
            
    def _position_secondary_display(self):
        """Position the secondary display on the correct screen"""
        if not self.secondary_display:
            return
        
        settings = self.settings_controller.get_settings()
        #secondary_index = settings.display.secondary_screen_index
        
        # Get the screen for the secondary display
        screen = ScreenHandler.get_configured_screen(settings, is_primary=False)
        if screen:
            # Get the geometry of the secondary screen
            geometry = screen.geometry()
            
            # Set the geometry of the secondary display
            self.secondary_display.setGeometry(geometry)
            self.secondary_display.showFullScreen()
    
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
            
            # Apply proper styling to ensure visibility
            self._apply_secondary_display_theme()
            
            # Show and position on the correct screen
            self.secondary_display.show()
            self._position_secondary_display()
            
            # Update toggle action
            self.toggle_secondary_action.setChecked(True)
        elif self.secondary_display:
            # Hide the secondary display
            self.secondary_display.hide()
            
            # Update toggle action
            self.toggle_secondary_action.setChecked(False)
    
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
    
    def _update_predicted_end_time(self, original_end_time, predicted_end_time):
        """Update the predicted end time display"""
        # Only show if the setting is enabled
        settings = self.settings_controller.get_settings()
        if not settings.display.show_predicted_end_time:
            self.predicted_end_time_label.setVisible(False)
            return
        
        # Format the times
        original_time_str = original_end_time.strftime("%H:%M")
        predicted_time_str = predicted_end_time.strftime("%H:%M")
        
        # Calculate the difference
        time_diff = predicted_end_time - original_end_time
        diff_minutes = int(time_diff.total_seconds() / 60)
        
        # Set the text and color based on whether we're running over or under
        if diff_minutes > 0:
            # Running over time
            self.predicted_end_time_label.setText(f"End: {predicted_time_str} (+{diff_minutes} min)")
            self.predicted_end_time_label.setStyleSheet("color: red;")
        elif diff_minutes < 0:
            # Running under time
            self.predicted_end_time_label.setText(f"End: {predicted_time_str} ({diff_minutes} min)")
            self.predicted_end_time_label.setStyleSheet("color: green;")
        else:
            # On time
            self.predicted_end_time_label.setText(f"End: {predicted_time_str} (on time)")
            self.predicted_end_time_label.setStyleSheet("color: black;")
        
        # Make the label visible
        self.predicted_end_time_label.setVisible(True)
    
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