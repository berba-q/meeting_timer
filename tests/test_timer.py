"""
Unit tests for Timer class in the JW Meeting Timer application.
"""
import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import sys

# Add the parent directory to the path so we can import the application code
sys.path.insert(0, '.')

# Set up Qt environment before importing Timer
import os
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = "/Users/griffithsobli-laryea/Documents/meeting_timer/.venv/lib/python3.11/site-packages/PyQt6/Qt6/plugins/platforms"
os.environ['QT_QPA_PLATFORM'] = "cocoa"  # Use offscreen for testing
try:
    import PyQt6
    qt_plugin_path = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins', 'platforms')
    if os.path.exists(qt_plugin_path):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path
except ImportError:
    print("PyQt6 not found")

from src.models.timer import Timer, TimerState, TimerDisplayMode
from PyQt6.QtCore import QCoreApplication, QTimer
from PyQt6.QtWidgets import QApplication

class TestTimer(unittest.TestCase):
    """Test cases for the Timer class"""
    
    @classmethod
    def setUpClass(cls):
        # Create a QApplication instance if one doesn't exist
        if not QCoreApplication.instance():
            cls.app = QApplication([])
    
    def setUp(self):
        """Set up test environment"""
        self.timer = Timer()
    
    def test_initial_state(self):
        """Test initial state of timer"""
        self.assertEqual(self.timer.state, TimerState.STOPPED)
        self.assertEqual(self.timer.remaining_seconds, 0)
        self.assertEqual(self.timer.total_seconds, 0)
        self.assertEqual(self.timer.elapsed_seconds, 0)
        self.assertEqual(self.timer.progress_percentage, 0)
    
    def test_start_timer(self):
        """Test starting the timer"""
        duration = 60  # 1 minute
        self.timer.start(duration)
        
        self.assertEqual(self.timer.state, TimerState.RUNNING)
        self.assertEqual(self.timer.total_seconds, duration)
        self.assertEqual(self.timer.remaining_seconds, duration)
    
    def test_pause_resume(self):
        """Test pausing and resuming the timer"""
        duration = 60
        self.timer.start(duration)
        
        # Pause
        self.timer.pause()
        self.assertEqual(self.timer.state, TimerState.PAUSED)
        
        # Resume
        self.timer.resume()
        self.assertEqual(self.timer.state, TimerState.RUNNING)
    
    def test_stop(self):
        """Test stopping the timer"""
        duration = 60
        self.timer.start(duration)
        self.timer.stop()
        
        self.assertEqual(self.timer.state, TimerState.STOPPED)
        self.assertEqual(self.timer.remaining_seconds, 0)
    
    def test_reset(self):
        """Test resetting the timer"""
        duration = 60
        self.timer.start(duration)
        
        # Wait a bit
        time.sleep(0.1)
        
        # Reset
        self.timer.reset()
        
        self.assertEqual(self.timer.remaining_seconds, duration)
        self.assertEqual(self.timer.state, TimerState.RUNNING)
    
    def test_adjust_time(self):
        """Test adjusting timer duration"""
        duration = 60
        self.timer.start(duration)
        
        # Add 30 seconds
        self.timer.adjust_time(30)
        self.assertEqual(self.timer.total_seconds, 90)
        
        # Subtract 20 seconds
        self.timer.adjust_time(-20)
        self.assertEqual(self.timer.total_seconds, 70)
    
    def test_set_remaining_time(self):
        """Test setting remaining time"""
        duration = 60
        self.timer.start(duration)
        
        self.timer.set_remaining_time(30)
        self.assertEqual(self.timer.remaining_seconds, 30)
    
    def test_overtime(self):
        """Test overtime state when timer reaches zero"""
        # Mock _update_timer to force overtime
        self.timer.start(10)
        
        # Manually set remaining time to 0
        self.timer.set_remaining_time(0)
        
        # Check for OVERTIME state
        self.assertEqual(self.timer.state, TimerState.OVERTIME)
    
    @patch('time.time')
    def test_elapsed_time_calculation(self, mock_time):
        """Test elapsed time calculation"""
        # Mock time.time() to return controlled values
        mock_time.side_effect = [100, 105, 110]
        
        # Start timer
        self.timer.start(60)
        
        # Manually trigger update with 5 seconds elapsed
        self.timer._update_timer()
        
        # 60 - 5 = 55 seconds remaining
        self.assertEqual(self.timer.remaining_seconds, 55)
        self.assertEqual(self.timer.elapsed_seconds, 5)
    
    @patch('time.time')
    @patch('src.models.timer.datetime')
    def test_start_countdown(self, mock_datetime, mock_time):
        """Test countdown to a specific date/time"""
        # Create consistent mock time points
        mock_now = datetime(2023, 1, 1, 12, 0, 0)  # Noon on Jan 1, 2023
        mock_time.return_value = mock_now.timestamp()
        
        # Make datetime.now() return our mock time
        mock_datetime.now.return_value = mock_now
        
        # Target time 60 seconds in the future
        target_time = mock_now + timedelta(seconds=60)
        
        # Start countdown
        self.timer.start_countdown(target_time)
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.COUNTDOWN)
        
        # Countdown should be 60 seconds
        self.assertEqual(self.timer.remaining_seconds, 60)
    
    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        # Start a 100-second timer
        self.timer.start(100)
        
        # Manually set elapsed time to 25 seconds
        self.timer._total_seconds = 100
        self.timer._remaining_seconds = 75
        
        # 25% progress
        self.assertEqual(self.timer.progress_percentage, 25)
    
    def test_signals(self):
        """Test that signals are emitted correctly"""
        # Mock slot functions
        time_updated_slot = MagicMock()
        state_changed_slot = MagicMock()
        
        # Connect slots to signals
        self.timer.time_updated.connect(time_updated_slot)
        self.timer.state_changed.connect(state_changed_slot)
        
        # Start timer
        self.timer.start(60)
        
        # Check that signals were emitted
        time_updated_slot.assert_called_with(60)
        state_changed_slot.assert_called_with(TimerState.RUNNING)
        
        # Reset mocks
        time_updated_slot.reset_mock()
        state_changed_slot.reset_mock()
        
        # Pause timer
        self.timer.pause()
        
        # Check signals again
        time_updated_slot.assert_not_called()  # Time shouldn't update on pause
        state_changed_slot.assert_called_with(TimerState.PAUSED)


def main():
    unittest.main()

if __name__ == "__main__":
    main()