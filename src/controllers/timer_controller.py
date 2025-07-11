"""
Controller for managing timer functionality in the OnTime Meeting Timer application.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import QObject, pyqtSignal

from src.controllers.settings_controller import SettingsController
from src.models.meeting import Meeting, MeetingPart, MeetingType
from src.models.timer import Timer, TimerState

class TransitionType(Enum):
    """Types of chairman transitions"""
    MIDWEEK = "Chairman Counsel and Transition"
    WEEKEND = "Chairman Introduction"
    GENERIC = "Chairman Transition"


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
    predicted_end_time_updated = pyqtSignal(datetime, datetime)  # original and predicted end times
    meeting_countdown_updated = pyqtSignal(int, str)  # seconds remaining, formatted message
    
    def __init__(self, settings_controller: SettingsController):
        """Initialize the TimerController with a settings controller"""
        super().__init__()
        
        # Initialize settings controller
        self.settings_controller = settings_controller
        self.settings_controller.settings_changed.connect(self._on_settings_updated)
        
        # Timer model
        self.timer = Timer()
        
        # Current meeting state
        self.current_meeting: Optional[Meeting] = None
        self.current_part_index: int = -1
        self.parts_list: List[MeetingPart] = []
        
        # Initialize timer to show current time
        self.timer.start_current_time_display()
        
        # Transition state
        self._in_transition = False
        self._next_part_after_transition = -1
        
        # Meeting progress tracking
        self._total_overtime_seconds = 0
        self._meeting_start_time = None
        self._original_end_time = None
        self._predicted_end_time = None
        self._remaining_parts_duration = 0
        
        # Meeting countdown tracking
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)  # Update every second
        self._countdown_timer.timeout.connect(self._update_meeting_countdown)
        self._meeting_target_datetime = None
        
        # Connect timer signals
        self.timer.state_changed.connect(self._handle_timer_state_change)
        self.timer.time_updated.connect(self._handle_time_update)
        
    def _initialize_current_time_display(self):
        """Initialize the timer to display current time"""
        # Update the display to show current time
        self.timer._update_current_time()
    
    def set_meeting(self, meeting: Meeting):
        """Set the current meeting and initialize countdown"""
        self.current_meeting = meeting
        self.current_part_index = -1
        self.parts_list = meeting.get_all_parts()
        
        # Stop any previous timer and show current time
        self.timer.stop()
        self.timer.start_current_time_display()
        
        # Initialize countdown to meeting start time
        self._initialize_meeting_countdown()
        
    def _initialize_meeting_countdown(self):
        """Initialize countdown to meeting start time"""
        # Prevent countdown reinitialization if meeting is already in progress
        if self.current_part_index >= 0:
            return
        if not self.current_meeting:
            return

        now = datetime.now()
        today = now.date()
        now_time = now.time()

        settings = self.settings_controller.get_settings()
        if self.current_meeting.meeting_type == MeetingType.MIDWEEK:
            meeting_day = settings.midweek_meeting.day.value
            meeting_time = settings.midweek_meeting.time
        else:
            meeting_day = settings.weekend_meeting.day.value
            meeting_time = settings.weekend_meeting.time

        days_ahead = (meeting_day - today.weekday() + 7) % 7
        candidate_date = today + timedelta(days=days_ahead)

        # Use today if it's the meeting day and meeting time is still in the future
        if days_ahead == 0 and meeting_time > now_time:
            target_date = today
        else:
            target_date = candidate_date

        target_datetime = datetime.combine(target_date, meeting_time)

        # Step 1: Store the target meeting time in the Timer model for internal tracking
        self.timer.target_meeting_time = target_datetime

        # Only set countdown if meeting is in the future
        if target_datetime > now:
            # Set countdown target - this will trigger countdown updates
            self.timer.set_meeting_target_time(target_datetime)

            self._meeting_target_datetime = target_datetime

            # Make sure we're in stopped state to show current time
            if self.timer.state != TimerState.STOPPED:
                self.timer.stop()
                self.timer.start_current_time_display()

            # Start the countdown timer if not already running
            if not self._countdown_timer.isActive():
                self._countdown_timer.start()

            # Emit the countdown signal with target time
            self.countdown_started.emit(target_datetime)
        else:
            # Meeting time has passed, clear any countdown
            self.timer.target_meeting_time = None

            # Stop the countdown timer if it's running
            if self._countdown_timer.isActive():
                self._countdown_timer.stop()
                
    def _update_meeting_countdown(self):
        """Update the meeting countdown display"""
        if not self.current_meeting:
            return

        meeting_datetime = self._meeting_target_datetime
        if not meeting_datetime:
            return

        now = datetime.now()
        time_diff = meeting_datetime - now
        seconds_remaining = int(time_diff.total_seconds())

        if seconds_remaining > 0:
            hours = seconds_remaining // 3600
            minutes = (seconds_remaining % 3600) // 60
            seconds = seconds_remaining % 60
            if hours > 0:
                countdown_msg = f"{self.tr('Meeting starts in')} {hours}h {minutes}m"
            else:
                countdown_msg = f"{self.tr('Meeting starts in')} {minutes}m"
            self.meeting_countdown_updated.emit(seconds_remaining, countdown_msg)
        else:
            countdown_msg = self.tr("Meeting starts now!")
            self.meeting_countdown_updated.emit(0, countdown_msg)
            self._countdown_timer.stop()
    
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
        
        # Reset overtime tracking
        self._total_overtime_seconds = 0
        
        # Record meeting start time and calculate original end time
        self._meeting_start_time = datetime.now()
        self._calculate_original_end_time()
        self._predicted_end_time = self._original_end_time
        
        # Start timer for first part
        self.timer.start(current_part.duration_seconds)
        
        # Stop the countdown timer if running
        if self._countdown_timer.isActive():
            self._countdown_timer.stop()
        
        # Emit signals
        self.part_changed.emit(current_part, self.current_part_index)
        self.meeting_started.emit()
        self.predicted_end_time_updated.emit(self._original_end_time, self._predicted_end_time)
    
    def _calculate_original_end_time(self):
        """Calculate the original end time based on scheduled parts"""
        if not self.current_meeting:
            return
        
        # Calculate total meeting duration in seconds
        total_seconds = 0
        for part in self.parts_list:
            total_seconds += part.duration_seconds
        
        # Add transition times between sections (1 minute per transition)
        section_transitions = len(self.current_meeting.sections) - 1
        total_seconds += section_transitions * 60
        
        # Set the original end time
        self._original_end_time = self._meeting_start_time + timedelta(seconds=total_seconds)
    
    def _update_predicted_end_time(self):
        """Update the predicted end time based on current progress and real-time data"""
        if not self._meeting_start_time or self.current_part_index < 0:
            return
        
        now = datetime.now()
        
        # CRITICAL FIX: Predicted end time must NEVER be earlier than current time
        # Calculate remaining time from current position forward
        
        remaining_time = 0.0
        
        # 1. Add remaining time from current part
        if (self.current_part_index < len(self.parts_list) and 
            self.timer.state in [TimerState.RUNNING, TimerState.PAUSED]):
            # Only count remaining time if not in overtime
            remaining_time += max(0, self.timer.remaining_seconds)
        elif (self.current_part_index < len(self.parts_list) and 
            self.timer.state == TimerState.OVERTIME):
            # If in overtime, no remaining time for current part
            remaining_time += 0
        
        # 2. Add duration of all future parts
        for i in range(self.current_part_index + 1, len(self.parts_list)):
            remaining_time += self.parts_list[i].duration_seconds
        
        # 3. Add remaining transitions
        remaining_transitions = self._calculate_remaining_transitions()
        remaining_time += remaining_transitions * 60
        
        # 4. GUARANTEE: Predicted end = current time + remaining time
        # This ensures predicted end is ALWAYS >= current time
        self._predicted_end_time = now + timedelta(seconds=remaining_time)
        
        # 5. Calculate overtime relative to original schedule
        if self._original_end_time and self._predicted_end_time > self._original_end_time:
            overtime_seconds = (self._predicted_end_time - self._original_end_time).total_seconds()
        else:
            overtime_seconds = 0
        
        # Emit signal with updated prediction
        self.predicted_end_time_updated.emit(self._original_end_time, self._predicted_end_time)
        
        # Debug logging to catch issues
        print(f"[TIMER] Predicted end time update:")
        print(f"  Current time: {now.strftime('%H:%M:%S')}")
        print(f"  Current part: {self.current_part_index + 1}/{len(self.parts_list)}")
        print(f"  Timer state: {self.timer.state}")
        print(f"  Current part remaining: {max(0, self.timer.remaining_seconds) if self.timer.state != TimerState.OVERTIME else 0:.0f}s")
        print(f"  Future parts time: {sum(self.parts_list[i].duration_seconds for i in range(self.current_part_index + 1, len(self.parts_list))):.0f}s")
        print(f"  Transitions remaining: {remaining_transitions}")
        print(f"  Total remaining: {remaining_time:.0f}s ({remaining_time/60:.1f}m)")
        print(f"  Predicted end: {self._predicted_end_time.strftime('%H:%M:%S')}")
        print(f"  Original end: {self._original_end_time.strftime('%H:%M:%S') if self._original_end_time else 'N/A'}")
        
        # SAFETY CHECK: This should never happen now
        if self._predicted_end_time < now:
            print(f"[ERROR] Predicted end time is in the past! This should not happen.")
            print(f"  Predicted: {self._predicted_end_time}")
            print(f"  Current: {now}")
    
    def _calculate_planned_elapsed_time(self) -> float:
        """Calculate how much time should have elapsed based on current part position"""
        if self.current_part_index < 0:
            return 0.0
        
        planned_elapsed = 0.0
        
        # Add duration of all completed parts
        for i in range(self.current_part_index):
            if i < len(self.parts_list):
                planned_elapsed += self.parts_list[i].duration_seconds
        
        # Add transitions that should have occurred
        completed_transitions = self._get_completed_transitions_count()
        planned_elapsed += completed_transitions * 60
        
        # Add elapsed time of current part
        if self.current_part_index < len(self.parts_list):
            current_part = self.parts_list[self.current_part_index]
            
            if self.timer.state == TimerState.OVERTIME:
                # If in overtime, we've used the full planned duration plus overtime
                planned_elapsed += current_part.duration_seconds
                # Note: overtime is handled by the drift calculation
            elif self.timer.state in [TimerState.RUNNING, TimerState.PAUSED]:
                # Add the elapsed portion of current part
                current_part_elapsed = current_part.duration_seconds - self.timer.remaining_seconds
                planned_elapsed += max(0, current_part_elapsed)
        
        return planned_elapsed
    
    def _calculate_remaining_planned_time(self) -> float:
        """Calculate remaining planned time from current position"""
        if self.current_part_index < 0:
            return sum(part.duration_seconds for part in self.parts_list)
        
        remaining_time = 0.0
        
        # Add remaining time from current part
        if (self.current_part_index < len(self.parts_list) and 
            self.timer.state in [TimerState.RUNNING, TimerState.PAUSED]):
            remaining_time += max(0, self.timer.remaining_seconds)
        
        # Add duration of future parts
        for i in range(self.current_part_index + 1, len(self.parts_list)):
            remaining_time += self.parts_list[i].duration_seconds
        
        # Add remaining transitions
        remaining_transitions = self._calculate_remaining_transitions()
        remaining_time += remaining_transitions * 60
        
        return remaining_time
    
    def _get_total_transitions_count(self) -> int:
        """Get total number of transitions in the meeting"""
        if not self.current_meeting:
            return 0
        
        if self.current_meeting.meeting_type == MeetingType.WEEKEND:
            return min(1, len(self.current_meeting.sections) - 1)  # Max 1 for weekend
        else:
            return max(0, len(self.current_meeting.sections) - 1)  # Between sections for midweek
    
    def _calculate_remaining_transitions(self) -> int:
        """Calculate how many chairman transitions are left"""
        if not self.current_meeting or self.current_part_index < 0:
            return 0
        
        remaining_transitions = 0
        current_section_index = -1
        
        # Find which section we're currently in
        part_count = 0
        for section_index, section in enumerate(self.current_meeting.sections):
            for part in section.parts:
                if part_count == self.current_part_index:
                    current_section_index = section_index
                    break
                part_count += 1
            if current_section_index != -1:
                break
        
        if current_section_index != -1:
            # Count transitions from current section to end
            if self.current_meeting.meeting_type == MeetingType.WEEKEND:
                # Weekend meetings have fewer transitions
                remaining_sections = len(self.current_meeting.sections) - current_section_index - 1
                remaining_transitions = min(remaining_sections, 1)  # Max 1 transition for weekend
            else:
                # Midweek meetings have transitions between sections
                remaining_sections = len(self.current_meeting.sections) - current_section_index - 1
                remaining_transitions = remaining_sections
        
        return remaining_transitions
    
    def _should_add_chairman_transition(self):
        """Check if we should add a chairman transition between parts"""
        if not self.current_meeting or not self.parts_list:
            return False

        # Don't add transition if we're at the last part
        if self.current_part_index < 0 or self.current_part_index >= len(self.parts_list) - 1:
            return False

        if self.current_meeting.meeting_type == MeetingType.WEEKEND:
            # Add transition only before part at index 1 or 2
            next_index = self.current_part_index + 1
            if next_index in [1, 2]:
                return True
            return False

        # Default: allow transition
        return True
    
    def _start_chairman_transition(self):
        """Start a 1-minute chairman transition period with meeting-specific text"""
        # Create a transition for 1 minute (60 seconds)
        transition_seconds = 60
        
        # Set timer state to transition
        self.timer._state = TimerState.TRANSITION
        self.timer.state_changed.emit(TimerState.TRANSITION)
        
        # Start the timer
        self.timer.start(transition_seconds)
        
        # Determine transition text based on meeting type
        transition_type = TransitionType.GENERIC
        if self.current_meeting:
            if self.current_meeting.meeting_type == MeetingType.MIDWEEK:
                transition_type = TransitionType.MIDWEEK
            elif self.current_meeting.meeting_type == MeetingType.WEEKEND:
                transition_type = TransitionType.WEEKEND
        
        # Emit a signal with the appropriate transition message
        self.transition_started.emit(transition_type.value)
        
        # Store that we're in transition mode and which part is next
        self._in_transition = True
        self._next_part_after_transition = self.current_part_index + 1
        
    def _complete_transition(self):
        """Let transition enter overtime instead of moving to next part"""
        if self._in_transition:
            self._in_transition = False
            # Do not auto-advance. Allow the timer to go into overtime.

    def next_part(self):
        """Move to the next part, allowing transitions to be skipped"""
        if not self.current_meeting or not self.parts_list:
            return
        
        # If we're in a transition, cancel it and move immediately to the next part
        if self._in_transition:
            if hasattr(self, '_transition_timer') and self._transition_timer.isActive():
                self._transition_timer.stop()
            self._in_transition = False
            self.current_part_index = self._next_part_after_transition
            if self.current_part_index >= len(self.parts_list):
                self.stop_meeting()
                return
            current_part = self.parts_list[self.current_part_index]
            self.timer.start(current_part.duration_seconds)
            self.part_changed.emit(current_part, self.current_part_index)
            self._update_predicted_end_time()
            return
        
        # Mark current part as completed
        if 0 <= self.current_part_index < len(self.parts_list):
            self.parts_list[self.current_part_index].is_completed = True
            self.part_completed.emit(self.current_part_index)
        
        # Add a chairman transition after every part
        if self._should_add_chairman_transition():
            self._start_chairman_transition()
            
            # Update predicted end time
            self._update_predicted_end_time()
            return
        
        # If no transition needed, move to next part directly
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
        
        # Update predicted end time
        self._update_predicted_end_time()
    
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
        
        # Update predicted end time
        self._update_predicted_end_time()
    
    def stop_meeting(self):
        """Stop the current meeting"""
        # Cancel any active transition timer
        if hasattr(self, '_transition_timer') and self._transition_timer.isActive():
            self._transition_timer.stop()
        
        self._in_transition = False
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
        
        # Update predicted end time since we've changed the duration
        self._update_predicted_end_time()
    
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
            
            # Update predicted end time
            self._update_predicted_end_time()
    
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
            pass
    
    def _handle_time_update(self, seconds: int):
        """Handle timer time updates to track meeting progress"""
        # Update predicted end time on every timer update for real-time accuracy
        self._update_predicted_end_time()
        
        # Check if we're in overtime
        if self.timer.state == TimerState.OVERTIME:
            # Use the exact value from the timer instead of incrementing
            current_overtime = abs(seconds)  # Get absolute value of the negative seconds
            self._total_overtime_seconds = current_overtime
            
            # Emit signal about total meeting overtime
            self.meeting_overtime.emit(self._total_overtime_seconds)
            
    def apply_current_part_update(self):
        """Apply updated duration to the currently running part without restarting timer"""
        if 0 <= self.current_part_index < len(self.parts_list):
            current_part = self.parts_list[self.current_part_index]
            self.timer.set_duration(current_part.duration_minutes)
    def _on_settings_updated(self):
        """Handle updates to settings such as meeting time"""
        #settings = self.settings_controller.get_settings()
        if self.current_meeting:
            # Update the meeting time in the timer
            self._initialize_meeting_countdown()