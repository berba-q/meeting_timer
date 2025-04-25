"""
Controller for managing application settings in the JW Meeting Timer application.
"""
from datetime import time
from typing import List, Dict
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QScreen

from src.models.settings import (
    SettingsManager, AppSettings, MeetingSettings, 
    DisplaySettings, DayOfWeek, TimerDisplayMode, 
    MeetingSourceMode, MeetingSourceSettings
)


class SettingsController(QObject):
    """Controller for managing application settings"""
    
    # Signals
    settings_changed = pyqtSignal()
    language_changed = pyqtSignal(str)
    display_mode_changed = pyqtSignal(TimerDisplayMode)
    theme_changed = pyqtSignal(str)
    meeting_source_mode_changed = pyqtSignal(MeetingSourceMode)
    
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings_manager = settings_manager
    
    def get_settings(self) -> AppSettings:
        """Get current settings"""
        return self.settings_manager.settings
    
    def save_settings(self):
        """Save current settings"""
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def reset_settings(self):
        """Reset settings to defaults"""
        self.settings_manager.reset_settings()
        self.settings_changed.emit()
    
    def set_language(self, language: str):
        """Set application language"""
        if language != self.settings_manager.settings.language:
            self.settings_manager.settings.language = language
            self.settings_manager.save_settings()
            self.language_changed.emit(language)
            self.settings_changed.emit()
    
    def set_midweek_meeting(self, day: DayOfWeek, meeting_time: time):
        """Set midweek meeting day and time"""
        self.settings_manager.settings.midweek_meeting = MeetingSettings(
            day=day,
            time=meeting_time
        )
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def set_weekend_meeting(self, day: DayOfWeek, meeting_time: time):
        """Set weekend meeting day and time"""
        self.settings_manager.settings.weekend_meeting = MeetingSettings(
            day=day,
            time=meeting_time
        )
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def set_display_mode(self, display_mode: TimerDisplayMode):
        """Set timer display mode"""
        self.settings_manager.settings.display.display_mode = display_mode
        self.settings_manager.save_settings()
        self.display_mode_changed.emit(display_mode)
        self.settings_changed.emit()
    
    def set_theme(self, theme: str):
        """Set application theme (light or dark)"""
        if theme not in ['light', 'dark']:
            theme = 'light'  # Default to light theme if invalid
            
        self.settings_manager.settings.display.theme = theme
        self.settings_manager.save_settings()
        self.theme_changed.emit(theme)
        self.settings_changed.emit()
    
    def set_show_predicted_end_time(self, enabled: bool):
        """Enable/disable predicted meeting end time"""
        self.settings_manager.settings.display.show_predicted_end_time = enabled
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def set_primary_screen(self, screen_index: int):
        """Set primary screen index"""
        self.settings_manager.settings.display.primary_screen_index = screen_index
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def set_secondary_screen(self, screen_index: int):
        """Set secondary screen index"""
        self.settings_manager.settings.display.secondary_screen_index = screen_index
        self.settings_manager.settings.display.use_secondary_screen = (screen_index is not None)
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def toggle_secondary_screen(self, enabled: bool):
        """Enable/disable secondary screen"""
        self.settings_manager.settings.display.use_secondary_screen = enabled
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    # New methods for meeting source settings
    def set_meeting_source_mode(self, mode: MeetingSourceMode):
        """Set meeting source mode (web scraping, manual entry, template-based)"""
        if mode != self.settings_manager.settings.meeting_source.mode:
            self.settings_manager.settings.meeting_source.mode = mode
            self.settings_manager.save_settings()
            self.meeting_source_mode_changed.emit(mode)
            self.settings_changed.emit()
    
    def set_auto_update_meetings(self, enabled: bool):
        """Enable/disable auto-update of meetings from web"""
        self.settings_manager.settings.meeting_source.auto_update_meetings = enabled
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def set_save_scraped_as_template(self, enabled: bool):
        """Enable/disable saving scraped meetings as templates"""
        self.settings_manager.settings.meeting_source.save_scraped_as_template = enabled
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def set_weekend_songs_manual(self, enabled: bool):
        """Enable/disable manual weekend song entry"""
        self.settings_manager.settings.meeting_source.weekend_songs_manual = enabled
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def get_all_screens(self) -> List[Dict]:
        """Get information about all available screens"""
        from PyQt6.QtWidgets import QApplication
        
        screens = []
        app = QApplication.instance()
        primary_screen = app.primaryScreen()
        
        for i, screen in enumerate(QApplication.screens()):
            geometry = screen.geometry()
            screens.append({
                'index': i,
                'name': screen.name(),
                'width': geometry.width(),
                'height': geometry.height(),
                'primary': (screen == primary_screen)  # Compare to primary screen
            })
        
        return screens