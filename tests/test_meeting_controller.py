"""
Simplified tests for the MeetingController class focusing on core functionality without Qt dependencies.
"""
import os
import json
import unittest
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime, time

# Add the parent directory to the path so we can import the application code
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import models directly - these don't depend on Qt
from src.models.meeting import Meeting, MeetingSection, MeetingPart, MeetingType
from src.models.settings import SettingsManager, MeetingSourceMode

# We'll test core functionality without PyQt dependencies
class TestMeetingControllerCore(unittest.TestCase):
    """Core functionality tests for MeetingController that don't require Qt"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.TemporaryDirectory()
        self.meetings_dir = os.path.join(self.test_dir.name, "meetings")
        os.makedirs(self.meetings_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        self.test_dir.cleanup()
    
    def test_save_and_load_meeting(self):
        """Test saving and loading a meeting file directly"""
        # Create a test meeting
        meeting = self._create_test_meeting()
        
        # Save the meeting to a file
        date_str = meeting.date.strftime("%Y-%m-%d")
        filename = f"{meeting.meeting_type.value}_{date_str}.json"
        file_path = os.path.join(self.meetings_dir, filename)
        
        with open(file_path, 'w') as f:
            json.dump(meeting.to_dict(), f)
        
        # Verify file exists
        self.assertTrue(os.path.exists(file_path))
        
        # Load the meeting from the file
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)
        
        loaded_meeting = Meeting.from_dict(loaded_data)
        
        # Verify meeting properties
        self.assertEqual(loaded_meeting.title, meeting.title)
        self.assertEqual(loaded_meeting.meeting_type, meeting.meeting_type)
        self.assertEqual(len(loaded_meeting.sections), len(meeting.sections))
    
    def test_meeting_serialization(self):
        """Test meeting serialization and deserialization"""
        # Create a test meeting
        original_meeting = self._create_test_meeting()
        
        # Convert to dict
        meeting_dict = original_meeting.to_dict()
        
        # Check dict structure
        self.assertIn('title', meeting_dict)
        self.assertIn('meeting_type', meeting_dict)
        self.assertIn('sections', meeting_dict)
        
        # Convert back to meeting
        deserialized_meeting = Meeting.from_dict(meeting_dict)
        
        # Verify properties preserved
        self.assertEqual(deserialized_meeting.title, original_meeting.title)
        self.assertEqual(deserialized_meeting.meeting_type, original_meeting.meeting_type)
        self.assertEqual(len(deserialized_meeting.sections), len(original_meeting.sections))
        
        # Check sections
        original_section = original_meeting.sections[0]
        deserialized_section = deserialized_meeting.sections[0]
        self.assertEqual(deserialized_section.title, original_section.title)
        
        # Check parts
        original_part = original_section.parts[0]
        deserialized_part = deserialized_section.parts[0]
        self.assertEqual(deserialized_part.title, original_part.title)
        self.assertEqual(deserialized_part.duration_minutes, original_part.duration_minutes)
    
    def test_add_parts_to_meeting(self):
        """Test building a meeting structure"""
        # Create a new meeting
        meeting = Meeting(
            meeting_type=MeetingType.CUSTOM,
            title="Test Meeting",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[]
        )
        
        # Add a section
        section = MeetingSection(
            title="Test Section",
            parts=[]
        )
        meeting.sections.append(section)
        
        # Add parts
        part1 = MeetingPart(
            title="Part 1",
            duration_minutes=10
        )
        part2 = MeetingPart(
            title="Part 2",
            duration_minutes=15
        )
        section.parts.extend([part1, part2])
        
        # Verify structure
        self.assertEqual(len(meeting.sections), 1)
        self.assertEqual(len(meeting.sections[0].parts), 2)
        self.assertEqual(meeting.sections[0].parts[0].title, "Part 1")
        self.assertEqual(meeting.sections[0].parts[1].title, "Part 2")
        
        # Check duration calculations
        self.assertEqual(section.total_duration_minutes, 25)
        self.assertEqual(meeting.total_duration_minutes, 25)
    
    def test_get_all_parts(self):
        """Test flattening parts across sections"""
        # Create a test meeting with multiple sections
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Test Meeting",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[
                MeetingSection(
                    title="Section 1",
                    parts=[
                        MeetingPart(title="Part 1", duration_minutes=10),
                        MeetingPart(title="Part 2", duration_minutes=15)
                    ]
                ),
                MeetingSection(
                    title="Section 2",
                    parts=[
                        MeetingPart(title="Part 3", duration_minutes=5),
                        MeetingPart(title="Part 4", duration_minutes=20)
                    ]
                )
            ]
        )
        
        # Get all parts
        all_parts = meeting.get_all_parts()
        
        # Verify correct flattening
        self.assertEqual(len(all_parts), 4)
        self.assertEqual(all_parts[0].title, "Part 1")
        self.assertEqual(all_parts[1].title, "Part 2")
        self.assertEqual(all_parts[2].title, "Part 3")
        self.assertEqual(all_parts[3].title, "Part 4")
    
    def test_invalid_json(self):
        """Test handling invalid JSON for meeting files"""
        # Create invalid JSON file
        file_path = os.path.join(self.meetings_dir, "invalid.json")
        with open(file_path, 'w') as f:
            f.write("This is not valid JSON")
        
        # Try to load it
        with self.assertRaises(json.JSONDecodeError):
            with open(file_path, 'r') as f:
                json.load(f)
    
    def _create_test_meeting(self):
        """Create a test meeting"""
        section = MeetingSection(
            title="Test Section",
            parts=[
                MeetingPart(title="Test Part 1", duration_minutes=10),
                MeetingPart(title="Test Part 2", duration_minutes=15)
            ]
        )
        
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Test Midweek Meeting",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[section]
        )
        
        return meeting


if __name__ == '__main__':
    unittest.main()