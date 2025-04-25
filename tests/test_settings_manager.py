"""
Tests for the SettingsManager class in the JW Meeting Timer application.
"""
import os
import json
import tempfile
import unittest
from datetime import time

# Add the parent directory to the path so we can import the application code
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.settings import (
    SettingsManager, AppSettings, MeetingSettings,
    DisplaySettings, DayOfWeek, TimerDisplayMode, MeetingSourceMode
)


class TestSettingsManager(unittest.TestCase):
    """Test cases for the SettingsManager class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test settings
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_file = os.path.join(self.test_dir.name, "test_settings.json")
        
        # Initialize settings manager with test file
        self.settings_manager = SettingsManager(self.settings_file)
    
    def tearDown(self):
        """Clean up after tests"""
        self.test_dir.cleanup()
    
    def test_default_settings(self):
        """Test default settings creation"""
        # Default settings should be created when no file exists
        settings = self.settings_manager.settings
        
        # Check default values
        self.assertEqual(settings.language, "en")
        self.assertEqual(settings.midweek_meeting.day, DayOfWeek.WEDNESDAY)
        self.assertEqual(settings.midweek_meeting.time, time(19, 0))
        self.assertEqual(settings.weekend_meeting.day, DayOfWeek.SATURDAY)
        self.assertEqual(settings.weekend_meeting.time, time(10, 0))
        self.assertEqual(settings.display.display_mode, TimerDisplayMode.DIGITAL)
        self.assertEqual(settings.display.theme, "light")
        self.assertEqual(settings.meeting_source.mode, MeetingSourceMode.WEB_SCRAPING)
        self.assertTrue(settings.meeting_source.auto_update_meetings)
        self.assertTrue(settings.meeting_source.weekend_songs_manual)
        self.assertEqual(len(settings.recent_meetings), 0)
    
    def test_save_and_load_settings(self):
        """Test saving and loading settings"""
        # Modify some settings
        self.settings_manager.settings.language = "es"
        self.settings_manager.settings.display.theme = "dark"
        self.settings_manager.settings.midweek_meeting.day = DayOfWeek.MONDAY
        self.settings_manager.settings.midweek_meeting.time = time(18, 30)
        
        # Save settings
        self.settings_manager.save_settings()
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.settings_file))
        
        # Load settings in a new manager
        new_manager = SettingsManager(self.settings_file)
        loaded_settings = new_manager.settings
        
        # Verify loaded settings match what we saved
        self.assertEqual(loaded_settings.language, "es")
        self.assertEqual(loaded_settings.display.theme, "dark")
        self.assertEqual(loaded_settings.midweek_meeting.day, DayOfWeek.MONDAY)
        self.assertEqual(loaded_settings.midweek_meeting.time, time(18, 30))
    
    def test_file_format(self):
        """Test the format of the saved settings file"""
        # Save default settings
        self.settings_manager.save_settings()
        
        # Read the raw JSON
        with open(self.settings_file, 'r') as f:
            settings_json = json.load(f)
        
        # Check for expected keys
        expected_keys = ['language', 'midweek_meeting', 'weekend_meeting', 'display', 'meeting_source', 'recent_meetings']
        for key in expected_keys:
            self.assertIn(key, settings_json)
        
        # Check nested structure
        self.assertIn('day', settings_json['midweek_meeting'])
        self.assertIn('time', settings_json['midweek_meeting'])
        self.assertIn('display_mode', settings_json['display'])
    
    def test_reset_settings(self):
        """Test resetting settings to defaults"""
        # Modify settings
        self.settings_manager.settings.language = "fr"
        self.settings_manager.settings.display.theme = "dark"
        self.settings_manager.save_settings()
        
        # Reset settings
        self.settings_manager.reset_settings()
        
        # Verify settings are back to defaults
        self.assertEqual(self.settings_manager.settings.language, "en")
        self.assertEqual(self.settings_manager.settings.display.theme, "light")
        
        # Check if the file was updated
        new_manager = SettingsManager(self.settings_file)
        self.assertEqual(new_manager.settings.language, "en")
        self.assertEqual(new_manager.settings.display.theme, "light")
    
    def test_corrupt_settings_file(self):
        """Test handling of corrupt settings file"""
        # Create a corrupt settings file
        with open(self.settings_file, 'w') as f:
            f.write("This is not valid JSON")
        
        # Load settings from corrupt file
        corrupt_manager = SettingsManager(self.settings_file)
        
        # Should fall back to default settings
        self.assertEqual(corrupt_manager.settings.language, "en")
        self.assertEqual(corrupt_manager.settings.display.theme, "light")
    
    def test_partial_settings(self):
        """Test loading partial settings file (missing some fields)"""
        # Create a more complete but still partial settings file 
        # that includes all required nested structures
        partial_settings = {
            "language": "de",
            "display": {
                "display_mode": TimerDisplayMode.DIGITAL.value,
                "primary_screen_index": 0,
                "secondary_screen_index": None,
                "use_secondary_screen": False,
                "show_predicted_end_time": True,
                "theme": "dark"
            },
            "midweek_meeting": {
                "day": DayOfWeek.WEDNESDAY.value,
                "time": "19:00:00"
            },
            "weekend_meeting": {
                "day": DayOfWeek.SATURDAY.value,
                "time": "10:00:00"
            },
            "meeting_source": {
                "mode": MeetingSourceMode.WEB_SCRAPING.value,
                "auto_update_meetings": True,
                "save_scraped_as_template": False,
                "weekend_songs_manual": True
            },
            "recent_meetings": []
        }
        
        with open(self.settings_file, 'w') as f:
            json.dump(partial_settings, f)
        
        # Load partial settings
        partial_manager = SettingsManager(self.settings_file)
        
        # Check that specified settings were loaded
        self.assertEqual(partial_manager.settings.language, "de")
        self.assertEqual(partial_manager.settings.display.theme, "dark")
        
        # Check that structure is intact
        self.assertEqual(partial_manager.settings.midweek_meeting.day, DayOfWeek.WEDNESDAY)
        self.assertEqual(partial_manager.settings.weekend_meeting.day, DayOfWeek.SATURDAY)
    
    def test_recent_meetings_list(self):
        """Test the recent meetings list management"""
        # Add some meeting paths
        test_paths = [
            "/path/to/meeting1.json",
            "/path/to/meeting2.json",
            "/path/to/meeting3.json"
        ]
        
        self.settings_manager.settings.recent_meetings = test_paths.copy()
        self.settings_manager.save_settings()
        
        # Load settings and check list
        new_manager = SettingsManager(self.settings_file)
        self.assertEqual(new_manager.settings.recent_meetings, test_paths)
        
        # Test list limit (if implemented)
        many_paths = [f"/path/to/meeting{i}.json" for i in range(20)]
        self.settings_manager.settings.recent_meetings = many_paths
        self.settings_manager.save_settings()
        
        new_manager = SettingsManager(self.settings_file)
        # The list should be saved completely
        self.assertEqual(len(new_manager.settings.recent_meetings), len(many_paths))


if __name__ == '__main__':
    unittest.main()