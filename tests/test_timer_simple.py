# Create a file called tests/test_timer_simple.py
import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import patch

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
# Import the simplified timer for testing
from tests.time_testable import SimpleTimer
from src.models.timer import TimerState

class TestTimer(unittest.TestCase):
    def setUp(self):
        self.timer = SimpleTimer()
    
    def test_initial_state(self):
        self.assertEqual(self.timer.state, TimerState.STOPPED)
        self.assertEqual(self.timer.remaining_seconds, 0)
        self.assertEqual(self.timer.total_seconds, 0)
        
    def test_start_timer(self):
        self.timer.start(60)
        self.assertEqual(self.timer.state, TimerState.RUNNING)
        self.assertEqual(self.timer.total_seconds, 60)
        
    def test_pause_resume(self):
        self.timer.start(60)
        self.timer.pause()
        self.assertEqual(self.timer.state, TimerState.PAUSED)
        self.timer.resume()
        self.assertEqual(self.timer.state, TimerState.RUNNING)
        
    # Add more tests as needed...
    
    @patch('time.time')
    @patch('tests.time_testable.datetime')
    def test_start_countdown(self, mock_datetime, mock_time):
        # Create consistent mock time points
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_time.return_value = mock_now.timestamp()
        mock_datetime.now.return_value = mock_now
        
        # Target time 60 seconds in the future
        target_time = mock_now + timedelta(seconds=60)
        
        print(f"Mock now: {mock_now}")
        print(f"Target time: {target_time}")
        print(f"Time difference: {(target_time - mock_now).total_seconds()} seconds")
        
        # Start countdown
        result_state = self.timer.start_countdown(target_time)
        print(f"Returned state: {result_state}")
        print(f"Timer state: {self.timer.state}")
        print(f"Timer remaining: {self.timer.remaining_seconds}")
        
        # Check state
        self.assertEqual(self.timer.state, TimerState.COUNTDOWN)
        self.assertEqual(self.timer.remaining_seconds, 60)

if __name__ == "__main__":
    unittest.main()