import datetime

from heath.day import Day
from heath.month import Month
from heath.project import Project
from heath.shift import Shift


def given_completed_shift_for_project_between_times(
    project: Project, start: datetime.datetime, stop: datetime.datetime
) -> Shift:
    new_shift = Shift(project, start.date())
    new_shift.start(start)
    new_shift.stop(stop)
    return new_shift


def given_completed_shift_for_date(
    shift_date: datetime.date, project: Project = None
) -> Shift:
    return given_completed_shift_for_project_between_times(
        project or Project("AnyProject"),
        datetime.datetime.combine(shift_date, datetime.time(9)),
        datetime.datetime.combine(shift_date, datetime.time(9)),
    )


def given_completed_day_for_date(
    day_date: datetime.date, project: Project = None
) -> Day:
    new_day = Day(day_date)
    new_day.add_shift(given_completed_shift_for_date(day_date, project))
    return new_day


def given_completed_month(year: int, month: int) -> Month:
    given_month = Month(year, month)
    while given_month.next_work_date:
        given_month.add_day(given_completed_day_for_date(given_month.next_work_date))
    return given_month


def given_all_day_project_on_date(
    day_date: datetime.date, all_day_project: Project
) -> Day:
    assert all_day_project.all_day
    new_day = Day(day_date)
    new_day.add_shift(Shift(all_day_project, day_date))
    return new_day
