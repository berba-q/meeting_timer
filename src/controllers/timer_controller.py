"""
Controller for managing timer functionality in the JW Meeting Timer application.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from src.models.meeting import Meeting, MeetingPart
from src.models.timer import Timer, TimerState

class TimerController(QObject):
    """Controller for managing timer functionality"""
    
    # Signals
    part_changed = pyqtSignal(MeetingPart, int)  # part, index
    part_completed = pyqtSignal(int)  # part index
    meeting_started = pyqtSignal()
    meeting_ended = pyqtSignal()
    countdown_started = pyqtSignal(datetime)  # target datetime
    transition_started = pyqtSignal(str)  # transition description
    meeting_overtime = pyqtSignal(int)  # total overtime in seconds
    
    def __init__(self):
        super().__init__()
        
        # Timer model
        self.timer = Timer()
        
        # Current meeting state
        self.current_meeting: Optional[Meeting] = None
        self.current_part_index: int = -1
        self.parts_list: List[MeetingPart] = []
        
        # Transition state
        self._in_transition = False
        self._next_part_after_transition = -1
        
        # Meeting progress tracking
        self._total_overtime_seconds = 0
        
        # Connect timer signals
        self.timer.state_changed.connect(self._handle_timer_state_change)
        self.timer.time_updated.connect(self._handle_time_update)
    
    def set_meeting(self, meeting: Meeting):
        """Set the current meeting"""
        self.current_meeting = meeting
        self.current_part_index = -1
        self.parts_list = meeting.get_all_parts()
    
    def start_meeting(self):
        """Start the current meeting"""
        if not self.current_meeting or not self.parts_list:
            return
        
        # Reset all parts completion status
        for part in self.parts_list:
            part.is_completed = False
        
        # Move to first part
        self.current_part_index = 0
        current_part = self.parts_list[self.current_part_index]
        
        # Start timer for first part
        self.timer.start(current_part.duration_seconds)
        
        # Emit signals
        self.part_changed.emit(current_part, self.current_part_index)
        self.meeting_started.emit()
    
    def next_part(self):
        """Move to the next part"""
        if not self.current_meeting or not self.parts_list:
            return
        
        # Mark current part as completed
        if 0 <= self.current_part_index < len(self.parts_list):
            self.parts_list[self.current_part_index].is_completed = True
            self.part_completed.emit(self.current_part_index)
        
        # Check if we need to add a chairman transition
        # Transitions happen between sections, not between parts within the same section
        if self._should_add_chairman_transition():
            self._start_chairman_transition()
            return
        
        # Move to next part
        self.current_part_index += 1
        
        # Check if we're at the end
        if self.current_part_index >= len(self.parts_list):
            self.stop_meeting()
            return
        
        # Get next part
        current_part = self.parts_list[self.current_part_index]
        
        # Start timer for next part
        self.timer.start(current_part.duration_seconds)
        
        # Emit signal
        self.part_changed.emit(current_part, self.current_part_index)
    
    def _should_add_chairman_transition(self):
        """Check if we should add a chairman transition between parts"""
        if not self.current_meeting or not self.parts_list:
            return False
            
        if self.current_part_index < 0 or self.current_part_index >= len(self.parts_list) - 1:
            return False
            
        # Get the current part and the next part
        current_part_index = self.current_part_index
        next_part_index = current_part_index + 1
        
        # Find which section each part belongs to
        current_section_index = -1
        next_section_index = -1
        
        part_count = 0
        for section_index, section in enumerate(self.current_meeting.sections):
            for _ in section.parts:
                if part_count == current_part_index:
                    current_section_index = section_index
                if part_count == next_part_index:
                    next_section_index = section_index
                part_count += 1
        
        # Add transition if parts are in different sections
        return current_section_index != next_section_index and current_section_index != -1 and next_section_index != -1
    
    def _start_chairman_transition(self):
        """Start a 1-minute chairman transition period"""
        # Create a transition for 1 minute (60 seconds)
        transition_seconds = 60
        
        # Set timer state to transition
        self.timer._state = TimerState.TRANSITION
        self.timer.state_changed.emit(TimerState.TRANSITION)
        
        # Start the timer
        self.timer.start(transition_seconds)
        
        # Emit a signal that we're in transition mode
        self.transition_started = pyqtSignal()
        self.transition_started.emit()
        
        # Store that we're in transition mode and which part is next
        self._in_transition = True
        self._next_part_after_transition = self.current_part_index + 1
    
    def previous_part(self):
        """Move to the previous part"""
        if not self.current_meeting or not self.parts_list:
            return
        
        # Move to previous part
        self.current_part_index -= 1
        
        # Check if we're at the beginning
        if self.current_part_index < 0:
            self.current_part_index = 0
        
        # Get current part
        current_part = self.parts_list[self.current_part_index]
        
        # Start timer for this part
        self.timer.start(current_part.duration_seconds)
        
        # Emit signal
        self.part_changed.emit(current_part, self.current_part_index)
    
    def stop_meeting(self):
        """Stop the current meeting"""
        self.timer.stop()
        self.current_part_index = -1
        self.meeting_ended.emit()
    
    def pause_timer(self):
        """Pause the current timer"""
        self.timer.pause()
    
    def resume_timer(self):
        """Resume the current timer"""
        self.timer.resume()
    
    def reset_timer(self):
        """Reset the current timer"""
        if 0 <= self.current_part_index < len(self.parts_list):
            current_part = self.parts_list[self.current_part_index]
            self.timer.start(current_part.duration_seconds)
    
    def adjust_time(self, minutes_delta: int):
        """Adjust the current timer by adding/removing minutes"""
        self.timer.adjust_time(minutes_delta * 60)
    
    def jump_to_part(self, part_index: int):
        """Jump to a specific part"""
        if not self.current_meeting or not self.parts_list:
            return
        
        if 0 <= part_index < len(self.parts_list):
            # Mark parts before this as completed
            for i in range(part_index):
                self.parts_list[i].is_completed = True
                self.part_completed.emit(i)
            
            # Set current part
            self.current_part_index = part_index
            current_part = self.parts_list[self.current_part_index]
            
            # Start timer for this part
            self.timer.start(current_part.duration_seconds)
            
            # Emit signal
            self.part_changed.emit(current_part, self.current_part_index)
    
    def start_countdown_to_meeting(self, meeting: Meeting):
        """Start countdown to the meeting time"""
        # Create target datetime from meeting date and time
        meeting_datetime = datetime.combine(meeting.date, meeting.start_time)
        
        # Start countdown
        self.timer.start_countdown(meeting_datetime)
        
        # Emit signal
        self.countdown_started.emit(meeting_datetime)
    
    def _handle_timer_state_change(self, state: TimerState):
        """Handle timer state changes"""
        if state == TimerState.OVERTIME:
            # Timer has reached zero, but we'll let it continue counting
            # until the user manually advances
            pass
        
        elif state == TimerState.STOPPED:
            # Timer was stopped, check if we need to advance
            if state == TimerState.COUNTDOWN:
                # Countdown finished, start the meeting
                self.start_meeting()
        
        elif state == TimerState.TRANSITION:
            # In transition mode
            self._in_transition = True
            
            # Determine if it's midweek or weekend meeting
            transition_msg = "Chairman transition"
            if self.current_meeting:
                if self.current_meeting.meeting_type == MeetingType.MIDWEEK:
                    transition_msg = "Chairman counsel and transition"
                elif self.current_meeting.meeting_type == MeetingType.WEEKEND:
                    transition_msg = "Chairman introduction"
            
            # Emit transition started signal
            self.transition_started.emit(transition_msg)
    
    def _handle_time_update(self, seconds: int):
        """Handle timer time updates to track meeting progress"""
        # Check if we're in overtime
        if self.timer.state == TimerState.OVERTIME:
            # Update total overtime count
            part_overtime = abs(seconds)
            self._total_overtime_seconds += 1  # Increment by one second
            
            # Emit signal about total meeting overtime
            self.meeting_overtime.emit(self._total_overtime_seconds)
        
        # Check if transition is complete
        if self._in_transition and seconds == 0:
            self._in_transition = False
            
            # Move to the next part
            self.current_part_index = self._next_part_after_transition
            
            # Check if we're at the end
            if self.current_part_index >= len(self.parts_list):
                self.stop_meeting()
                return
            
            # Get next part
            current_part = self.parts_list[self.current_part_index]
            
            # Start timer for next part
            self.timer.start(current_part.duration_seconds)
            
            # Emit signal
            self.part_changed.emit(current_part, self.current_part_index)