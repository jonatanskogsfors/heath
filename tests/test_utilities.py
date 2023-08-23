import datetime
from heath.day import Day
from heath.month import Month
from heath.project import Project
from heath.shift import Shift


def given_completed_shift_for_date(shift_date: datetime.date) -> Shift:
    new_shift = Shift(Project("AnyProject"), shift_date)
    new_shift.start(datetime.datetime.combine(shift_date, datetime.time(9)))
    new_shift.stop(datetime.datetime.combine(shift_date, datetime.time(17)))
    return new_shift


def given_completed_day_for_date(day_date: datetime.date) -> Day:
    new_day = Day(day_date)
    new_day.add_shift(given_completed_shift_for_date(day_date))
    return new_day


def given_completed_month(year: int, month: int) -> Month:
    given_month = Month(year, month)
    while given_month.next_work_date:
        given_month.add_day(given_completed_day_for_date(given_month.next_work_date))
    return given_month
