"""
Tests for the Timer model class in the JW Meeting Timer application.
"""
import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the application code
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.timer import Timer, TimerState, TimerDisplayMode


class TestTimer(unittest.TestCase):
    """Test cases for the Timer class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a timer instance
        self.timer = Timer()
        
        # Replace QTimer with a mock to avoid thread issues
        self.timer._timer = MagicMock()
        
        # Track emitted signals
        self.time_updated_signals = []
        self.state_changed_signals = []
        
        # Connect to signals
        self.timer.time_updated.connect(
            lambda seconds: self.time_updated_signals.append(seconds)
        )
        self.timer.state_changed.connect(
            lambda state: self.state_changed_signals.append(state)
        )
    
    def _reset_signals(self):
        """Reset signal tracking"""
        self.time_updated_signals = []
        self.state_changed_signals = []
    
    def test_initial_state(self):
        """Test initial timer state"""
        # Check initial properties
        self.assertEqual(self.timer.state, TimerState.STOPPED)
        self.assertEqual(self.timer.remaining_seconds, 0)
        self.assertEqual(self.timer.total_seconds, 0)
        self.assertEqual(self.timer.elapsed_seconds, 0)
        self.assertEqual(self.timer.progress_percentage, 0)
    
    def test_start_timer(self):
        """Test starting the timer"""
        # Start timer with 5 minutes
        duration = 5 * 60  # 5 minutes in seconds
        self.timer.start(duration)
        
        # Check timer state
        self.assertEqual(self.timer.state, TimerState.RUNNING)
        self.assertEqual(self.timer.total_seconds, duration)
        self.assertEqual(self.timer.remaining_seconds, duration)
        
        # Check signals
        self.assertEqual(len(self.state_changed_signals), 1)
        self.assertEqual(self.state_changed_signals[0], TimerState.RUNNING)
        
        self.assertEqual(len(self.time_updated_signals), 1)
        self.assertEqual(self.time_updated_signals[0], duration)
    
    def test_pause_resume(self):
        """Test pausing and resuming the timer"""
        # Start timer
        self.timer.start(60)  # 1 minute
        self._reset_signals()
        
        # Pause timer
        self.timer.pause()
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.PAUSED)
        
        # Check signals
        self.assertEqual(len(self.state_changed_signals), 1)
        self.assertEqual(self.state_changed_signals[0], TimerState.PAUSED)
        
        self._reset_signals()
        
        # Resume timer
        self.timer.resume()
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.RUNNING)
        
        # Check signals
        self.assertEqual(len(self.state_changed_signals), 1)
        self.assertEqual(self.state_changed_signals[0], TimerState.RUNNING)
    
    def test_stop(self):
        """Test stopping the timer"""
        # Start timer
        self.timer.start(60)
        self._reset_signals()
        
        # Stop timer
        self.timer.stop()
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.STOPPED)
        self.assertEqual(self.timer.remaining_seconds, 0)
        
        # Check signals
        self.assertEqual(len(self.state_changed_signals), 1)
        self.assertEqual(self.state_changed_signals[0], TimerState.STOPPED)
        
        self.assertEqual(len(self.time_updated_signals), 1)
        self.assertEqual(self.time_updated_signals[0], 0)
    
    def test_reset(self):
        """Test resetting the timer"""
        # Start timer
        duration = 60
        self.timer.start(duration)
        
        # Simulate time passing
        self.timer._remaining_seconds = 30
        self._reset_signals()
        
        # Reset timer
        self.timer.reset()
        
        # Check state
        self.assertEqual(self.timer.remaining_seconds, duration)
        
        # Check signals
        self.assertEqual(len(self.time_updated_signals), 1)
        self.assertEqual(self.time_updated_signals[0], duration)
    
    def test_adjust_time(self):
        """Test adjusting the timer duration"""
        # Start timer with 5 minutes
        self.timer.start(5 * 60)
        self._reset_signals()
        
        # Add 1 minute
        self.timer.adjust_time(60)
        
        # Check new duration
        self.assertEqual(self.timer.total_seconds, 6 * 60)
        
        # Remove 2 minutes
        self.timer.adjust_time(-120)
        
        # Check new duration
        self.assertEqual(self.timer.total_seconds, 4 * 60)
        
        # Check signals
        self.assertEqual(len(self.time_updated_signals), 2)
    
    def test_set_remaining_time(self):
        """Test directly setting the remaining time"""
        # Start timer with 5 minutes
        self.timer.start(5 * 60)
        self._reset_signals()
        
        # Set remaining time to 2 minutes
        self.timer.set_remaining_time(2 * 60)
        
        # Check remaining time
        self.assertEqual(self.timer.remaining_seconds, 2 * 60)
        
        # Check signals
        self.assertEqual(len(self.time_updated_signals), 1)
        self.assertEqual(self.time_updated_signals[0], 2 * 60)
    
    def test_overtime(self):
        """Test timer going into overtime"""
        # Start timer with 1 second
        self.timer.start(1)
        self._reset_signals()
        
        # Set remaining time to 0 to trigger overtime
        self.timer.set_remaining_time(0)
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.OVERTIME)
        
        # Check signals
        self.assertEqual(len(self.state_changed_signals), 1)
        self.assertEqual(self.state_changed_signals[0], TimerState.OVERTIME)
    
    @patch('src.models.timer.time.time')
    def test_update_timer_running(self, mock_time):
        """Test the _update_timer method when running"""
        # Configure mock time
        start_time = 1000.0
        mock_time.side_effect = [start_time, start_time + 10]  # 10 seconds elapsed
        
        # Start timer with 30 seconds
        self.timer.start(30)
        self._reset_signals()
        
        # Manually call update (normally called by QTimer)
        self.timer._update_timer()
        
        # Check remaining time (should be 20 seconds now)
        self.assertEqual(self.timer.remaining_seconds, 20)
        
        # Check signals
        self.assertEqual(len(self.time_updated_signals), 1)
        self.assertEqual(self.time_updated_signals[0], 20)
    
    @patch('src.models.timer.time.time')
    def test_update_timer_overtime(self, mock_time):
        """Test the _update_timer method in overtime"""
        # Configure mock time
        start_time = 1000.0
        current_time = start_time + 40  # 10 seconds into overtime
        mock_time.side_effect = [start_time, current_time]
        
        # Start timer with 30 seconds
        self.timer.start(30)
        
        # Set state to overtime and reset signals
        self.timer._state = TimerState.OVERTIME
        self._reset_signals()
        
        # Manually call update
        self.timer._update_timer()
        
        # Check remaining time (should be -10 seconds in overtime)
        self.assertEqual(self.timer.remaining_seconds, -10)
        
        # Check signals
        self.assertEqual(len(self.time_updated_signals), 1)
        self.assertEqual(self.time_updated_signals[0], -10)
    
    @patch('src.models.timer.datetime')
    def test_start_countdown(self, mock_datetime):
        """Test countdown to a specific date/time"""
        # Configure mock datetime
        now = datetime(2023, 1, 1, 12, 0, 0)  # Noon
        target = datetime(2023, 1, 1, 12, 5, 0)  # 5 minutes later
        
        mock_datetime.now.return_value = now
        
        # Start countdown
        self.timer.start_countdown(target)
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.COUNTDOWN)
        self.assertEqual(self.timer.total_seconds, 5 * 60)  # 5 minutes
        
        # Check signals
        self.assertEqual(len(self.state_changed_signals), 1)
        self.assertEqual(self.state_changed_signals[0], TimerState.COUNTDOWN)
        
        self.assertEqual(len(self.time_updated_signals), 1)
        self.assertEqual(self.time_updated_signals[0], 5 * 60)
    
    @patch('src.models.timer.datetime')
    @patch('src.models.timer.time.time')
    def test_update_countdown(self, mock_time, mock_datetime):
        """Test updating the countdown timer"""
        # Configure mocks
        now = datetime(2023, 1, 1, 12, 0, 0)  # Noon
        target = datetime(2023, 1, 1, 12, 5, 0)  # 5 minutes later
        
        mock_datetime.now.return_value = now
        
        start_time = 1000.0
        current_time = start_time + 60  # 1 minute elapsed
        mock_time.side_effect = [start_time, current_time]
        
        # Start countdown
        self.timer.start_countdown(target)
        self._reset_signals()
        
        # Update timer
        self.timer._update_timer()
        
        # Check remaining time (should be 4 minutes now)
        self.assertEqual(self.timer.remaining_seconds, 4 * 60)
        
        # Check signals
        self.assertEqual(len(self.time_updated_signals), 1)
        self.assertEqual(self.time_updated_signals[0], 4 * 60)
    
    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        # Start timer with 100 seconds
        self.timer.start(100)
        
        # Initial progress should be 0%
        self.assertEqual(self.timer.progress_percentage, 0)
        
        # Simulate 25 seconds elapsed
        self.timer._remaining_seconds = 75
        
        # Progress should be 25%
        self.assertEqual(self.timer.progress_percentage, 25)
        
        # Simulate 50 seconds elapsed
        self.timer._remaining_seconds = 50
        
        # Progress should be 50%
        self.assertEqual(self.timer.progress_percentage, 50)
        
        # Simulate complete
        self.timer._remaining_seconds = 0
        
        # Progress should be 100%
        self.assertEqual(self.timer.progress_percentage, 100)
    
    def test_zero_duration_timer(self):
        """Test timer with zero duration"""
        # Start timer with 0 seconds
        self.timer.start(0)
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.RUNNING)
        self.assertEqual(self.timer.total_seconds, 0)
        self.assertEqual(self.timer.remaining_seconds, 0)
        
        # Update should switch to overtime immediately
        self.timer._update_timer()
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.OVERTIME)


if __name__ == '__main__':
    unittest.main()