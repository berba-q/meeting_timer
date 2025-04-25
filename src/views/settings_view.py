"""
Settings dialog for the JW Meeting Timer application.
"""
import os
from datetime import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QCheckBox, QTimeEdit, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QDialogButtonBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QTime

from src.controllers.settings_controller import SettingsController
from src.models.settings import DayOfWeek, TimerDisplayMode, MeetingSourceMode


class SettingsDialog(QDialog):
    """Settings dialog for the application"""
    
    def __init__(self, settings_controller: SettingsController, parent=None):
        super().__init__(parent)
        self.settings_controller = settings_controller
        
        # Available languages
        self.available_languages = {
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "pt": "Português",
            "it": "Italiano",
            "ja": "日本語",
            "ko": "한국어",
            "zh": "中文"
        }
        
        # Setup UI
        self._setup_ui()
        
        # Load current settings
        self._load_settings()
    
    def _setup_ui(self):
        """Setup the UI components"""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.general_tab = QWidget()
        self.meetings_tab = QWidget()
        self.display_tab = QWidget()
        self.meeting_source_tab = QWidget()  # New tab for meeting source options
        
        self._setup_general_tab()
        self._setup_meetings_tab()
        self._setup_display_tab()
        self._setup_meeting_source_tab()  # Setup new tab
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.meetings_tab, "Meetings")
        self.tab_widget.addTab(self.display_tab, "Display")
        self.tab_widget.addTab(self.meeting_source_tab, "Meeting Source")
        
        # Add tab widget to layout
        layout.addWidget(self.tab_widget)
        
        # Add button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel | 
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Reset
        )
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_settings)
        button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._reset_settings)
        
        layout.addWidget(button_box)
    
    def _setup_general_tab(self):
        """Setup general settings tab"""
        layout = QVBoxLayout(self.general_tab)
        
        # Language selection
        language_group = QGroupBox("Language")
        language_layout = QFormLayout(language_group)
        
        self.language_combo = QComboBox()
        for lang_code, lang_name in self.available_languages.items():
            self.language_combo.addItem(lang_name, lang_code)
        
        language_layout.addRow("Interface Language:", self.language_combo)
        
        # Add groups to layout
        layout.addWidget(language_group)
        layout.addStretch()
    
    def _setup_meetings_tab(self):
        """Setup meetings settings tab"""
        layout = QVBoxLayout(self.meetings_tab)
        
        # Midweek meeting settings
        midweek_group = QGroupBox("Midweek Meeting")
        midweek_layout = QFormLayout(midweek_group)
        
        self.midweek_day_combo = QComboBox()
        for day in DayOfWeek:
            self.midweek_day_combo.addItem(day.name.capitalize(), day.value)
        
        self.midweek_time_edit = QTimeEdit()
        self.midweek_time_edit.setDisplayFormat("hh:mm AP")
        
        midweek_layout.addRow("Day:", self.midweek_day_combo)
        midweek_layout.addRow("Time:", self.midweek_time_edit)
        
        # Weekend meeting settings
        weekend_group = QGroupBox("Weekend Meeting")
        weekend_layout = QFormLayout(weekend_group)
        
        self.weekend_day_combo = QComboBox()
        for day in DayOfWeek:
            self.weekend_day_combo.addItem(day.name.capitalize(), day.value)
        
        self.weekend_time_edit = QTimeEdit()
        self.weekend_time_edit.setDisplayFormat("hh:mm AP")
        
        weekend_layout.addRow("Day:", self.weekend_day_combo)
        weekend_layout.addRow("Time:", self.weekend_time_edit)
        
        # Add groups to layout
        layout.addWidget(midweek_group)
        layout.addWidget(weekend_group)
        layout.addStretch()
    
    def _setup_display_tab(self):
        """Setup display settings tab"""
        layout = QVBoxLayout(self.display_tab)
        
        # Timer display mode
        display_mode_group = QGroupBox("Timer Display")
        display_mode_layout = QVBoxLayout(display_mode_group)
        
        self.digital_mode_radio = QCheckBox("Digital")
        self.analog_mode_radio = QCheckBox("Analog")
        
        # Make checkboxes mutually exclusive
        self.digital_mode_radio.toggled.connect(lambda checked: self.analog_mode_radio.setChecked(not checked))
        self.analog_mode_radio.toggled.connect(lambda checked: self.digital_mode_radio.setChecked(not checked))
        
        display_mode_layout.addWidget(self.digital_mode_radio)
        display_mode_layout.addWidget(self.analog_mode_radio)
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light Theme", "light")
        self.theme_combo.addItem("Dark Theme", "dark")
        
        theme_layout.addWidget(self.theme_combo)
        display_mode_layout.addLayout(theme_layout)
        
        # Meeting timing options
        timing_group = QGroupBox("Meeting Timing")
        timing_layout = QVBoxLayout(timing_group)
        
        self.show_end_time_check = QCheckBox("Show predicted meeting end time")
        self.show_end_time_check.setToolTip("Display the predicted meeting end time based on current progress")
        timing_layout.addWidget(self.show_end_time_check)
        
        # Screen selection
        screen_group = QGroupBox("Screen Selection")
        screen_layout = QFormLayout(screen_group)
        
        # Get available screens
        self.available_screens = self.settings_controller.get_all_screens()
        
        # Primary screen selection
        self.primary_screen_combo = QComboBox()
        for screen in self.available_screens:
            self.primary_screen_combo.addItem(
                f"{screen['name']} ({screen['width']}x{screen['height']})", 
                screen['index']
            )
        
        # Secondary screen selection
        self.secondary_screen_combo = QComboBox()
        self.secondary_screen_combo.clear()  # Clear any existing items
        self.secondary_screen_combo.addItem("None", None)

        # Add all screens to the secondary dropdown
        for screen in self.available_screens:
            self.secondary_screen_combo.addItem(
                f"{screen['name']} ({screen['width']}x{screen['height']})", 
                screen['index']
            )
        
        self.use_secondary_check = QCheckBox("Use Secondary Display")
        self.use_secondary_check.toggled.connect(self._toggle_secondary_screen)
        
        screen_layout.addRow("Primary Screen:", self.primary_screen_combo)
        screen_layout.addRow("Secondary Screen:", self.secondary_screen_combo)
        screen_layout.addRow("", self.use_secondary_check)
        
        # Add groups to layout
        layout.addWidget(display_mode_group)
        layout.addWidget(timing_group)
        layout.addWidget(screen_group)
        layout.addStretch()
    
    def _setup_meeting_source_tab(self):
        """Setup meeting source settings tab"""
        layout = QVBoxLayout(self.meeting_source_tab)
        
        # Meeting source mode
        source_mode_group = QGroupBox("Meeting Data Source")
        source_mode_layout = QVBoxLayout(source_mode_group)
        
        # Create radio buttons for each mode
        self.source_mode_radios = {}
        self.source_mode_group = QButtonGroup(self)
        
        for mode in MeetingSourceMode:
            radio = QRadioButton(self._get_source_mode_display_name(mode))
            self.source_mode_radios[mode] = radio
            self.source_mode_group.addButton(radio)
            source_mode_layout.addWidget(radio)
        
        # Web scraping options
        self.web_options_group = QGroupBox("Web Scraping Options")
        web_options_layout = QVBoxLayout(self.web_options_group)
        
        self.auto_update_check = QCheckBox("Automatically update meetings from the web")
        self.auto_update_check.setToolTip("Update meetings from wol.jw.org when the application starts")
        
        self.save_scraped_check = QCheckBox("Save scraped meetings as templates")
        self.save_scraped_check.setToolTip("Save scraped meeting data as templates for future use")
        
        web_options_layout.addWidget(self.auto_update_check)
        web_options_layout.addWidget(self.save_scraped_check)
        
        # Song options
        self.song_options_group = QGroupBox("Song Entry Options")
        song_options_layout = QVBoxLayout(self.song_options_group)
        
        self.weekend_songs_manual_check = QCheckBox("Always manually enter weekend songs")
        self.weekend_songs_manual_check.setToolTip("Weekend songs must be entered manually for each meeting")
        
        song_options_layout.addWidget(self.weekend_songs_manual_check)
        
        # Connect source mode changes to toggle option groups
        for mode, radio in self.source_mode_radios.items():
            radio.toggled.connect(self._update_source_options_visibility)
        
        # Add groups to layout
        layout.addWidget(source_mode_group)
        layout.addWidget(self.web_options_group)
        layout.addWidget(self.song_options_group)
        layout.addStretch()
    
    def _get_source_mode_display_name(self, mode: MeetingSourceMode) -> str:
        """Get a user-friendly display name for source modes"""
        if mode == MeetingSourceMode.WEB_SCRAPING:
            return "Web Scraping (Automatically download from wol.jw.org)"
        elif mode == MeetingSourceMode.MANUAL_ENTRY:
            return "Manual Entry (Enter meeting parts manually)"
        elif mode == MeetingSourceMode.TEMPLATE_BASED:
            return "Template-Based (Use templates with modifications)"
        return str(mode)
    
    def _update_source_options_visibility(self):
        """Update visibility of option groups based on selected source mode"""
        # Determine which mode is selected
        selected_mode = None
        for mode, radio in self.source_mode_radios.items():
            if radio.isChecked():
                selected_mode = mode
                break
        
        # Update visibility based on selected mode
        if selected_mode == MeetingSourceMode.WEB_SCRAPING:
            self.web_options_group.setVisible(True)
            self.auto_update_check.setEnabled(True)
            self.save_scraped_check.setEnabled(True)
        else:
            self.web_options_group.setVisible(False)
        
        # Song options are always visible, but context changes
        if selected_mode == MeetingSourceMode.WEB_SCRAPING:
            self.weekend_songs_manual_check.setText("Always manually enter weekend songs")
        else:
            self.weekend_songs_manual_check.setText("Include song placeholders in templates")
    
    def _load_settings(self):
        """Load current settings into UI"""
        settings = self.settings_controller.get_settings()
        
        # General settings
        language_index = self.language_combo.findData(settings.language)
        if language_index >= 0:
            self.language_combo.setCurrentIndex(language_index)
        
        # Meeting settings
        self.midweek_day_combo.setCurrentIndex(settings.midweek_meeting.day.value)
        self.midweek_time_edit.setTime(QTime(
            settings.midweek_meeting.time.hour,
            settings.midweek_meeting.time.minute
        ))
        
        self.weekend_day_combo.setCurrentIndex(settings.weekend_meeting.day.value)
        self.weekend_time_edit.setTime(QTime(
            settings.weekend_meeting.time.hour,
            settings.weekend_meeting.time.minute
        ))
        
        # Display settings
        is_digital = settings.display.display_mode == TimerDisplayMode.DIGITAL
        self.digital_mode_radio.setChecked(is_digital)
        self.analog_mode_radio.setChecked(not is_digital)
        
        # Theme setting
        theme_index = self.theme_combo.findData(settings.display.theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        # Predicted end time
        self.show_end_time_check.setChecked(settings.display.show_predicted_end_time)
        
        # Screen settings
        primary_index = self.primary_screen_combo.findData(settings.display.primary_screen_index)
        if primary_index >= 0:
            self.primary_screen_combo.setCurrentIndex(primary_index)
        
        secondary_index = self.secondary_screen_combo.findData(settings.display.secondary_screen_index)
        if secondary_index >= 0:
            self.secondary_screen_combo.setCurrentIndex(secondary_index)
        
        self.use_secondary_check.setChecked(settings.display.use_secondary_screen)
        self._toggle_secondary_screen(settings.display.use_secondary_screen)
        
        # Meeting source settings
        source_mode = settings.meeting_source.mode
        if source_mode in self.source_mode_radios:
            self.source_mode_radios[source_mode].setChecked(True)
        
        self.auto_update_check.setChecked(settings.meeting_source.auto_update_meetings)
        self.save_scraped_check.setChecked(settings.meeting_source.save_scraped_as_template)
        self.weekend_songs_manual_check.setChecked(settings.meeting_source.weekend_songs_manual)
        
        # Update visibility based on current settings
        self._update_source_options_visibility()
    
    def _apply_settings(self):
        """Apply settings changes"""
        # General settings
        language = self.language_combo.currentData()
        self.settings_controller.set_language(language)
        
        # Meeting settings
        midweek_day = DayOfWeek(self.midweek_day_combo.currentData())
        midweek_time_qtime = self.midweek_time_edit.time()
        midweek_time = time(midweek_time_qtime.hour(), midweek_time_qtime.minute())
        
        self.settings_controller.set_midweek_meeting(midweek_day, midweek_time)
        
        weekend_day = DayOfWeek(self.weekend_day_combo.currentData())
        weekend_time_qtime = self.weekend_time_edit.time()
        weekend_time = time(weekend_time_qtime.hour(), weekend_time_qtime.minute())
        
        self.settings_controller.set_weekend_meeting(weekend_day, weekend_time)
        
        # Display settings
        display_mode = TimerDisplayMode.DIGITAL if self.digital_mode_radio.isChecked() else TimerDisplayMode.ANALOG
        self.settings_controller.set_display_mode(display_mode)
        
        # Theme setting
        theme = self.theme_combo.currentData()
        self.settings_controller.set_theme(theme)
        
        # Predicted end time
        self.settings_controller.set_show_predicted_end_time(self.show_end_time_check.isChecked())
        
        # Screen settings
        primary_screen = self.primary_screen_combo.currentData()
        self.settings_controller.set_primary_screen(primary_screen)
        
        if self.use_secondary_check.isChecked():
            secondary_screen = self.secondary_screen_combo.currentData()
            self.settings_controller.set_secondary_screen(secondary_screen)
        else:
            self.settings_controller.toggle_secondary_screen(False)
        
        # Meeting source settings
        for mode, radio in self.source_mode_radios.items():
            if radio.isChecked():
                self.settings_controller.set_meeting_source_mode(mode)
                break
        
        self.settings_controller.set_auto_update_meetings(self.auto_update_check.isChecked())
        self.settings_controller.set_save_scraped_as_template(self.save_scraped_check.isChecked())
        self.settings_controller.set_weekend_songs_manual(self.weekend_songs_manual_check.isChecked())
    
    def _reset_settings(self):
        """Reset settings to defaults"""
        self.settings_controller.reset_settings()
        self._load_settings()
    
    def _toggle_secondary_screen(self, enabled):
        """Toggle secondary screen combo box"""
        self.secondary_screen_combo.setEnabled(enabled)
    
    def accept(self):
        """Handle dialog acceptance"""
        self._apply_settings()
        super().accept()