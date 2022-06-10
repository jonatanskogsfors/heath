from collections import defaultdict
import datetime
from typing import Collection, Iterable, Optional
from heath.day import Day, NonWorkingDay
from tabulate import tabulate
from heath.time_utils import pretty_duration, time_to_seconds
import statistics


class TimePeriod:
    def __init__(self):
        self._days: list[Day] = []
        self._non_working_dates = {}
        self.title = ""

    @property
    def days(self) -> list[Day]:
        return self._days

    @property
    def complete_days(self) -> list[Day]:
        return [day for day in self.days if day.completed]

    @property
    def all_days(self) -> list[Day]:
        return sorted(
            self.days + list(self._non_working_dates.values()), key=lambda d: d.date
        )

    @property
    def projects(self) -> list[str]:
        return list(
            {
                project.key: project for day in self.days for project in day.projects
            }.values()
        )

    @property
    def worked_hours(self) -> datetime.timedelta:
        return sum((day.worked_hours for day in self.days), start=datetime.timedelta())

    @property
    def balance(self) -> tuple[str, datetime.timedelta]:
        non_all_day_days = [day for day in self.complete_days if not day.all_day]
        worked_hours = sum(
            (day.worked_hours for day in non_all_day_days), datetime.timedelta()
        )
        expected_hours = len(non_all_day_days) * datetime.timedelta(hours=8)
        balance = abs(expected_hours - worked_hours)
        sign = "+" if self.worked_hours > expected_hours else "-"
        return sign, balance

    def duration_at(self, read_time: datetime.datetime) -> datetime.timedelta:
        return sum(
            (day.duration_at(read_time) for day in self.days),
            start=datetime.timedelta(),
        )

    @property
    def last_day(self) -> Optional[Day]:
        return self._days[-1] if self._days else None

    def get_day(self, date_number: int) -> Optional[Day]:
        requested_date = datetime.date(self.year, self.month, date_number)
        for day in self.days:
            if day.date == requested_date:
                return day
        return self._non_working_dates.get(requested_date)

    def __iter__(self):
        return self._days.__iter__()

    def report(
            self,
            include_active_day: bool = False,
            include_comments: bool = False,
            by_project: bool = False,
            by_project_total: bool = False,
    ) -> str:
        if by_project_total:
            projects = defaultdict(datetime.timedelta)
            day_data = [
                day.report_data_by_project(include_active_shift=include_active_day)
                for day in self.all_days
            ]
            for day in day_data:
                for project, duration in day:
                    projects[project] += duration
            report_data = [
                (project, pretty_duration(duration).rjust(6))
                for project, duration in projects.items()
            ]
        else:
            report_data = [
                day.report_data(
                    include_active_shift=include_active_day,
                    include_comments=include_comments,
                    by_project=by_project,
                )
                for day in self.all_days
            ]
        table = tabulate(report_data)
        if not table:
            return f"No data for {self.title}."
        original_line = table.splitlines()[0]
        solid_line = "-" * len(original_line)
        table = table.replace(original_line, solid_line)
        if include_active_day:
            duration = pretty_duration(
                self.duration_at(datetime.datetime.now().replace(second=0))
            )

        else:
            duration = pretty_duration(self.worked_hours)

        footer = f"Totalt:{duration.rjust(len(solid_line) - 7)}"
        return "\n".join(
            (
                solid_line,
                self.title.center(len(solid_line)),
                table,
                footer,
                solid_line,
            )
        )

    def statistics_report(self):
        table = tabulate(self.statistics(), headers=("", "Medel", "Median", "SD"))
        original_line = table.splitlines()[1]
        solid_line = "-" * len(original_line)
        return "\n".join(
            (
                solid_line,
                self.title.center(len(solid_line)),
                solid_line,
                table,
                solid_line,
            )
        )

    def statistics(self):
        start_stats = mean_median_std(
            [
                time_to_seconds(day.start_time.time())
                for day in self.days
                if day.start_time
            ]
        )

        stop_stats = mean_median_std(
            [
                time_to_seconds(day.stop_time.time())
                for day in self.days
                if day.stop_time
            ]
        )

        lunch_stats = mean_median_std(
            [day.lunch.total_seconds() for day in self.days if day.lunch]
        )

        return (
            (
                "Start",
                *(
                    pretty_duration(stat, round_seconds=True).rjust(5)
                    for stat in start_stats
                ),
            ),
            (
                "Slut",
                *(
                    pretty_duration(stat, round_seconds=True).rjust(5)
                    for stat in stop_stats
                ),
            ),
            (
                "Lunch",
                *(
                    pretty_duration(stat, round_seconds=True).rjust(5)
                    for stat in lunch_stats
                ),
            ),
        )

    def overview(self):
        sign, balance = self.balance
        table = tabulate(
            (("Arbetade timmar", pretty_duration(self.worked_hours).rjust(6)),
             ("Balans", f"{sign if balance else ''}{pretty_duration(balance)}".rjust(6))),

        )
        original_line = table.splitlines()[0]
        solid_line = "-" * len(original_line)
        table = table.replace(original_line, solid_line)
        return "\n".join(
            (
                solid_line,
                self.title.center(len(solid_line)),
                table,
            )
        )


def mean_median_std(
        timepoints: list[float],
) -> tuple[datetime.timedelta, datetime.timedelta, datetime.timedelta]:
    mean_time = statistics.mean(timepoints) if len(timepoints) > 1 else None
    median_time = statistics.median(timepoints) if len(timepoints) > 1 else None
    standard_deviation = statistics.stdev(timepoints) if len(timepoints) > 1 else None

    return (
        None if mean_time is None else datetime.timedelta(seconds=mean_time),
        None if median_time is None else datetime.timedelta(seconds=median_time),
        None if standard_deviation is None else datetime.timedelta(seconds=standard_deviation)
    )


class CustomTimePeriod(TimePeriod):
    def __init__(
            self,
            first_date: datetime.date,
            last_date: datetime.date,
            days: Collection[Day],
            title="",
    ):
        super().__init__()
        self.first_date = first_date
        self.last_date = last_date
        self.title = title
        for day in days:
            if self.first_date <= day.date <= self.last_date:
                if isinstance(day, NonWorkingDay):
                    self._non_working_dates[day.date] = day
                else:
                    self._days.append(day)
