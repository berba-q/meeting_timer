"""
Settings dialog for the JW Meeting Timer application.
"""
import os
from datetime import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QCheckBox, QTimeEdit, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTime

from src.controllers.settings_controller import SettingsController
from src.models.settings import DayOfWeek, TimerDisplayMode


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
        
        self._setup_general_tab()
        self._setup_meetings_tab()
        self._setup_display_tab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.meetings_tab, "Meetings")
        self.tab_widget.addTab(self.display_tab, "Display")
        
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
        
        # Auto update settings
        update_group = QGroupBox("Updates")
        update_layout = QVBoxLayout(update_group)
        
        self.auto_update_check = QCheckBox("Automatically update meetings from the web")
        update_layout.addWidget(self.auto_update_check)
        
        # Add groups to layout
        layout.addWidget(language_group)
        layout.addWidget(update_group)
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
        self.secondary_screen_combo.addItem("None", None)
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
    
    def _load_settings(self):
        """Load current settings into UI"""
        settings = self.settings_controller.get_settings()
        
        # General settings
        language_index = self.language_combo.findData(settings.language)
        if language_index >= 0:
            self.language_combo.setCurrentIndex(language_index)
        
        self.auto_update_check.setChecked(settings.auto_update_meetings)
        
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
    
    def _apply_settings(self):
        """Apply settings changes"""
        # General settings
        language = self.language_combo.currentData()
        self.settings_controller.set_language(language)
        
        self.settings_controller.set_auto_update_meetings(self.auto_update_check.isChecked())
        
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