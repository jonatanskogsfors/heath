import calendar
import datetime
from typing import Optional

from heath.day import Day, NonWorkingDay
from heath.exceptions import (
    MonthDateInconsistencyError,
    MonthPreviousDayNotCompletedError,
)
from heath.time_period import TimePeriod


class Month(TimePeriod):
    def __init__(self, year: int, month: int) -> None:
        super().__init__()
        self.year = year
        self.month = month
        self.title = f"{calendar.month_name[self.month]} {self.year}".capitalize()

    @property
    def key(self) -> str:
        return f"{self.year}-{self.month:02}"

    @property
    def next_work_date(self) -> Optional[datetime.date]:
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        first_potential_day = self.days[-1].date.day + 1 if self.days else 1
        for day_number in range(first_potential_day, days_in_month + 1):
            potential_date = datetime.date(self.year, self.month, day_number)
            if potential_date in self._non_working_dates:
                continue
            if potential_date.isoweekday() < 6:
                return potential_date
        return None

    def worked_hours_for_project(self, project_name: str):
        return sum(
            (
                shift.duration
                for day in self.days
                for shift in day.shifts
                if shift.project.key == project_name
            ),
            start=datetime.timedelta(),
        )

    def days_for_project(self, project_name: str):
        return len(
            [day for day in self.days if day.all_day_project_name == project_name]
        )

    def add_day(self, new_day: Day):
        if any(not day.completed for day in self._days):
            raise MonthPreviousDayNotCompletedError(
                "All previous days are not completed."
            )

        if new_day.date.year != self.year or new_day.date.month != self.month:
            raise MonthDateInconsistencyError(
                "Added day has wrong year or month. "
                f"{new_day.date.year}-{new_day.date.month} != {self.year}-{self.month}"
            )

        if new_day.date > self.next_work_date:
            raise MonthDateInconsistencyError(
                f"Added day skips a workday ({new_day.date} > {self.next_work_date})"
            )

        self._days.append(new_day)

    def add_non_working_date(
        self, non_working_date: datetime.date, comment: str = None
    ):
        non_working_day = NonWorkingDay(non_working_date, comment)
        self._non_working_dates[non_working_date] = non_working_day

    def serialize(self) -> str:
        return "\n".join(str(day) for day in self.days) + "\n"
