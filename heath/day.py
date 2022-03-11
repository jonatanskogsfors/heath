from collections import defaultdict
import datetime
from email.policy import default
from typing import Optional
from heath.exceptions import DateInconsistencyError, DayInconsistencyError, DayError
from heath.shift import Shift
from heath.time_utils import pretty_duration
from tabulate import tabulate


class Day:
    def __init__(self, date: datetime.date, comment: str = None):
        if not isinstance(date, datetime.date):
            raise DayError("A date must be given.")
        self.date = date
        self.comment = comment
        self._shifts = []

    def __str__(self):
        date = f"{self.date.day}."
        shifts = "; ".join(str(shift) for shift in self.shifts)
        comment = f"# {self.comment}" if self.comment else ""
        return " ".join(element for element in (date, shifts, comment) if element)

    @property
    def shifts(self) -> list[Shift]:
        return self._shifts

    @property
    def current_shift(self) -> Optional[Shift]:
        if self.shifts:
            last_shift = self.shifts[-1]
            if last_shift.started and not last_shift.completed:
                return last_shift
        return None

    @property
    def start_time(self) -> datetime.timedelta:
        return self.shifts[0].start_time

    @property
    def stop_time(self) -> datetime.timedelta:
        return self.shifts[-1].stop_time

    @property
    def worked_hours(self) -> datetime.timedelta:
        return sum(
            (shift.duration for shift in self.shifts), start=datetime.timedelta()
        )

    @property
    def projects(self):
        return list(
            {shift.project.key: shift.project for shift in self.shifts}.values()
        )

    @property
    def all_day_project_name(self):
        return self.shifts[0].project.key if self.all_day else None

    @property
    def all_day(self) -> bool:
        return len(self.shifts) == 1 and self.shifts[0].all_day

    @property
    def completed(self):
        return self.all_day or (
            self.shifts and all(shift.completed for shift in self.shifts)
        )

    def duration_at(self, read_time: datetime.datetime) -> datetime.timedelta:
        return sum(
            (
                shift.duration if shift.completed else shift.duration_at(read_time)
                for shift in self.shifts
            ),
            start=datetime.timedelta(),
        )

    def add_shift(self, shift: Shift):
        if shift.date != self.date:
            raise DayInconsistencyError(
                f"Shift and Day does not share date ({shift.date} != {self.date})"
            )
        if shift.project.all_day:
            if self._shifts:
                raise DayInconsistencyError(
                    "All day shift can only be added to empty days."
                )
        else:
            self._shift_consistency_check(shift)
        self._shifts.append(shift)

    def report(
        self,
        include_active_shift: bool = False,
        include_comments: bool = False,
        by_project: bool = False,
    ):
        if by_project:
            projects = defaultdict(datetime.timedelta)
            for shift in self.shifts:
                if include_active_shift:
                    projects[shift.project.key] += shift.current_duration
                else:
                    projects[shift.project.key] += shift.duration
            shift_data = sorted(
                (project, pretty_duration(duration))
                for project, duration in projects.items()
            )
        else:
            shift_data = (
                shift.report_data(include_active_shift=include_active_shift)
                for shift in self.shifts
            )

        table = tabulate(shift_data)

        header = self.date.strftime("%A %-d %B, %Y").capitalize()

        original_line = table.splitlines()[0]
        solid_line = "-" * max(len(original_line), len(header))
        table = table.replace(original_line, solid_line)
        if include_active_shift:
            duration = pretty_duration(
                self.duration_at(datetime.datetime.now().replace(second=0))
            )

        else:
            duration = pretty_duration(self.worked_hours)

        footer = f"Totalt:{duration.rjust(len(solid_line) - 7)}"
        report_string = "\n".join(
            (
                solid_line,
                header.center(len(solid_line)),
                table,
                footer,
                solid_line,
            )
        )
        if include_comments and self.comment:
            report_string += f"\n# {self.comment}"

        return report_string

    def report_data(
        self, include_active_shift: bool = False, include_comments: bool = False
    ):
        date_string = f"{self.date.strftime('%a')} {self.date.day:>2}.".capitalize()
        shifts_string = "\n".join(str(shift) for shift in self.shifts)
        duration_string = ""
        if not self.all_day and (self.completed or include_active_shift):
            duration = (
                self.worked_hours
                if self.completed
                else self.duration_at(datetime.datetime.now().replace(second=0))
            )
            duration_string = pretty_duration(duration)
        return (
            date_string,
            shifts_string,
            duration_string,
            f"# {self.comment}" if self.comment and include_comments else None,
        )

    def _shift_consistency_check(self, shift: Shift):
        # (StartA <= EndB) and (EndA >= StartB)
        for existing_shift in self.shifts:
            if not existing_shift.completed:
                raise DateInconsistencyError("Previous shift not completed.")

            if (
                shift.completed
                and (existing_shift.start_time < shift.stop_time)
                and (existing_shift.stop_time > shift.start_time)
            ):
                raise DayInconsistencyError(
                    "Added shift overlaps with a previous shift "
                    f"({shift.start_time}-{shift.stop_time}, "
                    f"{existing_shift.start_time}-{existing_shift.stop_time}"
                )


class NonWorkingDay(Day):
    def report_data(
        self, include_active_shift: bool = False, include_comments: bool = False
    ):
        date_string = f"{self.date.strftime('%a')} {self.date.day:>2}.".capitalize()
        return (date_string, f"\x1B[3m{self.comment}\x1B[0m")
