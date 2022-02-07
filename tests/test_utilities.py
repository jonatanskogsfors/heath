import datetime
from heath.day import Day
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
