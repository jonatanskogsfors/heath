from ast import parse
from calendar import weekday
import configparser
import re
import datetime
from heath import exceptions

from heath.month import Month
from heath.day import Day
from heath.project import Project
from heath.shift import Shift
from heath.time_period import CustomTimePeriod

COMMENT_PATTERN = re.compile("#.*")
DAY_PATTERN = re.compile("(\d+)\.\s*(.+)?")
SHIFT_PATTERN = re.compile(
    "(\w+)(?:\s+(?:(\d+:\d+)(?:\s*-\s*(\d+:\d+)?)?\s*(?:,\s*Lunch\s*(\d+:\d+)?)?)?)?",
    flags=re.IGNORECASE,
)


class Ledger:
    def __init__(self) -> None:
        self._months = []
        self._projects = {}
        self._non_working_dates = {}

    @property
    def months(self) -> list[Month]:
        return self._months

    @property
    def projects(self) -> dict[str, Project]:
        return self._projects

    @property
    def current_year(self) -> CustomTimePeriod:
        today = datetime.date.today()
        return self.get_year(today.year)

    @property
    def current_month(self) -> Month:
        return self.months[-1]

    @property
    def current_week(self) -> CustomTimePeriod:
        today = datetime.date.today()
        return self.get_week(today.isocalendar().week, today.year)

    @property
    def last_day(self) -> Day:
        return self.current_month.last_day

    @property
    def today(self) -> Day:
        today = datetime.date.today()
        return self.get_day(today.day, today.month, today.year)

    @property
    def current_shift(self):
        return self.today.current_shift

    @property
    def next_work_date(self) -> datetime.date:
        if self.current_month.next_work_date:
            return self.current_month.next_work_date

        next_month = self.current_month.month + 1
        next_month_year = self.current_month.year + (next_month > 12)
        next_month = (next_month - 1) % 12 + 1
        temporary_month = Month(next_month_year, next_month)
        for date, desciption in self.non_working_dates.get(next_month_year, {}).items():
            if date.month == next_month:
                temporary_month.add_non_working_date(date, desciption)
        return temporary_month.next_work_date

    def get_day(self, day_number, month_number=None, year=None) -> Day:
        month = self.get_month(month_number, year)
        return month.get_day(day_number)

    def get_week(self, week_number, year=None) -> CustomTimePeriod:
        year = year or datetime.date.today().year
        week_string = f"{year}-{week_number:02}"
        monday = datetime.datetime.strptime(f"{week_string}-1", "%Y-%W-%u")
        sunday = datetime.datetime.strptime(f"{week_string}-7", "%Y-%W-%u")

        title = f"Vecka {week_number}, {year}"

        return CustomTimePeriod(
            monday.date(),
            sunday.date(),
            [day for month in self.months for day in month.all_days],
            title=title,
        )

    def get_custom_time_period(
        self, start_date: datetime.date, end_date: datetime.date
    ):
        return CustomTimePeriod(
            start_date,
            end_date,
            [day for month in self.months for day in month.all_days],
            title=f"{start_date.isoformat()} - {end_date.isoformat()}",
        )

    def get_month(self, month_number, year=None) -> Month | None:
        year = year or datetime.date.today().year
        month_number = month_number or datetime.date.today().month

        month = [
            month
            for month in self.months
            if month.year == year and month.month == month_number
        ]
        return month[0] if month else None

    def get_year(self, year) -> CustomTimePeriod | None:
        year = year or datetime.date.today().year
        title = str(year)
        new_years_day = datetime.date(year, 1, 1)
        new_years_eve = datetime.date(year, 12, 31)

        return CustomTimePeriod(
            new_years_day,
            new_years_eve,
            [day for month in self.months for day in month.all_days],
            title=title,
        )

    @property
    def non_working_dates(self) -> dict[int, dict[datetime.date, str]]:
        return self._non_working_dates

    def add_day(self, new_day: Day):
        if new_day.date.month != self.current_month.month:
            self.add_month(Month(new_day.date.year, new_day.date.month))
        first_day = len(self.months) == 1 and not self.current_month.days
        self.current_month.add_day(new_day, allow_late_start=first_day)

    def add_month(self, month: Month):
        for date, desciption in self.non_working_dates.get(month.year, {}).items():
            if date.month == month.month:
                month.add_non_working_date(date, desciption)
        self._months.append(month)
        self._months.sort(key=lambda m: f"{m.year}{m.month:02}")

    def add_non_working_date(self, date: datetime.date, description: str):
        for month in self.months:
            if (month.year, month.month) == (date.year, date.month):
                raise exceptions.MonthDateInconsistencyError(
                    "Month for non working date already added to ledger. "
                    f"{date}: {description}"
                )

        if date.year not in self._non_working_dates:
            self._non_working_dates[date.year] = {}
        self._non_working_dates[date.year][date] = description

    def add_project(self, project: Project):
        self._projects[project.key] = project

    def parse_day(self, year: int, month: int, day_string: str) -> None:
        day_components = day_string.split("#", 1)
        day_data = day_components[0]
        day_comment = day_components[1].strip() if len(day_components) == 2 else None

        if day_match := DAY_PATTERN.match(day_data):
            date = datetime.date(year, month, int(day_match.group(1)))

            day = Day(date, day_comment)
            for shift_matches in SHIFT_PATTERN.findall(day_match.group(2) or ""):
                (project_key, start_time, stop_time, lunch_duration) = shift_matches
                project = self.get_project(project_key)
                shift = Shift(project, date)
                if start_time:
                    time = datetime.time(*map(int, start_time.split(":")))
                    shift.start(datetime.datetime.combine(date, time))

                if stop_time:
                    time = datetime.time(*map(int, stop_time.split(":")))
                    shift.stop(datetime.datetime.combine(date, time))

                if lunch_duration:
                    hours, minutes = map(int, lunch_duration.split(":"))
                    shift.lunch(datetime.timedelta(hours=hours, minutes=minutes))

                day.add_shift(shift)
            self.add_day(day)

    def get_project(self, project_key: str, all_day=False):
        try:
            project = self.projects[project_key]
        except KeyError:
            raise exceptions.UnknownProjectError(f"Project {project_key} is not known.")
        if all_day and not project.all_day:
            raise exceptions.ProjectError(
                f"Project {project_key} is not an all day project."
            )

        return project

    def parse_month(self, year, month, month_string: str) -> None:
        new_month = Month(year, month)
        self.add_month(new_month)

        for day_string in month_string.splitlines():
            self.parse_day(year, month, day_string)

    def parse_year(self, year: int, year_string: str) -> None:
        year_string_without_comments = COMMENT_PATTERN.sub("", year_string)

        non_working_dates = {}
        for date_string, description in (
            line.split(":")
            for line in year_string_without_comments.splitlines()
            if line.strip()
        ):
            date = datetime.date.fromisoformat(date_string.strip())
            if date.year != year:
                raise exceptions.DateInconsistencyError(
                    "Non working date in year file is outside year. "
                    f"{date} not in {year}"
                )
            non_working_dates[date] = description.strip()

        for date, description in non_working_dates.items():
            self.add_non_working_date(date, description)

    def parse_projects(self, project_string: str) -> None:
        projects_config = configparser.ConfigParser()
        projects_config.read_string(project_string)
        for project_key in projects_config.sections():
            project_data = projects_config[project_key]
            new_project = Project(
                project_key,
                project_data["name"],
                description=project_data.get("description"),
                all_day=project_data.getboolean("all_day"),
            )
            self.add_project(new_project)
