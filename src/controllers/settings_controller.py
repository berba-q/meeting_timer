"""
Controller for managing application settings in the OnTime Meeting Timer application.
"""
from datetime import time
from typing import List, Dict
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QScreen

from src.utils.screen_handler import ScreenHandler
from src.models.settings import (
    SettingsManager, AppSettings, MeetingSettings, 
    DisplaySettings, DayOfWeek, TimerDisplayMode, 
    MeetingSourceMode, MeetingSourceSettings
)
from src.models.settings import NetworkDisplayMode, NetworkDisplaySettings


class SettingsController(QObject):
    """Controller for managing application settings"""
    
    # Signals
    settings_changed = pyqtSignal()
    language_changed = pyqtSignal(str)
    display_mode_changed = pyqtSignal(TimerDisplayMode)
    theme_changed = pyqtSignal(str)
    meeting_source_mode_changed = pyqtSignal(MeetingSourceMode)
    primary_screen_changed = pyqtSignal(int)  # Emits the new primary screen index
    secondary_screen_changed = pyqtSignal(int, bool)  # Emits (screen_index, enabled)
    network_display_mode_changed = pyqtSignal(NetworkDisplayMode)
    network_display_ports_changed = pyqtSignal(int, int)  # HTTP port, WS port
    network_display_options_changed = pyqtSignal(bool, bool)  # Auto-start, QR code
    
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings_manager = settings_manager
        
        # Initialize correct screen indices if not already set
        self._initialize_screen_settings()
    
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
        if screen_index != self.settings_manager.settings.display.primary_screen_index:
            # Check if this was previously the secondary screen
            if screen_index == self.settings_manager.settings.display.secondary_screen_index:
                # Swap screens
                old_primary = self.settings_manager.settings.display.primary_screen_index
                self.settings_manager.settings.display.secondary_screen_index = old_primary
            
            # Set new primary
            self.settings_manager.settings.display.primary_screen_index = screen_index
            self.settings_manager.save_settings()
            self.primary_screen_changed.emit(screen_index)
            self.settings_changed.emit()
    
    def set_secondary_screen(self, screen_index: int):
        """Set secondary screen index"""
        if screen_index != self.settings_manager.settings.display.secondary_screen_index:
            # Check if this was previously the primary screen
            if screen_index == self.settings_manager.settings.display.primary_screen_index:
                # Swap screens
                old_secondary = self.settings_manager.settings.display.secondary_screen_index
                self.settings_manager.settings.display.primary_screen_index = old_secondary
            
            # Set new secondary
            self.settings_manager.settings.display.secondary_screen_index = screen_index
            
            # If enabling or changing secondary screen, make sure it's enabled
            self.settings_manager.settings.display.use_secondary_screen = True
            
            self.settings_manager.save_settings()
            self.secondary_screen_changed.emit(screen_index, True)
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

    def set_start_reminder_enabled(self, enabled: bool):
        """Enable/disable start timer reminder"""
        self.settings_manager.settings.start_reminder_enabled = enabled
        self.settings_manager.save_settings()
        self.settings_changed.emit()

    def set_start_reminder_delay(self, delay: int):
        """Set delay (seconds) before start timer reminder"""
        self.settings_manager.settings.start_reminder_delay = delay
        self.settings_manager.save_settings()
        self.settings_changed.emit()

    def set_overrun_enabled(self, enabled: bool):
        """Enable/disable part overrun reminder"""
        self.settings_manager.settings.overrun_enabled = enabled
        self.settings_manager.save_settings()
        self.settings_changed.emit()

    def set_overrun_delay(self, delay: int):
        """Set delay (seconds) before part overrun reminder"""
        self.settings_manager.settings.overrun_delay = delay
        self.settings_manager.save_settings()
        self.settings_changed.emit()
    
    def get_all_screens(self):
        """Get information about all available screens"""
        return ScreenHandler.get_all_screens()
    
    def _initialize_screen_settings(self):
        """Initialize screen settings with correct values if not already set"""
        settings = self.settings_manager.settings
        screens = ScreenHandler.get_all_screens()
        
        # Set primary screen to system primary if not set
        if settings.display.primary_screen_index is None:
            settings.display.primary_screen_index = ScreenHandler.get_primary_screen_index()
        
        # Set secondary screen to first non-primary screen if not set
        if settings.display.secondary_screen_index is None:
            primary_index = settings.display.primary_screen_index
            # Look for a screen that's not the primary
            for screen in screens:
                if screen['index'] != primary_index:
                    settings.display.secondary_screen_index = screen['index']
                    break
            
            # If no secondary screen found, use same as primary (will be disabled)
            if settings.display.secondary_screen_index is None and screens:
                settings.display.secondary_screen_index = primary_index
                settings.display.use_secondary_screen = False
                
    def set_network_display_mode(self, mode: NetworkDisplayMode):
        """Set network display mode"""
        if mode != self.settings_manager.settings.network_display.mode:
            self.settings_manager.settings.network_display.mode = mode
            self.settings_manager.save_settings()
            self.network_display_mode_changed.emit(mode)
            self.settings_changed.emit()

    def set_network_display_ports(self, http_port: int, ws_port: int):
        """Set network display ports"""
        settings = self.settings_manager.settings.network_display
        if http_port != settings.http_port or ws_port != settings.ws_port:
            settings.http_port = http_port
            settings.ws_port = ws_port
            self.settings_manager.save_settings()
            self.network_display_ports_changed.emit(http_port, ws_port)
            self.settings_changed.emit()

    def set_network_display_options(self, auto_start: bool, qr_code_enabled: bool):
        """Set network display options"""
        settings = self.settings_manager.settings.network_display
        if auto_start != settings.auto_start or qr_code_enabled != settings.qr_code_enabled:
            settings.auto_start = auto_start
            settings.qr_code_enabled = qr_code_enabled
            self.settings_manager.save_settings()
            self.network_display_options_changed.emit(auto_start, qr_code_enabled)
            self.settings_changed.emit()
        
        # Save updated settings
        self.settings_manager.save_settings()