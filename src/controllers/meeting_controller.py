"""
Controller for managing meetings in the JW Meeting Timer application.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from src.models.meeting import Meeting, MeetingType
from src.models.settings import SettingsManager
from src.utils.scraper import MeetingScraper


class MeetingController(QObject):
    """Controller for managing meeting data"""
    
    # Signals
    meeting_updated = pyqtSignal(Meeting)
    meetings_loaded = pyqtSignal(dict)  # Dict[MeetingType, Meeting]
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Setup data directories
        self.data_dir = os.path.join(os.path.expanduser("~"), ".jwmeetingtimer")
        self.meetings_dir = os.path.join(self.data_dir, "meetings")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.meetings_dir, exist_ok=True)
        
        # Load settings
        self.settings_manager = SettingsManager(
            os.path.join(self.data_dir, "settings.json")
        )
        
        # Current meetings
        self.current_meetings: Dict[MeetingType, Meeting] = {}
        self.current_meeting: Optional[Meeting] = None
        
        # Initialize scraper
        self.scraper = MeetingScraper(self.settings_manager.settings.language)
    
    def load_meetings(self):
        """Load the most recent meetings"""
        # Check if we need to update meetings from web
        if self.settings_manager.settings.auto_update_meetings:
            self.update_meetings_from_web()
        else:
            # Load from local files
            self._load_local_meetings()
    
    def update_meetings_from_web(self):
        """Update meetings from the web"""
        try:
            # Update scraper language
            self.scraper.language = self.settings_manager.settings.language
            
            # Fetch meetings
            meetings = self.scraper.update_meetings()
            
            # Update current meetings
            self.current_meetings = meetings
            
            # Save fetched meetings
            for meeting_type, meeting in meetings.items():
                self.save_meeting(meeting)
            
            # Emit signal
            self.meetings_loaded.emit(self.current_meetings)
            
        except Exception as e:
            error_message = f"Failed to update meetings: {str(e)}"
            print(error_message)
            self.error_occurred.emit(error_message)
            
            # If update fails, try loading from local files
            self._load_local_meetings()
    
    def _load_local_meetings(self):
        """Load the most recent meetings from local files"""
        meetings = {}
        
        try:
            # Get all meeting files
            meeting_files = [f for f in os.listdir(self.meetings_dir) 
                           if f.endswith('.json')]
            
            # Group by meeting type
            midweek_files = [f for f in meeting_files if 'midweek' in f.lower()]
            weekend_files = [f for f in meeting_files if 'weekend' in f.lower()]
            
            # Sort by date (assuming filename contains date)
            midweek_files.sort(reverse=True)
            weekend_files.sort(reverse=True)
            
            # Load most recent of each type
            if midweek_files:
                midweek_meeting = self._load_meeting_file(
                    os.path.join(self.meetings_dir, midweek_files[0])
                )
                if midweek_meeting:
                    meetings[MeetingType.MIDWEEK] = midweek_meeting
            
            if weekend_files:
                weekend_meeting = self._load_meeting_file(
                    os.path.join(self.meetings_dir, weekend_files[0])
                )
                if weekend_meeting:
                    meetings[MeetingType.WEEKEND] = weekend_meeting
            
            self.current_meetings = meetings
            self.meetings_loaded.emit(meetings)
            
        except Exception as e:
            error_message = f"Failed to load meetings: {str(e)}"
            print(error_message)
            self.error_occurred.emit(error_message)
    
    def _load_meeting_file(self, file_path: str) -> Optional[Meeting]:
        """Load a meeting from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                meeting_data = json.load(f)
            return Meeting.from_dict(meeting_data)
        except Exception as e:
            print(f"Error loading meeting file {file_path}: {e}")
            return None
    
    def save_meeting(self, meeting: Meeting):
        """Save a meeting to a file"""
        # Create filename with date and meeting type
        date_str = meeting.date.strftime("%Y-%m-%d")
        filename = f"{meeting.meeting_type.value}_{date_str}.json"
        file_path = os.path.join(self.meetings_dir, filename)
        
        # Save meeting data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(meeting.to_dict(), f, indent=2)
        
        # Add to recent meetings list if not already there
        if file_path not in self.settings_manager.settings.recent_meetings:
            self.settings_manager.settings.recent_meetings.append(file_path)
            
            # Limit to last 10 meetings
            if len(self.settings_manager.settings.recent_meetings) > 10:
                self.settings_manager.settings.recent_meetings.pop(0)
            
            self.settings_manager.save_settings()
    
    def set_current_meeting(self, meeting: Meeting):
        """Set the currently active meeting"""
        self.current_meeting = meeting
        self.meeting_updated.emit(meeting)
    
    def get_meeting(self, meeting_type: MeetingType) -> Optional[Meeting]:
        """Get a meeting by type"""
        return self.current_meetings.get(meeting_type)
    
    def create_custom_meeting(self, title: str, date: datetime) -> Meeting:
        """Create a new custom meeting"""
        # Create blank meeting
        meeting = Meeting(
            meeting_type=MeetingType.CUSTOM,
            title=title,
            date=date,
            start_time=datetime.now().time(),
            sections=[]
        )
        
        return meeting
    
    def add_section_to_meeting(self, meeting: Meeting, section_title: str) -> Meeting:
        """Add a new section to a meeting"""
        from src.models.meeting import MeetingSection
        
        # Create new section
        section = MeetingSection(
            title=section_title,
            parts=[]
        )
        
        # Add to meeting
        meeting.sections.append(section)
        
        # If this is the current meeting, emit update
        if meeting is self.current_meeting:
            self.meeting_updated.emit(meeting)
        
        return meeting
    
    def add_part_to_section(self, meeting: Meeting, section_index: int, 
                            part_title: str, duration_minutes: int) -> Meeting:
        """Add a new part to a section in a meeting"""
        from src.models.meeting import MeetingPart
        
        # Create new part
        part = MeetingPart(
            title=part_title,
            duration_minutes=duration_minutes
        )
        
        # Add to section
        if 0 <= section_index < len(meeting.sections):
            meeting.sections[section_index].parts.append(part)
        
        # If this is the current meeting, emit update
        if meeting is self.current_meeting:
            self.meeting_updated.emit(meeting)
        
        return meeting