"""
Meeting data models for the JW Meeting Timer application.
"""
from dataclasses import dataclass
from datetime import datetime, time
from typing import List, Optional
from enum import Enum

class MeetingType(Enum):
    """Types of meetings supported by the application"""
    MIDWEEK = "midweek"
    WEEKEND = "weekend"
    CUSTOM = "custom"

@dataclass
class MeetingPart:
    """Represents a single part in a meeting"""
    title: str
    duration_minutes: int
    presenter: str = ""
    notes: str = ""
    is_completed: bool = False
    
    @property
    def duration_seconds(self) -> int:
        """Convert minutes to seconds"""
        return self.duration_minutes * 60
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'title': self.title,
            'duration_minutes': self.duration_minutes,
            'presenter': self.presenter,
            'notes': self.notes,
            'is_completed': self.is_completed
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MeetingPart':
        """Create from dictionary"""
        return cls(
            title=data['title'],
            duration_minutes=data['duration_minutes'],
            presenter=data.get('presenter', ''),
            notes=data.get('notes', ''),
            is_completed=data.get('is_completed', False)
        )

@dataclass
class MeetingSection:
    """Represents a section of a meeting containing multiple parts"""
    title: str
    parts: List[MeetingPart]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'title': self.title,
            'parts': [part.to_dict() for part in self.parts]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MeetingSection':
        """Create from dictionary"""
        return cls(
            title=data['title'],
            parts=[MeetingPart.from_dict(part) for part in data['parts']]
        )
    
    @property
    def total_duration_minutes(self) -> int:
        """Calculate total duration of all parts in this section"""
        return sum(part.duration_minutes for part in self.parts)

@dataclass
class Meeting:
    """Represents a complete meeting with multiple sections"""
    meeting_type: MeetingType
    title: str
    date: datetime
    start_time: time
    sections: List[MeetingSection]
    language: str = "en"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'meeting_type': self.meeting_type.value,
            'title': self.title,
            'date': self.date.isoformat(),
            'start_time': self.start_time.isoformat(),
            'sections': [section.to_dict() for section in self.sections],
            'language': self.language
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Meeting':
        """Create from dictionary"""
        return cls(
            meeting_type=MeetingType(data['meeting_type']),
            title=data['title'],
            date=datetime.fromisoformat(data['date']),
            start_time=time.fromisoformat(data['start_time']),
            sections=[MeetingSection.from_dict(section) for section in data['sections']],
            language=data.get('language', 'en')
        )
    
    @property
    def total_duration_minutes(self) -> int:
        """Calculate total duration of the entire meeting"""
        return sum(section.total_duration_minutes for section in self.sections)
    
    def get_all_parts(self) -> List[MeetingPart]:
        """Get a flattened list of all parts across all sections"""
        all_parts = []
        for section in self.sections:
            all_parts.extend(section.parts)
        return all_parts