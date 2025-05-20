from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from datetime import datetime

class ReminderController(QObject):
    remind_to_start = pyqtSignal()
    remind_to_advance = pyqtSignal()

    def __init__(self,
                 meeting_controller,   # emits meeting_loaded & meeting_started
                 timer_controller,     # emits part_changed
                 settings_controller,  # to pull thresholds
                 parent= None):
        super().__init__(parent)

        self._meetings = meeting_controller
        self._timer    = timer_controller
        self._settings = settings_controller

        # QTimers for our two reminders
        self._start_timer   = QTimer(singleShot=True)
        self._advance_timer = QTimer(singleShot=True)
        self._start_timer.timeout.connect(self.remind_to_start.emit)
        self._advance_timer.timeout.connect(self.remind_to_advance.emit)

        # Hook up the signals
        meeting_controller.meeting_updated.connect(self._on_meeting_updated)
        meeting_controller.meeting_started.connect(self._on_meeting_started)
        timer_controller.part_changed.connect(self._on_part_changed)

    def _on_meeting_updated(self, meeting):
        # Cancel any old schedules
        self._start_timer.stop()
        # Calculate delay until the scheduled meeting time
        sched = meeting.date.replace(
            hour=self._settings.get_settings().midweek_meeting.time.hour,
            minute=self._settings.get_settings().midweek_meeting.time.minute,
        )
        now = datetime.now()
        delay = (sched - now).total_seconds()
        threshold = self._settings.get_settings().start_reminder_delay
        if self._settings.get_settings().start_reminder_enabled and delay + threshold > 0:
            self._start_timer.start(int((delay + threshold) * 1_000))

    def _on_meeting_started(self):
        # If they actually clicked Start, cancel the “did you forget?” reminder
        self._start_timer.stop()
        # And schedule first part overrun if needed
        self._schedule_advance(self._timer.current_part)

    def _on_part_changed(self, part, idx):
        self._advance_timer.stop()
        self._schedule_advance(part)

    def _schedule_advance(self, part):
        if not part: 
            return
        delay = part.duration_minutes * 60
        threshold = self._settings.get_settings().overrun_delay
        if self._settings.get_settings().overrun_enabled:
            self._advance_timer.start(int((delay + threshold) * 1_000))