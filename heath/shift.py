import datetime
from heath.exceptions import ShiftConsistencyError, ShiftError
from heath.project import Project
from heath.time_utils import pretty_duration, pretty_time


class Shift:
    def __init__(self, project: Project, date: datetime.date):
        self.project = project
        self.date = date
        self._start_time = None
        self._stop_time = None
        self._lunch_duration = datetime.timedelta()

    def __str__(self):
        string = self.project.key
        if self.start_time:
            string += f" {pretty_time(self.start_time)} -"
        if self.stop_time:
            string += f" {pretty_time(self.stop_time)}"
        if self.lunch_duration:
            string += f", Lunch {pretty_duration(self.lunch_duration)}"
        return string

    @property
    def all_day(self):
        return self.project.all_day

    @property
    def start_time(self) -> datetime.datetime:
        return self._start_time

    @property
    def lunch_duration(self) -> datetime.timedelta:
        return self._lunch_duration

    @property
    def stop_time(self) -> datetime.datetime:
        return self._stop_time

    @property
    def started(self) -> bool:
        return self.start_time is not None

    @property
    def completed(self) -> bool:
        return self.all_day or (
            self.start_time is not None and self.stop_time is not None
        )

    @property
    def duration(self) -> datetime.timedelta:
        if self.stop_time is not None:
            return self.stop_time - self.start_time - self.lunch_duration
        else:
            return datetime.timedelta()

    @property
    def current_duration(self) -> datetime.timedelta:
        if self.completed:
            return self.duration
        else:
            return self.duration_at(datetime.datetime.now().replace(second=0))

    def duration_at(self, read_time: datetime.datetime) -> datetime.timedelta:
        return max(
            read_time - self.start_time - self.lunch_duration, datetime.timedelta()
        )

    def start(self, start_time: datetime.datetime):
        if self.all_day:
            raise ShiftError("All day shifts cant be started.")
        self._start_time = start_time

    def lunch(self, lunch_duration: datetime.timedelta):
        if not self.started:
            raise ShiftConsistencyError("Shift must be started to have a lunch.")
        self._lunch_duration = lunch_duration

    def stop(self, stop_time: datetime.datetime):
        if not self.started:
            raise ShiftConsistencyError("Shift must be started to be stopped.")
        next_date = (
            datetime.datetime.combine(self.date, datetime.datetime.min.time())
            + datetime.timedelta(days=1)
        ).date()
        if stop_time.date() not in (self.date, next_date):
            raise ShiftConsistencyError(
                "Stop time must be on the same or on the next date as shift. "
                f"{stop_time.date()} not in ({self.date}, {next_date})"
            )
        if stop_time < (self.start_time + self.lunch_duration):
            raise ShiftConsistencyError(
                "Shift can't be stopped before start plus lunch."
            )
        self._stop_time = stop_time

    def report_data(self, include_active_shift: bool = False):
        start_stop = ""
        if self.start_time:
            start_stop += f"{pretty_time(self.start_time)} -"

        if self.stop_time:
            start_stop += f" {pretty_time(self.stop_time)}"
        elif include_active_shift:
            start_stop += f" ({pretty_time(datetime.datetime.now())})"

        duration_string = ""
        if not self.all_day and (self.completed or include_active_shift):
            duration = (
                self.duration
                if self.completed
                else self.duration_at(datetime.datetime.now().replace(second=0))
            )
            duration_string = pretty_duration(duration)
        return (
            self.project.key,
            start_stop,
            f"Lunch {pretty_duration(self.lunch_duration)}"
            if self.lunch_duration
            else "",
            duration_string,
        )
