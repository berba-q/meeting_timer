# Create a file called tests/timer_testable.py
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.timer import TimerState, TimerDisplayMode
from datetime import datetime
import time

class SimpleTimer:
    """A simplified version of Timer for testing without Qt dependencies"""
    
    def __init__(self):
        # Timer properties
        self._total_seconds = 0
        self._remaining_seconds = 0
        self._start_time = None
        self._elapsed_time = 0
        self._state = TimerState.STOPPED
        
    @property
    def state(self) -> TimerState:
        return self._state
    
    @property
    def remaining_seconds(self) -> int:
        return self._remaining_seconds
    
    @property
    def total_seconds(self) -> int:
        return self._total_seconds
    
    @property
    def elapsed_seconds(self) -> int:
        return self._total_seconds - self._remaining_seconds
    
    @property
    def progress_percentage(self) -> float:
        if self._total_seconds == 0:
            return 0
        return (self.elapsed_seconds / self._total_seconds) * 100
    
    def start(self, duration_seconds: int):
        self._total_seconds = duration_seconds
        self._remaining_seconds = duration_seconds
        self._start_time = time.time()
        self._elapsed_time = 0
        self._state = TimerState.RUNNING
    
    def pause(self):
        if self._state == TimerState.RUNNING:
            self._elapsed_time += time.time() - self._start_time
            self._state = TimerState.PAUSED
    
    def resume(self):
        if self._state == TimerState.PAUSED:
            self._start_time = time.time()
            self._state = TimerState.RUNNING
    
    def stop(self):
        self._state = TimerState.STOPPED
        self._remaining_seconds = 0
    
    def reset(self):
        was_running = self._state == TimerState.RUNNING
        self._start_time = time.time() if was_running else None
        self._elapsed_time = 0
        self._remaining_seconds = self._total_seconds
        
    def adjust_time(self, seconds_delta: int):
        new_total = max(0, self._total_seconds + seconds_delta)
        
        if self._state != TimerState.STOPPED:
            elapsed_percentage = self.elapsed_seconds / self._total_seconds if self._total_seconds > 0 else 0
            self._remaining_seconds = int(new_total * (1 - elapsed_percentage))
        else:
            self._remaining_seconds = new_total
            
        self._total_seconds = new_total
    
    def set_remaining_time(self, seconds: int):
        self._remaining_seconds = max(0, min(seconds, self._total_seconds))
        
        if self._remaining_seconds == 0 and self._state == TimerState.RUNNING:
            self._state = TimerState.OVERTIME
    
    def start_countdown(self, target_datetime: datetime):
        self._state = TimerState.COUNTDOWN
        
        # Use the provided target_datetime to calculate time difference
        now = datetime.now()
        time_diff = target_datetime - now
        
        if time_diff.total_seconds() <= 0:
            self.stop()
            return
        
        self._total_seconds = int(time_diff.total_seconds())
        self._remaining_seconds = self._total_seconds
        self._start_time = time.time()
        self._elapsed_time = 0
        
        # Make sure state is set to COUNTDOWN before returning
        return self._state  # Return the state for easier debugging
        
    def update(self):
        """Manually update the timer state - replacement for QTimer's automatic updates"""
        if self._state == TimerState.RUNNING:
            elapsed = self._elapsed_time + (time.time() - self._start_time)
            self._remaining_seconds = max(0, int(self._total_seconds - elapsed))
            
            if self._remaining_seconds == 0:
                self._state = TimerState.OVERTIME
        
        elif self._state == TimerState.OVERTIME:
            elapsed = self._elapsed_time + (time.time() - self._start_time)
            overtime_seconds = int(elapsed - self._total_seconds)
            self._remaining_seconds = -overtime_seconds
            
        elif self._state == TimerState.COUNTDOWN:
            now = time.time()
            elapsed = now - self._start_time
            self._remaining_seconds = max(0, int(self._total_seconds - elapsed))
            
            if self._remaining_seconds == 0:
                self.stop()