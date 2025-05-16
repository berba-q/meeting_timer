"""
Controller for managing meetings in the OnTime Meeting Timer application.
"""
import os
import json
import re
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWidgets import QDialog

from src.models.meeting import Meeting, MeetingType, MeetingSection, MeetingPart
from src.models.settings import SettingsManager, MeetingSourceMode
from src.models.meeting_template import MeetingTemplate, TemplateType
from src.utils.scraper import MeetingScraper
from src.utils.helpers import safe_json_load, safe_json_save
from src.views.weekend_song_editor import WeekendSongEditorDialog


class MeetingController(QObject):
    """Controller for managing meeting data"""
    
    # Signals
    meeting_updated = pyqtSignal(Meeting)
    meetings_loaded = pyqtSignal(dict)  # Dict[MeetingType, Meeting]
    error_occurred = pyqtSignal(str)
    part_updated = pyqtSignal(MeetingPart, int, int)  # part, section_index, part_index
    
    def __init__(self):
        super().__init__()
        
        # Setup data directories
        self.data_dir = os.path.join(os.path.expanduser("~"), ".ontime")
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
        
        # Initialize template manager
        self.template_manager = MeetingTemplate()
    
    def load_meetings(self):
        """Load the most recent meetings"""
        meeting_source_mode = self.settings_manager.settings.meeting_source.mode
        
        # Check if we need to update meetings from web
        if (meeting_source_mode == MeetingSourceMode.WEB_SCRAPING and 
            self.settings_manager.settings.meeting_source.auto_update_meetings):
            self.update_meetings_from_web()
        else:
            # Load from local files or templates based on mode
            self._load_local_meetings()
        
        # Process weekend meeting songs if present
        if MeetingType.WEEKEND in self.current_meetings:
            weekend_meeting = self.current_meetings[MeetingType.WEEKEND]
            self.process_weekend_meeting_songs(weekend_meeting)
            
            # Save processed meeting
            self.save_meeting(weekend_meeting)
    
    def update_meetings_from_web(self):
        """Update meetings from the web"""
        try:
            # Update scraper language
            self.scraper.language = self.settings_manager.settings.language

            # Fetch meetings
            meetings = self.scraper.update_meetings()

            # Handle weekend songs manual entry if enabled
            if self.settings_manager.settings.meeting_source.weekend_songs_manual:
                if MeetingType.WEEKEND in meetings:
                    weekend_meeting = meetings[MeetingType.WEEKEND]
                    self.process_weekend_meeting_songs(weekend_meeting)

            # Save scraped meetings as templates if option enabled
            if self.settings_manager.settings.meeting_source.save_scraped_as_template:
                self._save_meetings_as_templates(meetings)

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
        return self.current_meetings
    
    def process_weekend_meeting_songs(self, meeting: Meeting):
        """
        Process weekend meeting songs to ensure they're properly displayed
        - Formats song titles consistently
        - Highlights missing song numbers
        - Returns True if songs need manual entry
        """
        if meeting.meeting_type != MeetingType.WEEKEND:
            return False
        
        needs_manual_update = False
        
        for section in meeting.sections:
            for part in section.parts:
                part_title_lower = part.title.lower()
                
                if "song" in part_title_lower:
                    # Check if there's a song number
                    song_num_match = re.search(r'song\s+(\d+)', part_title_lower)
                    
                    if not song_num_match:
                        # No song number found
                        needs_manual_update = True
                        
                        # Format the title to indicate missing song number
                        if "song" == part_title_lower.strip():
                            # Very generic title, enhance it based on position
                            if "public" in section.title.lower():
                                if "prayer" in part_title_lower:
                                    part.title = "Opening Song and Prayer"
                                else:
                                    part.title = "Opening Song"
                            elif "watchtower" in section.title.lower():
                                if "concluding" in part_title_lower or "prayer" in part_title_lower:
                                    part.title = "Concluding Song and Prayer"
                                else:
                                    part.title = "Song"
                    else:
                        # Song number found, ensure consistent formatting
                        song_num = song_num_match.group(1)
                        
                        # Format based on whether it includes prayer
                        if "prayer" in part_title_lower:
                            if "opening" in part_title_lower or "public" in section.title.lower():
                                part.title = f"Song {song_num} and Opening Prayer"
                            elif "concluding" in part_title_lower or "watchtower" in section.title.lower():
                                part.title = f"Song {song_num} and Concluding Prayer"
                            else:
                                part.title = f"Song {song_num} and Prayer"
                        else:
                            part.title = f"Song {song_num}"
        
        return needs_manual_update
    
    def _show_weekend_song_editor(self, meeting: Meeting):
        """Show the weekend song editor dialog"""
        
        # Get parent window if any
        parent = QApplication.activeWindow()
        
        dialog = WeekendSongEditorDialog(meeting, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save the updated meeting
            self.save_meeting(meeting)
            
            # If this is the current meeting, emit update signal
            if meeting is self.current_meeting:
                self.meeting_updated.emit(meeting)
    
    def _clear_weekend_songs(self, meeting: Meeting):
        """
        Clear song information from weekend meeting to be manually entered
        but preserve songs that already have numbers
        """
        # First check if all songs already have numbers - if so, preserve them
        all_songs_have_numbers = True
        
        for section in meeting.sections:
            for part in section.parts:
                part_title_lower = part.title.lower()
                if "song" in part_title_lower:
                    # Check if it has a song number
                    song_match = re.search(r'song\s+(\d+)', part_title_lower)
                    if not song_match:
                        all_songs_have_numbers = False
                        break
        
        # If all songs already have numbers, keep them!
        if all_songs_have_numbers:
            return
        
        # Otherwise, clear songs as before for manual entry
        for section in meeting.sections:
            for part in section.parts:
                part_title_lower = part.title.lower()
                if "song" in part_title_lower or "song" in section.title.lower():
                    # Keep the part but clear specific song number
                    if part_title_lower.startswith("song"):
                        # Try to preserve the structure (e.g., "Song 123" -> "Song")
                        part.title = "Song"
                    elif "song" in part_title_lower:
                        # If song is mentioned in the middle, preserve the text
                        # E.g., "Opening Song and Prayer" stays the same
                        pass
    
    def _save_meetings_as_templates(self, meetings: Dict[MeetingType, Meeting]):
        """Save fetched meetings as templates for future use"""
        for meeting_type, meeting in meetings.items():
            # Convert to template format
            template_data = {
                'title': meeting.title,
                'language': meeting.language,
                'sections': []
            }
            
            for section in meeting.sections:
                section_data = {
                    'title': section.title,
                    'parts': []
                }
                
                for part in section.parts:
                    part_data = {
                        'title': part.title,
                        'duration_minutes': part.duration_minutes,
                        'presenter': part.presenter,
                        'notes': part.notes
                    }
                    section_data['parts'].append(part_data)
                
                template_data['sections'].append(section_data)
            
            # Save as template
            if meeting_type == MeetingType.MIDWEEK:
                self.template_manager.save_template(TemplateType.MIDWEEK, template_data)
            elif meeting_type == MeetingType.WEEKEND:
                self.template_manager.save_template(TemplateType.WEEKEND, template_data)
    
    def _load_local_meetings(self):
        """Load the most recent meetings from local files"""
        meetings = {}
        
        # Check if we should use templates instead of saved meetings
        meeting_source_mode = self.settings_manager.settings.meeting_source.mode
        
        if meeting_source_mode == MeetingSourceMode.TEMPLATE_BASED:
            # Create meetings from templates
            meetings = self._create_meetings_from_templates()
        else:
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
            
            except Exception as e:
                error_message = f"Failed to load meetings: {str(e)}"
                print(error_message)
                self.error_occurred.emit(error_message)
                
                # Fall back to templates if local loading fails
                if not meetings:
                    meetings = self._create_meetings_from_templates()
        
        self.current_meetings = meetings
        self.meetings_loaded.emit(meetings)
    
    def _create_meetings_from_templates(self) -> Dict[MeetingType, Meeting]:
        """Create meetings from templates for the current week"""
        meetings = {}
        
        # Get current date/time
        now = datetime.now()
        
        # Create midweek meeting
        midweek_day = self.settings_manager.settings.midweek_meeting.day.value
        midweek_time = self.settings_manager.settings.midweek_meeting.time
        
        # Calculate the date for the next midweek meeting
        days_until_midweek = (midweek_day - now.weekday()) % 7
        if days_until_midweek == 0 and now.time() > midweek_time:
            days_until_midweek = 7  # Move to next week if today's meeting passed
        
        midweek_date = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + datetime.timedelta(days=days_until_midweek)
        
        # Create midweek meeting from template
        midweek_meeting = self.template_manager.create_meeting_from_template(
            TemplateType.MIDWEEK,
            midweek_date,
            midweek_time
        )
        
        meetings[MeetingType.MIDWEEK] = midweek_meeting
        
        # Create weekend meeting
        weekend_day = self.settings_manager.settings.weekend_meeting.day.value
        weekend_time = self.settings_manager.settings.weekend_meeting.time
        
        # Calculate the date for the next weekend meeting
        days_until_weekend = (weekend_day - now.weekday()) % 7
        if days_until_weekend == 0 and now.time() > weekend_time:
            days_until_weekend = 7  # Move to next week if today's meeting passed
        
        weekend_date = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + datetime.timedelta(days=days_until_weekend)
        
        # Create weekend meeting from template
        weekend_meeting = self.template_manager.create_meeting_from_template(
            TemplateType.WEEKEND,
            weekend_date,
            weekend_time
        )
        
        meetings[MeetingType.WEEKEND] = weekend_meeting
        
        return meetings
    
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
                           part_title: str, duration_minutes: int, 
                           presenter: str = "") -> Meeting:
        """Add a new part to a section in a meeting"""
        # Create new part
        part = MeetingPart(
            title=part_title,
            duration_minutes=duration_minutes,
            presenter=presenter
        )
        
        # Add to section
        if 0 <= section_index < len(meeting.sections):
            meeting.sections[section_index].parts.append(part)
            
            # Emit part updated signal
            part_index = len(meeting.sections[section_index].parts) - 1
            self.part_updated.emit(part, section_index, part_index)
        
        # If this is the current meeting, emit update
        if meeting is self.current_meeting:
            self.meeting_updated.emit(meeting)
        
        return meeting
    
    def update_part(self, meeting: Meeting, section_index: int, part_index: int, 
                   updated_part: MeetingPart) -> Meeting:
        """Update a part in a meeting section"""
        # Check bounds
        if (0 <= section_index < len(meeting.sections) and 
            0 <= part_index < len(meeting.sections[section_index].parts)):
            
            # Update the part
            meeting.sections[section_index].parts[part_index] = updated_part
            
            # Emit part updated signal
            self.part_updated.emit(updated_part, section_index, part_index)
            
            # If this is the current meeting, save and emit update
            if meeting is self.current_meeting:
                self.save_meeting(meeting)
                self.meeting_updated.emit(meeting)
        
        return meeting
    
    def remove_part(self, meeting: Meeting, section_index: int, part_index: int) -> Meeting:
        """Remove a part from a meeting section"""
        # Check bounds
        if (0 <= section_index < len(meeting.sections) and 
            0 <= part_index < len(meeting.sections[section_index].parts)):
            
            # Remove the part
            removed_part = meeting.sections[section_index].parts.pop(part_index)
            
            # If this is the current meeting, save and emit update
            if meeting is self.current_meeting:
                self.save_meeting(meeting)
                self.meeting_updated.emit(meeting)
        
        return meeting
    
    def get_part_indices(self, meeting: Meeting, global_part_index: int) -> Tuple[int, int]:
        """Convert global part index to section and part indices"""
        current_index = 0
        
        for section_index, section in enumerate(meeting.sections):
            for part_index, part in enumerate(section.parts):
                if current_index == global_part_index:
                    return section_index, part_index
                current_index += 1
        
        # If not found, return invalid indices
        return -1, -1
    
    def edit_part_at_global_index(self, meeting: Meeting, global_part_index: int, 
                                 updated_part: MeetingPart) -> bool:
        """Edit a part identified by its global index across all sections"""
        section_index, part_index = self.get_part_indices(meeting, global_part_index)
        
        if section_index >= 0 and part_index >= 0:
            meeting.sections[section_index].parts[part_index] = updated_part
            
            # Emit part updated signal
            self.part_updated.emit(updated_part, section_index, part_index)
            
            # If this is the current meeting, save and emit update
            if meeting is self.current_meeting:
                self.save_meeting(meeting)
                self.meeting_updated.emit(meeting)
                
            return True
            
        return False
    
    def show_meeting_editor(self, parent=None, meeting: Optional[Meeting] = None, on_meeting_updated=None):
        """Show the meeting editor dialog
        :param parent: Parent widget
        :param meeting: Meeting instance to edit
        :param on_meeting_updated: Optional callback to connect to meeting_updated signal
        """
        from src.views.meeting_editor_dialog import MeetingEditorDialog

        dialog = MeetingEditorDialog(parent, meeting)

        # Connect the signal from the dialog
        if on_meeting_updated:
            dialog.meeting_updated.connect(on_meeting_updated)
        else:
            dialog.meeting_updated.connect(self._handle_meeting_updated)

        # Show the dialog
        dialog.exec()
    
    def _handle_meeting_updated(self, meeting: Meeting):
        """Handle a meeting being updated from the editor"""
        # Save the meeting
        self.save_meeting(meeting)
        
        # Update current meetings dictionary
        self.current_meetings[meeting.meeting_type] = meeting
        
        # Set as current meeting
        self.set_current_meeting(meeting)
        
        # Emit signal to notify all components
        self.meetings_loaded.emit(self.current_meetings)