import datetime
from typing import Collection, Iterable, Optional
from heath.day import Day
from tabulate import tabulate
from heath.time_utils import pretty_duration


class TimePeriod:
    def __init__(self):
        self._days: list[Day] = []
        self._non_working_dates = {}
        self.title = ""

    @property
    def days(self) -> list[Day]:
        return self._days

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
    ) -> str:
        table = tabulate(
            [
                day.report_data(
                    include_active_day=include_active_day,
                    include_comments=include_comments,
                )
                for day in self.all_days
            ],
        )
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

        footer = "Totalt:" + duration.rjust(len(solid_line) - 7)
        return "\n".join(
            (
                solid_line,
                self.title.center(len(solid_line)),
                table,
                footer,
                solid_line,
            )
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
                self._days.append(day)
