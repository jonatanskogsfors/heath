from collections import defaultdict
import datetime
from typing import Optional
from heath.exceptions import DateInconsistencyError, DayInconsistencyError, DayError
from heath.shift import Shift
from heath.time_utils import pretty_duration, pretty_time
import tabulate

tabulate.PRESERVE_WHITESPACE = True


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
    def start_time(self) -> datetime.datetime:
        return self.shifts[0].start_time

    @property
    def stop_time(self) -> datetime.datetime:
        return self.shifts[-1].stop_time

    @property
    def lunch(self) -> datetime.timedelta:
        return sum(
            (shift.lunch_duration for shift in self.shifts), datetime.timedelta()
        )

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

        table = tabulate.tabulate(shift_data)

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

    def report_data_by_project(self, include_active_shift: bool = False):

        projects = defaultdict(datetime.timedelta)
        for shift in self.shifts:
            if include_active_shift:
                projects[shift.project.key] += shift.current_duration
            else:
                projects[shift.project.key] += shift.duration
        return sorted((project, duration) for project, duration in projects.items())

    def report_data(
        self,
        include_active_shift: bool = False,
        include_comments: bool = False,
        by_project: bool = False,
    ):
        date_string = f"{self.date.strftime('%a')} {self.date.day:>2}.".capitalize()

        duration_string = ""

        if by_project:
            projects = defaultdict(datetime.timedelta)
            for shift in self.shifts:
                if include_active_shift:
                    projects[shift.project.key] += shift.current_duration
                else:
                    projects[shift.project.key] += shift.duration
            shift_data = sorted(
                (project, duration) for project, duration in projects.items()
            )

            shifts_string = "\n".join([shift[0] for shift in shift_data])
            duration_string = "\n".join(
                pretty_duration(shift[1]) for shift in shift_data
            )
        else:
            shifts_string = "\n".join(str(shift) for shift in self.shifts)

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

    def overview(self, week_balance: tuple[str, datetime.timedelta] = None):
        if self.completed:
            data = [
                ("Starttid", pretty_time(self.start_time).rjust(5)),
                ("Lunchlängd", pretty_duration(self.lunch).rjust(5)),
                ("Sluttid", pretty_time(self.stop_time).rjust(5)),
                ("Arbetade timmar", pretty_duration(self.worked_hours).rjust(5)),
            ]
            if week_balance:
                data.append(
                    (
                        "Veckobalans",
                        f"{week_balance[0]}{pretty_duration(week_balance[1])}",
                    )
                )
        elif self.shifts:
            current_time = datetime.datetime.now().replace(second=0, microsecond=0)
            current_duration = self.duration_at(current_time)
            time_left = abs(datetime.timedelta(hours=8) - current_duration)
            sign = "+" if current_duration >= datetime.timedelta(hours=8) else "-"
            full_day = current_time + time_left
            data = [
                ("Starttid", pretty_time(self.start_time).rjust(5)),
                (
                    "Lunchlängd",
                    pretty_duration(self.lunch).rjust(5)
                    if self.lunch
                    else "-".center(5),
                ),
                (
                    "Arbetade timmar",
                    f"{pretty_duration(current_duration):>5} ({sign}{pretty_duration(time_left)})",
                ),
                ("8 timmar", pretty_time(full_day).rjust(5)),
            ]
            if week_balance:
                in_phase_with_week = full_day
                if week_balance[0] == "+":
                    in_phase_with_week -= week_balance[1]
                elif week_balance[0] == "-":
                    in_phase_with_week += week_balance[1]
                data.append(
                    ("I fas med veckan", pretty_time(in_phase_with_week).rjust(5))
                )
        table = tabulate.tabulate(data)
        header = self.date.strftime("%A %-d %B, %Y").capitalize()

        original_line = table.splitlines()[0]
        solid_line = "-" * max(len(original_line), len(header))
        table = table.replace(original_line, solid_line)

        overview_string = "\n".join(
            (
                solid_line,
                header.center(len(solid_line)),
                table,
            )
        )

        return overview_string

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
