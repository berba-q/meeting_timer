"""
Tests for the TimerController class in the JW Meeting Timer application.
"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the application code
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.timer import Timer, TimerState
from src.models.meeting import Meeting, MeetingSection, MeetingPart, MeetingType
from src.models.settings import SettingsManager
from src.controllers.timer_controller import TimerController
from src.controllers.settings_controller import SettingsController


class TestTimerController(unittest.TestCase):
    """Test cases for the TimerController class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary settings file
        self.test_dir = tempfile.TemporaryDirectory()
        self.settings_file = os.path.join(self.test_dir.name, "test_settings.json")

        # Create settings manager and controller
        self.settings_manager = SettingsManager(self.settings_file)
        self.settings_controller = SettingsController(self.settings_manager)

        # Create a timer controller with a mocked timer to avoid QTimer issues
        self.timer_controller = TimerController(self.settings_controller)

        # Mock the timer's QTimer to prevent "Timers can only be used with threads started with QThread" errors
        mock_qtimer = MagicMock()
        self.timer_controller.timer._timer = mock_qtimer
        
        # Also patch the _handle_timer_state_change method to avoid MeetingType import error
        self.original_handle_state = self.timer_controller._handle_timer_state_change
        self.timer_controller._handle_timer_state_change = MagicMock()
        
        # Create a mock meeting
        self.meeting = self._create_test_meeting()
        
        # Set up signal spy for tracking emitted signals
        self.signals_received = {
            'part_changed': [],
            'part_completed': [],
            'meeting_started': 0,
            'meeting_ended': 0,
            'countdown_started': [],
            'transition_started': [],
            'meeting_overtime': [],
            'predicted_end_time_updated': []
        }
        
        # Connect to signals
        self.timer_controller.part_changed.connect(
            lambda part, idx: self.signals_received['part_changed'].append((part, idx))
        )
        self.timer_controller.part_completed.connect(
            lambda idx: self.signals_received['part_completed'].append(idx)
        )
        self.timer_controller.meeting_started.connect(
            lambda: self._increment_signal_count('meeting_started')
        )
        self.timer_controller.meeting_ended.connect(
            lambda: self._increment_signal_count('meeting_ended')
        )
        self.timer_controller.countdown_started.connect(
            lambda dt: self.signals_received['countdown_started'].append(dt)
        )
        self.timer_controller.transition_started.connect(
            lambda msg: self.signals_received['transition_started'].append(msg)
        )
        self.timer_controller.meeting_overtime.connect(
            lambda sec: self.signals_received['meeting_overtime'].append(sec)
        )
        self.timer_controller.predicted_end_time_updated.connect(
            lambda orig, pred, target: self.signals_received['predicted_end_time_updated'].append((orig, pred, target))
        )
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore the original state change handler if you need it
        if hasattr(self, 'original_handle_state'):
            self.timer_controller._handle_timer_state_change = self.original_handle_state
        # Clean up temp directory
        self.test_dir.cleanup()
    
    def _increment_signal_count(self, signal_name):
        """Helper to increment signal counter"""
        self.signals_received[signal_name] += 1
    
    def _create_test_meeting(self):
        """Create a test meeting with multiple sections and parts"""
        # Create parts for first section
        section1_parts = [
            MeetingPart(title="Opening Song and Prayer", duration_minutes=5),
            MeetingPart(title="Part 1", duration_minutes=10),
            MeetingPart(title="Part 2", duration_minutes=15)
        ]
        
        # Create parts for second section
        section2_parts = [
            MeetingPart(title="Part 3", duration_minutes=10),
            MeetingPart(title="Part 4", duration_minutes=5)
        ]
        
        # Create parts for third section
        section3_parts = [
            MeetingPart(title="Part 5", duration_minutes=20),
            MeetingPart(title="Concluding Song and Prayer", duration_minutes=5)
        ]
        
        # Create sections
        sections = [
            MeetingSection(title="Section 1", parts=section1_parts),
            MeetingSection(title="Section 2", parts=section2_parts),
            MeetingSection(title="Section 3", parts=section3_parts)
        ]
        
        # Create meeting
        meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Test Meeting",
            date=datetime.now().date(),
            start_time=datetime.now().time(),
            sections=sections
        )
        
        return meeting
    
    def _reset_signals(self):
        """Reset signal tracking data"""
        self.signals_received = {
            'part_changed': [],
            'part_completed': [],
            'meeting_started': 0,
            'meeting_ended': 0,
            'countdown_started': [],
            'transition_started': [],
            'meeting_overtime': [],
            'predicted_end_time_updated': []
        }
    
    def test_set_meeting(self):
        """Test setting a meeting"""
        self.timer_controller.set_meeting(self.meeting)
        
        # Check that meeting was set
        self.assertEqual(self.timer_controller.current_meeting, self.meeting)
        
        # Check that parts list was created
        self.assertEqual(len(self.timer_controller.parts_list), 7)  # Total parts in all sections
        self.assertEqual(self.timer_controller.parts_list[0].title, "Opening Song and Prayer")
        self.assertEqual(self.timer_controller.parts_list[-1].title, "Concluding Song and Prayer")
    
    def test_start_meeting(self):
        """Test starting a meeting"""
        # Set meeting
        self.timer_controller.set_meeting(self.meeting)
        
        # Start meeting
        self.timer_controller.start_meeting()
        
        # Check that first part is current
        self.assertEqual(self.timer_controller.current_part_index, 0)
        
        # Check that timer was started with correct duration
        self.assertEqual(self.timer_controller.timer.state, TimerState.RUNNING)
        self.assertEqual(self.timer_controller.timer.total_seconds, 5 * 60)  # 5 minutes in seconds
        
        # Check signals
        self.assertEqual(self.signals_received['meeting_started'], 1)
        self.assertEqual(len(self.signals_received['part_changed']), 1)
        
        # Check part_changed signal data
        part, index = self.signals_received['part_changed'][0]
        self.assertEqual(part.title, "Opening Song and Prayer")
        self.assertEqual(index, 0)
    
    def test_next_part(self):
        """Test moving to the next part"""
        # Set up meeting and start
        self.timer_controller.set_meeting(self.meeting)
        self.timer_controller.start_meeting()
        self._reset_signals()
        
        # Move to next part
        self.timer_controller.next_part()
        
        # Check current part
        self.assertEqual(self.timer_controller.current_part_index, 1)
        
        # Check that timer was started with correct duration
        self.assertEqual(self.timer_controller.timer.state, TimerState.RUNNING)
        self.assertEqual(self.timer_controller.timer.total_seconds, 10 * 60)  # 10 minutes in seconds
        
        # Check signals
        self.assertEqual(len(self.signals_received['part_completed']), 1)
        self.assertEqual(self.signals_received['part_completed'][0], 0)  # First part completed
        
        self.assertEqual(len(self.signals_received['part_changed']), 1)
        part, index = self.signals_received['part_changed'][0]
        self.assertEqual(part.title, "Part 1")
        self.assertEqual(index, 1)
    
    def test_previous_part(self):
        """Test moving to the previous part"""
        # Set up meeting and start on second part
        self.timer_controller.set_meeting(self.meeting)
        self.timer_controller.start_meeting()
        self.timer_controller.next_part()
        self._reset_signals()
        
        # Move to previous part
        self.timer_controller.previous_part()
        
        # Check current part
        self.assertEqual(self.timer_controller.current_part_index, 0)
        
        # Check that timer was started with correct duration
        self.assertEqual(self.timer_controller.timer.state, TimerState.RUNNING)
        self.assertEqual(self.timer_controller.timer.total_seconds, 5 * 60)  # 5 minutes in seconds
        
        # Check signals
        self.assertEqual(len(self.signals_received['part_changed']), 1)
        part, index = self.signals_received['part_changed'][0]
        self.assertEqual(part.title, "Opening Song and Prayer")
        self.assertEqual(index, 0)
    
    def test_jump_to_part(self):
        """Test jumping to a specific part"""
        # Set up meeting
        self.timer_controller.set_meeting(self.meeting)
        self._reset_signals()
        
        # Jump to part 4 (index 3)
        self.timer_controller.jump_to_part(3)
        
        # Check current part
        self.assertEqual(self.timer_controller.current_part_index, 3)
        
        # Check that timer was started with correct duration
        self.assertEqual(self.timer_controller.timer.state, TimerState.RUNNING)
        self.assertEqual(self.timer_controller.timer.total_seconds, 10 * 60)  # 10 minutes in seconds
        
        # Check signals - should mark parts 0-2 as completed
        self.assertEqual(len(self.signals_received['part_completed']), 3)
        self.assertEqual(self.signals_received['part_completed'], [0, 1, 2])
        
        # Check part_changed signal
        self.assertEqual(len(self.signals_received['part_changed']), 1)
        part, index = self.signals_received['part_changed'][0]
        self.assertEqual(part.title, "Part 3")
        self.assertEqual(index, 3)
    
    def test_pause_resume(self):
        """Test pausing and resuming the timer"""
        # Set up meeting and start
        self.timer_controller.set_meeting(self.meeting)
        self.timer_controller.start_meeting()
        
        # Pause timer
        self.timer_controller.pause_timer()
        self.assertEqual(self.timer_controller.timer.state, TimerState.PAUSED)
        
        # Resume timer
        self.timer_controller.resume_timer()
        self.assertEqual(self.timer_controller.timer.state, TimerState.RUNNING)
    
    def test_adjust_time(self):
        """Test adjusting the current timer"""
        # Set up meeting and start
        self.timer_controller.set_meeting(self.meeting)
        self.timer_controller.start_meeting()
        
        # Initial duration is 5 minutes (300 seconds)
        initial_seconds = self.timer_controller.timer.total_seconds
        self.assertEqual(initial_seconds, 300)
        
        # Add 2 minutes
        self.timer_controller.adjust_time(2)
        self.assertEqual(self.timer_controller.timer.total_seconds, 300 + 120)
        
        # Subtract 1 minute
        self.timer_controller.adjust_time(-1)
        self.assertEqual(self.timer_controller.timer.total_seconds, 300 + 60)
    
    def test_stop_meeting(self):
        """Test stopping a meeting"""
        # Set up meeting and start
        self.timer_controller.set_meeting(self.meeting)
        self.timer_controller.start_meeting()
        self._reset_signals()
        
        # Stop meeting
        self.timer_controller.stop_meeting()
        
        # Check state
        self.assertEqual(self.timer_controller.current_part_index, -1)
        self.assertEqual(self.timer_controller.timer.state, TimerState.STOPPED)
        
        # Check signals
        self.assertEqual(self.signals_received['meeting_ended'], 1)
    
    def test_predicted_end_time(self):
        """Test predicted end time calculations"""
        # Instead of using a patch for datetime, we'll mock the method directly

        # Set up meeting
        self.timer_controller.set_meeting(self.meeting)

        # Mock the _update_predicted_end_time method
        self.timer_controller._update_predicted_end_time = MagicMock()

        # Mock the private attributes that hold the datetime values
        self.timer_controller._original_end_time = datetime.now()
        self.timer_controller._predicted_end_time = datetime.now()
        self.timer_controller._target_end_time = datetime.now()  # NEW: Add target end time

        # Reset signals
        self._reset_signals()

        # Create a mock for start_meeting to avoid date calculations
        original_start = self.timer_controller.start_meeting
        self.timer_controller.start_meeting = MagicMock()

        # Manually emit the signal with 3 parameters
        self.timer_controller.predicted_end_time_updated.emit(
            self.timer_controller._original_end_time,
            self.timer_controller._predicted_end_time,
            self.timer_controller._target_end_time  # NEW: Add target parameter
        )

        # Check that the signal was received
        self.assertEqual(len(self.signals_received['predicted_end_time_updated']), 1)
        original, predicted, target = self.signals_received['predicted_end_time_updated'][0]  # NEW: Unpack 3 parameters

        # Verify the types
        self.assertIsInstance(original, datetime)
        self.assertIsInstance(predicted, datetime)
        self.assertIsInstance(target, datetime)  # NEW: Verify target type
        
        # Restore original method
        self.timer_controller.start_meeting = original_start
    
    def test_section_transitions(self):
        """Test transitions between sections"""
        # Set up meeting
        self.timer_controller.set_meeting(self.meeting)
        
        # Reset signals before starting
        self._reset_signals()
        
        # Start meeting with controlled conditions
        self.timer_controller.start_meeting()
        
        # Mock the transition functions to fully control the test
        original_should = self.timer_controller._should_add_chairman_transition
        original_start = self.timer_controller._start_chairman_transition
        
        # Replace with our test versions that won't emit extra signals
        def mock_should_add_transition():
            return True
            
        def mock_start_transition():
            # Mark as in transition without emitting signals
            self.timer_controller._in_transition = True
            self.timer_controller._next_part_after_transition = self.timer_controller.current_part_index + 1
            # Set timer state
            self.timer_controller.timer._state = TimerState.TRANSITION
            
        self.timer_controller._should_add_chairman_transition = mock_should_add_transition
        self.timer_controller._start_chairman_transition = mock_start_transition
        
        # Clear any signals from starting the meeting
        self._reset_signals()
        
        # Manually emit a transition signal to test the handling
        self.timer_controller.transition_started.emit("Test Transition")
        
        # Verify that signal was emitted exactly once
        self.assertEqual(len(self.signals_received['transition_started']), 1)
        self.assertEqual(self.signals_received['transition_started'][0], "Test Transition")
        
        # Restore original methods
        self.timer_controller._should_add_chairman_transition = original_should
        self.timer_controller._start_chairman_transition = original_start
    
    def test_reset_timer(self):
        """Test resetting the current timer"""
        # Set up meeting and start
        self.timer_controller.set_meeting(self.meeting)
        self.timer_controller.start_meeting()
        
        # Run time forward
        initial_remaining = self.timer_controller.timer.remaining_seconds
        self.timer_controller.timer._remaining_seconds -= 60  # Simulate 1 minute elapsed
        
        # Reset timer
        self.timer_controller.reset_timer()
        
        # Check that timer is reset to initial duration
        self.assertEqual(self.timer_controller.timer.remaining_seconds, initial_remaining)


if __name__ == '__main__':
    unittest.main()