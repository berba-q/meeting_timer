"""
Settings model for the JW Meeting Timer application.
"""
import json
import os
from dataclasses import dataclass, asdict, field
from datetime import time
from enum import Enum
from typing import Dict, Optional, List
from .timer import TimerDisplayMode


class DayOfWeek(Enum):
    """Days of the week"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class MeetingSettings:
    """Settings for a specific meeting type"""
    day: DayOfWeek = DayOfWeek.WEDNESDAY  # Default midweek meeting day
    time: time = field(default_factory=lambda: time(19, 0))  # Default 7:00 PM
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'day': self.day.value,
            'time': self.time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MeetingSettings':
        """Create from dictionary"""
        return cls(
            day=DayOfWeek(data['day']),
            time=time.fromisoformat(data['time'])
        )


@dataclass
class DisplaySettings:
    """Settings for timer display"""
    display_mode: TimerDisplayMode = TimerDisplayMode.DIGITAL
    primary_screen_index: int = 0
    secondary_screen_index: Optional[int] = None
    use_secondary_screen: bool = False
    show_predicted_end_time: bool = True
    theme: str = "light"  # 'light' or 'dark'
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'display_mode': self.display_mode.value,
            'primary_screen_index': self.primary_screen_index,
            'secondary_screen_index': self.secondary_screen_index,
            'use_secondary_screen': self.use_secondary_screen,
            'show_predicted_end_time': self.show_predicted_end_time,
            'theme': self.theme
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DisplaySettings':
        """Create from dictionary"""
        return cls(
            display_mode=TimerDisplayMode(data['display_mode']),
            primary_screen_index=data['primary_screen_index'],
            secondary_screen_index=data['secondary_screen_index'],
            use_secondary_screen=data['use_secondary_screen'],
            show_predicted_end_time=data.get('show_predicted_end_time', True),  # Default to True for backward compatibility
            theme=data.get('theme', 'light')  # Default to light theme for backward compatibility
        )


@dataclass
class AppSettings:
    """Global application settings"""
    language: str = "en"
    midweek_meeting: MeetingSettings = field(default_factory=MeetingSettings)
    weekend_meeting: MeetingSettings = field(default_factory=lambda: MeetingSettings(
        day=DayOfWeek.SATURDAY,
        time=time(10, 0)  # Default 10:00 AM
    ))
    display: DisplaySettings = field(default_factory=DisplaySettings)
    auto_update_meetings: bool = True
    recent_meetings: List[str] = field(default_factory=list)  # List of meeting file paths
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'language': self.language,
            'midweek_meeting': self.midweek_meeting.to_dict(),
            'weekend_meeting': self.weekend_meeting.to_dict(),
            'display': self.display.to_dict(),
            'auto_update_meetings': self.auto_update_meetings,
            'recent_meetings': self.recent_meetings
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppSettings':
        """Create from dictionary"""
        return cls(
            language=data.get('language', 'en'),
            midweek_meeting=MeetingSettings.from_dict(data.get('midweek_meeting', {})),
            weekend_meeting=MeetingSettings.from_dict(data.get('weekend_meeting', {})),
            display=DisplaySettings.from_dict(data.get('display', {})),
            auto_update_meetings=data.get('auto_update_meetings', True),
            recent_meetings=data.get('recent_meetings', [])
        )


class SettingsManager:
    """Manages loading and saving application settings"""
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings = self._load_settings()
    
    def _load_settings(self) -> AppSettings:
        """Load settings from file or create default settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings_dict = json.load(f)
                return AppSettings.from_dict(settings_dict)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error loading settings: {e}")
                return AppSettings()
        return AppSettings()
    
    def save_settings(self):
        """Save current settings to file"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings.to_dict(), f, indent=2)
    
    def reset_settings(self):
        """Reset settings to defaults"""
        self.settings = AppSettings()
        self.save_settings()