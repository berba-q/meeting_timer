"""
Tests for target duration feature in the JW Meeting Timer application.

Tests cover:
- Target duration in MeetingSettings (global settings)
- Target duration in Meeting model (per-meeting overrides)
- Target end time calculation in TimerController
- Signal emission with target end time parameter
- Mid-meeting setting changes
- Backwards compatibility
- Web-scraped meetings
- Custom meetings
- CO visit meetings
"""
import os
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, time, timedelta

# Add the parent directory to the path so we can import the application code
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.settings import (
    SettingsManager, AppSettings, MeetingSettings, DayOfWeek
)
from src.models.meeting import Meeting, MeetingSection, MeetingPart, MeetingType
from src.controllers.timer_controller import TimerController
from src.controllers.settings_controller import SettingsController


class TestTargetDurationSettings(unittest.TestCase):
    """Test target duration in settings model"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_file = os.path.join(self.test_dir.name, "test_settings.json")
        self.settings_manager = SettingsManager(self.settings_file)

    def tearDown(self):
        """Clean up after tests"""
        self.test_dir.cleanup()

    def test_default_target_duration(self):
        """Test that default target duration is 105 minutes for both meetings"""
        settings = self.settings_manager.settings

        # Both midweek and weekend should default to 105 minutes
        self.assertEqual(settings.midweek_meeting.target_duration_minutes, 105)
        self.assertEqual(settings.weekend_meeting.target_duration_minutes, 105)

    def test_save_and_load_target_duration(self):
        """Test saving and loading target duration settings"""
        # Set custom target durations
        self.settings_manager.settings.midweek_meeting.target_duration_minutes = 110
        self.settings_manager.settings.weekend_meeting.target_duration_minutes = 100

        # Save settings
        self.settings_manager.save_settings()

        # Load settings in a new manager
        new_manager = SettingsManager(self.settings_file)

        # Verify target durations were saved and loaded
        self.assertEqual(new_manager.settings.midweek_meeting.target_duration_minutes, 110)
        self.assertEqual(new_manager.settings.weekend_meeting.target_duration_minutes, 100)

    def test_backwards_compatibility_missing_target_duration(self):
        """Test backwards compatibility when target_duration_minutes is missing from settings file"""
        # Create settings file without target_duration_minutes
        old_settings = {
            "language": "en",
            "midweek_meeting": {
                "day": DayOfWeek.WEDNESDAY.value,
                "time": "19:00:00"
                # No target_duration_minutes
            },
            "weekend_meeting": {
                "day": DayOfWeek.SATURDAY.value,
                "time": "10:00:00"
                # No target_duration_minutes
            },
            "display": {
                "display_mode": 0,
                "primary_screen_index": 0,
                "secondary_screen_index": None,
                "use_secondary_screen": False,
                "show_predicted_end_time": True,
                "theme": "system"
            },
            "meeting_source": {
                "mode": 0,
                "auto_update_meetings": True,
                "save_scraped_as_template": False,
                "weekend_songs_manual": True
            },
            "recent_meetings": [],
            "network_display": {
                "mode": 0,
                "http_port": 8080,
                "ws_port": 8765,
                "auto_start": False,
                "qr_code_enabled": True
            },
            "co_visit": {
                "enabled": False,
                "week_start_date": None
            },
            "start_reminder_enabled": True,
            "start_reminder_delay": 2,
            "overrun_enabled": True,
            "overrun_delay": 20
        }

        with open(self.settings_file, 'w') as f:
            json.dump(old_settings, f)

        # Load settings from old file
        manager = SettingsManager(self.settings_file)

        # Should default to 105 minutes for both
        self.assertEqual(manager.settings.midweek_meeting.target_duration_minutes, 105)
        self.assertEqual(manager.settings.weekend_meeting.target_duration_minutes, 105)

    def test_meeting_settings_serialization_includes_target_duration(self):
        """Test that MeetingSettings serialization includes target_duration_minutes"""
        meeting_settings = MeetingSettings(
            day=DayOfWeek.WEDNESDAY,
            time=time(19, 0),
            target_duration_minutes=110
        )

        # Convert to dict
        settings_dict = meeting_settings.to_dict()

        # Verify target_duration_minutes is included
        self.assertIn('target_duration_minutes', settings_dict)
        self.assertEqual(settings_dict['target_duration_minutes'], 110)

        # Convert back from dict
        restored_settings = MeetingSettings.from_dict(settings_dict)
        self.assertEqual(restored_settings.target_duration_minutes, 110)


class TestTargetDurationMeetingModel(unittest.TestCase):
    """Test target duration in Meeting model"""

    def test_meeting_with_no_target_duration(self):
        """Test that regular meetings have None as target_duration_minutes"""
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Regular Midweek Meeting",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[],
            language="en"
            # No target_duration_minutes specified
        )

        # Should be None (uses global settings)
        self.assertIsNone(meeting.target_duration_minutes)

    def test_custom_meeting_with_target_duration(self):
        """Test that custom meetings can have their own target_duration_minutes"""
        meeting = Meeting(
            meeting_type=MeetingType.CUSTOM,
            title="Memorial",
            date=datetime.now().date(),
            start_time=time(20, 0),
            sections=[],
            language="en",
            target_duration_minutes=60  # 1 hour memorial
        )

        # Should have custom target
        self.assertEqual(meeting.target_duration_minutes, 60)

    def test_meeting_serialization_with_target_duration(self):
        """Test meeting serialization includes target_duration_minutes"""
        meeting = Meeting(
            meeting_type=MeetingType.CUSTOM,
            title="Circuit Assembly",
            date=datetime.now().date(),
            start_time=time(9, 0),
            sections=[],
            language="en",
            target_duration_minutes=480  # 8 hours
        )

        # Convert to dict
        meeting_dict = meeting.to_dict()

        # Verify target_duration_minutes is included
        self.assertIn('target_duration_minutes', meeting_dict)
        self.assertEqual(meeting_dict['target_duration_minutes'], 480)

        # Convert back from dict
        restored_meeting = Meeting.from_dict(meeting_dict)
        self.assertEqual(restored_meeting.target_duration_minutes, 480)

    def test_meeting_serialization_without_target_duration(self):
        """Test meeting serialization when target_duration_minutes is None"""
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Regular Meeting",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[]
        )

        # Convert to dict
        meeting_dict = meeting.to_dict()

        # Verify target_duration_minutes is included (as None)
        self.assertIn('target_duration_minutes', meeting_dict)
        self.assertIsNone(meeting_dict['target_duration_minutes'])

        # Convert back from dict
        restored_meeting = Meeting.from_dict(meeting_dict)
        self.assertIsNone(restored_meeting.target_duration_minutes)

    def test_backwards_compatibility_meeting_without_target_duration(self):
        """Test loading old meeting files without target_duration_minutes"""
        # Old meeting dict without target_duration_minutes
        old_meeting_dict = {
            'meeting_type': 'midweek',
            'title': 'Old Meeting',
            'date': datetime.now().date().isoformat(),
            'start_time': '19:00:00',
            'sections': [],
            'language': 'en'
            # No target_duration_minutes
        }

        # Should load without error and default to None
        meeting = Meeting.from_dict(old_meeting_dict)
        self.assertIsNone(meeting.target_duration_minutes)


class TestTargetEndTimeCalculation(unittest.TestCase):
    """Test target end time calculation in TimerController"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary settings file
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_file = os.path.join(self.test_dir.name, "test_settings.json")

        # Create settings manager and controller
        self.settings_manager = SettingsManager(self.settings_file)
        self.settings_controller = SettingsController(self.settings_manager)

        # Create a timer controller with mocked timer
        self.timer_controller = TimerController(self.settings_controller)

        # Mock the timer's QTimer to prevent Qt errors
        mock_qtimer = MagicMock()
        self.timer_controller.timer._timer = mock_qtimer

        # Mock the _handle_timer_state_change method
        self.timer_controller._handle_timer_state_change = MagicMock()

        # Track signals
        self.signals_received = {
            'predicted_end_time_updated': []
        }

        # Connect to signal
        self.timer_controller.predicted_end_time_updated.connect(
            lambda orig, pred, target: self.signals_received['predicted_end_time_updated'].append(
                (orig, pred, target)
            )
        )

    def tearDown(self):
        """Clean up after tests"""
        self.test_dir.cleanup()

    def test_midweek_meeting_uses_midweek_target_duration(self):
        """Test that midweek meeting uses midweek target duration from settings"""
        # Create midweek meeting without custom target
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Midweek Meeting",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[
                MeetingSection(
                    title="Section 1",
                    parts=[
                        MeetingPart(title="Part 1", duration_minutes=30)
                    ]
                )
            ],
            target_duration_minutes=None  # Uses global settings
        )

        # Set meeting
        self.timer_controller.set_meeting(meeting)

        # Set meeting start time
        start_datetime = datetime.combine(datetime.now().date(), time(19, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target end time
        self.timer_controller._calculate_target_end_time()

        # Target should be start time + 105 minutes (default midweek target)
        expected_target = start_datetime + timedelta(minutes=105)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)

    def test_weekend_meeting_uses_weekend_target_duration(self):
        """Test that weekend meeting uses weekend target duration from settings"""
        # Create weekend meeting without custom target
        meeting = Meeting(
            meeting_type=MeetingType.WEEKEND,
            title="Weekend Meeting",
            date=datetime.now().date(),
            start_time=time(10, 0),
            sections=[
                MeetingSection(
                    title="Section 1",
                    parts=[
                        MeetingPart(title="Public Talk", duration_minutes=30),
                        MeetingPart(title="Watchtower", duration_minutes=60)
                    ]
                )
            ],
            target_duration_minutes=None  # Uses global settings
        )

        # Set meeting
        self.timer_controller.set_meeting(meeting)

        # Set meeting start time
        start_datetime = datetime.combine(datetime.now().date(), time(10, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target end time
        self.timer_controller._calculate_target_end_time()

        # Target should be start time + 105 minutes (default weekend target)
        expected_target = start_datetime + timedelta(minutes=105)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)

    def test_custom_meeting_uses_meeting_specific_target_duration(self):
        """Test that custom meeting uses its own target_duration_minutes"""
        # Create custom meeting with specific target
        meeting = Meeting(
            meeting_type=MeetingType.CUSTOM,
            title="Memorial",
            date=datetime.now().date(),
            start_time=time(20, 0),
            sections=[
                MeetingSection(
                    title="Memorial",
                    parts=[
                        MeetingPart(title="Talk", duration_minutes=45),
                        MeetingPart(title="Emblems", duration_minutes=10)
                    ]
                )
            ],
            target_duration_minutes=60  # Custom 60-minute target
        )

        # Set meeting
        self.timer_controller.set_meeting(meeting)

        # Set meeting start time
        start_datetime = datetime.combine(datetime.now().date(), time(20, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target end time
        self.timer_controller._calculate_target_end_time()

        # Target should be start time + 60 minutes (custom target)
        expected_target = start_datetime + timedelta(minutes=60)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)

    def test_signal_emission_includes_target_end_time(self):
        """Test that predicted_end_time_updated signal includes target_end_time parameter"""
        # Create meeting
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Test Meeting",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[
                MeetingSection(
                    title="Section 1",
                    parts=[
                        MeetingPart(title="Part 1", duration_minutes=30)
                    ]
                )
            ]
        )

        # Set and start meeting
        self.timer_controller.set_meeting(meeting)
        self.timer_controller.start_meeting()

        # Check that signal was emitted with 3 parameters
        self.assertGreater(len(self.signals_received['predicted_end_time_updated']), 0)

        # Get the last emitted signal
        original, predicted, target = self.signals_received['predicted_end_time_updated'][-1]

        # All three should be datetime objects
        self.assertIsInstance(original, datetime)
        self.assertIsInstance(predicted, datetime)
        self.assertIsInstance(target, datetime)

        # Target should be approximately start_time + 105 minutes
        # (allowing some flexibility for test execution time)
        start_time = self.timer_controller._meeting_start_time
        expected_target = start_time + timedelta(minutes=105)

        # Check they're within 5 seconds of each other (account for test execution time)
        time_diff = abs((target - expected_target).total_seconds())
        self.assertLess(time_diff, 5)


class TestMidMeetingSettingChanges(unittest.TestCase):
    """Test handling of setting changes during active meeting"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_file = os.path.join(self.test_dir.name, "test_settings.json")

        # Create settings manager and controller
        self.settings_manager = SettingsManager(self.settings_file)
        self.settings_controller = SettingsController(self.settings_manager)

        # Create timer controller
        self.timer_controller = TimerController(self.settings_controller)

        # Mock the timer's QTimer
        mock_qtimer = MagicMock()
        self.timer_controller.timer._timer = mock_qtimer

        # Mock state change handler
        self.timer_controller._handle_timer_state_change = MagicMock()

        # Track target end time updates
        self.target_end_times = []
        self.timer_controller.predicted_end_time_updated.connect(
            lambda orig, pred, target: self.target_end_times.append(target)
        )

    def tearDown(self):
        """Clean up after tests"""
        self.test_dir.cleanup()

    def test_target_end_time_recalculates_on_setting_change(self):
        """Test that target end time recalculates when settings change during meeting"""
        # Create and start a meeting
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Test Meeting",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[
                MeetingSection(
                    title="Section 1",
                    parts=[
                        MeetingPart(title="Part 1", duration_minutes=30)
                    ]
                )
            ]
        )

        self.timer_controller.set_meeting(meeting)
        self.timer_controller.start_meeting()

        # Get initial target end time
        initial_target = self.timer_controller._target_end_time
        self.assertIsNotNone(initial_target)

        # Simulate settings change (increase target duration from 105 to 110)
        self.settings_controller.settings_manager.settings.midweek_meeting.target_duration_minutes = 110
        self.settings_controller.settings_manager.save_settings()

        # Trigger the settings update handler (this would normally be triggered by settings_changed signal)
        self.timer_controller._on_settings_updated()

        # Target end time should have been recalculated
        new_target = self.timer_controller._target_end_time

        # New target should be 5 minutes later than initial
        expected_difference = timedelta(minutes=5)
        actual_difference = new_target - initial_target

        self.assertEqual(actual_difference, expected_difference)


class TestWebScrapedMeetings(unittest.TestCase):
    """Test web-scraped meetings use global target duration settings"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary settings file
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_file = os.path.join(self.test_dir.name, "test_settings.json")

        # Create settings manager and controller
        self.settings_manager = SettingsManager(self.settings_file)
        self.settings_controller = SettingsController(self.settings_manager)

        # Create timer controller
        self.timer_controller = TimerController(self.settings_controller)

        # Mock the timer's QTimer
        mock_qtimer = MagicMock()
        self.timer_controller.timer._timer = mock_qtimer

        # Mock state change handler
        self.timer_controller._handle_timer_state_change = MagicMock()

    def tearDown(self):
        """Clean up after tests"""
        self.test_dir.cleanup()

    def test_scraped_midweek_meeting_uses_midweek_target(self):
        """Test that scraped midweek meeting uses midweek target duration"""
        # Create a meeting that would be scraped from web (no custom target)
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Life and Ministry Meeting",  # Typical JW.org title
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[
                MeetingSection(
                    title="Treasures From God's Word",
                    parts=[
                        MeetingPart(title="Opening Song and Prayer", duration_minutes=4),
                        MeetingPart(title="Treasures from God's Word", duration_minutes=10)
                    ]
                )
            ],
            target_duration_minutes=None  # Scraped meetings don't set custom target
        )

        # Set meeting and start
        self.timer_controller.set_meeting(meeting)
        start_datetime = datetime.combine(datetime.now().date(), time(19, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target
        self.timer_controller._calculate_target_end_time()

        # Should use midweek target (105 min)
        expected_target = start_datetime + timedelta(minutes=105)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)

    def test_scraped_weekend_meeting_uses_weekend_target(self):
        """Test that scraped weekend meeting uses weekend target duration"""
        # Create a meeting that would be scraped from web
        meeting = Meeting(
            meeting_type=MeetingType.WEEKEND,
            title="Public Meeting and Watchtower Study",  # Typical JW.org title
            date=datetime.now().date(),
            start_time=time(10, 0),
            sections=[
                MeetingSection(
                    title="Public Meeting",
                    parts=[
                        MeetingPart(title="Opening Song and Prayer", duration_minutes=5),
                        MeetingPart(title="Public Talk", duration_minutes=30)
                    ]
                ),
                MeetingSection(
                    title="Watchtower Study",
                    parts=[
                        MeetingPart(title="Middle Song", duration_minutes=5),
                        MeetingPart(title="Watchtower Study", duration_minutes=60)
                    ]
                )
            ],
            target_duration_minutes=None  # Scraped meetings don't set custom target
        )

        # Set meeting and start
        self.timer_controller.set_meeting(meeting)
        start_datetime = datetime.combine(datetime.now().date(), time(10, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target
        self.timer_controller._calculate_target_end_time()

        # Should use weekend target (105 min)
        expected_target = start_datetime + timedelta(minutes=105)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)


class TestCOVisitMeetings(unittest.TestCase):
    """Test Circuit Overseer visit meetings use global target duration settings"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary settings file
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_file = os.path.join(self.test_dir.name, "test_settings.json")

        # Create settings manager and controller
        self.settings_manager = SettingsManager(self.settings_file)
        self.settings_controller = SettingsController(self.settings_manager)

        # Create timer controller
        self.timer_controller = TimerController(self.settings_controller)

        # Mock the timer's QTimer
        mock_qtimer = MagicMock()
        self.timer_controller.timer._timer = mock_qtimer

        # Mock state change handler
        self.timer_controller._handle_timer_state_change = MagicMock()

    def tearDown(self):
        """Clean up after tests"""
        self.test_dir.cleanup()

    def test_co_visit_midweek_uses_midweek_target(self):
        """Test that CO visit midweek meeting uses midweek target duration"""
        # CO visit meetings are just regular meetings with CO as speaker
        # They should still be marked as MIDWEEK type
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Life and Ministry Meeting with Circuit Overseer",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[
                MeetingSection(
                    title="Section 1",
                    parts=[
                        MeetingPart(title="Opening Song", duration_minutes=4),
                        MeetingPart(title="CO Talk", duration_minutes=30)
                    ]
                )
            ],
            target_duration_minutes=None  # Uses global midweek settings
        )

        # Set meeting and start
        self.timer_controller.set_meeting(meeting)
        start_datetime = datetime.combine(datetime.now().date(), time(19, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target
        self.timer_controller._calculate_target_end_time()

        # Should use midweek target (105 min)
        expected_target = start_datetime + timedelta(minutes=105)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)

    def test_co_visit_weekend_uses_weekend_target(self):
        """Test that CO visit weekend meeting uses weekend target duration"""
        # CO visit weekend meeting
        meeting = Meeting(
            meeting_type=MeetingType.WEEKEND,
            title="Public Meeting with Circuit Overseer",
            date=datetime.now().date(),
            start_time=time(10, 0),
            sections=[
                MeetingSection(
                    title="Section 1",
                    parts=[
                        MeetingPart(title="Opening Song", duration_minutes=5),
                        MeetingPart(title="CO Public Talk", duration_minutes=30),
                        MeetingPart(title="Watchtower Study", duration_minutes=60)
                    ]
                )
            ],
            target_duration_minutes=None  # Uses global weekend settings
        )

        # Set meeting and start
        self.timer_controller.set_meeting(meeting)
        start_datetime = datetime.combine(datetime.now().date(), time(10, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target
        self.timer_controller._calculate_target_end_time()

        # Should use weekend target (105 min)
        expected_target = start_datetime + timedelta(minutes=105)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)


class TestCustomMeetingVariety(unittest.TestCase):
    """Test custom meetings with various target durations"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary settings file
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_file = os.path.join(self.test_dir.name, "test_settings.json")

        # Create settings manager and controller
        self.settings_manager = SettingsManager(self.settings_file)
        self.settings_controller = SettingsController(self.settings_manager)

        # Create timer controller
        self.timer_controller = TimerController(self.settings_controller)

        # Mock the timer's QTimer
        mock_qtimer = MagicMock()
        self.timer_controller.timer._timer = mock_qtimer

        # Mock state change handler
        self.timer_controller._handle_timer_state_change = MagicMock()

    def tearDown(self):
        """Clean up after tests"""
        self.test_dir.cleanup()

    def test_short_custom_meeting_memorial(self):
        """Test short custom meeting (Memorial - 60 minutes)"""
        meeting = Meeting(
            meeting_type=MeetingType.CUSTOM,
            title="Memorial",
            date=datetime.now().date(),
            start_time=time(20, 0),
            sections=[
                MeetingSection(
                    title="Memorial Program",
                    parts=[
                        MeetingPart(title="Opening Song", duration_minutes=5),
                        MeetingPart(title="Memorial Talk", duration_minutes=45),
                        MeetingPart(title="Pass Emblems", duration_minutes=10)
                    ]
                )
            ],
            target_duration_minutes=60  # 1 hour
        )

        # Set meeting and start
        self.timer_controller.set_meeting(meeting)
        start_datetime = datetime.combine(datetime.now().date(), time(20, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target
        self.timer_controller._calculate_target_end_time()

        # Should use custom target (60 min)
        expected_target = start_datetime + timedelta(minutes=60)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)

    def test_long_custom_meeting_assembly(self):
        """Test long custom meeting (Circuit Assembly - 8 hours)"""
        meeting = Meeting(
            meeting_type=MeetingType.CUSTOM,
            title="Circuit Assembly",
            date=datetime.now().date(),
            start_time=time(9, 0),
            sections=[
                MeetingSection(
                    title="Morning Session",
                    parts=[
                        MeetingPart(title="Opening Program", duration_minutes=30),
                        MeetingPart(title="Morning Talks", duration_minutes=120)
                    ]
                ),
                MeetingSection(
                    title="Afternoon Session",
                    parts=[
                        MeetingPart(title="Afternoon Talks", duration_minutes=150),
                        MeetingPart(title="Concluding Program", duration_minutes=30)
                    ]
                )
            ],
            target_duration_minutes=480  # 8 hours
        )

        # Set meeting and start
        self.timer_controller.set_meeting(meeting)
        start_datetime = datetime.combine(datetime.now().date(), time(9, 0))
        self.timer_controller._meeting_start_time = start_datetime

        # Calculate target
        self.timer_controller._calculate_target_end_time()

        # Should use custom target (480 min = 8 hours)
        expected_target = start_datetime + timedelta(minutes=480)
        self.assertEqual(self.timer_controller._target_end_time, expected_target)

        # Verify target time is 5:00 PM (9:00 AM + 8 hours)
        self.assertEqual(expected_target.hour, 17)
        self.assertEqual(expected_target.minute, 0)

    def test_custom_meeting_does_not_affect_global_settings(self):
        """Test that custom meeting target doesn't affect global midweek/weekend settings"""
        # Create custom meeting with 90-minute target
        custom_meeting = Meeting(
            meeting_type=MeetingType.CUSTOM,
            title="Special Event",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[
                MeetingSection(
                    title="Event",
                    parts=[
                        MeetingPart(title="Program", duration_minutes=90)
                    ]
                )
            ],
            target_duration_minutes=90
        )

        # Set and calculate target for custom meeting
        self.timer_controller.set_meeting(custom_meeting)
        start_datetime = datetime.combine(datetime.now().date(), time(19, 0))
        self.timer_controller._meeting_start_time = start_datetime
        self.timer_controller._calculate_target_end_time()

        # Custom meeting should use 90 minutes
        expected_custom_target = start_datetime + timedelta(minutes=90)
        self.assertEqual(self.timer_controller._target_end_time, expected_custom_target)

        # Now create a regular midweek meeting
        midweek_meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Regular Midweek",
            date=datetime.now().date(),
            start_time=time(19, 0),
            sections=[
                MeetingSection(
                    title="Section",
                    parts=[
                        MeetingPart(title="Part", duration_minutes=30)
                    ]
                )
            ],
            target_duration_minutes=None  # Uses global settings
        )

        # Set and calculate target for midweek meeting
        self.timer_controller.set_meeting(midweek_meeting)
        self.timer_controller._meeting_start_time = start_datetime
        self.timer_controller._calculate_target_end_time()

        # Midweek meeting should still use 105 minutes (global setting)
        expected_midweek_target = start_datetime + timedelta(minutes=105)
        self.assertEqual(self.timer_controller._target_end_time, expected_midweek_target)


if __name__ == '__main__':
    unittest.main()
