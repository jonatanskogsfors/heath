import datetime
import pytest

from heath.day import Day
from heath.shift import Shift
from heath.project import Project
from heath.exceptions import DayError, DayInconsistencyError


def test_day_must_be_initialized_with_date():
    # When initialing day without a date
    # Then an exception in thrown
    with pytest.raises(DayError):
        Day(None)


def test_minimal_day():
    # Given a date
    given_date = datetime.date(2021, 12, 6)

    # When creating a day
    day = Day(given_date)

    # Then the day has the date
    assert day.date == given_date

    # And its duration is 0
    assert day.worked_hours == datetime.timedelta()


def test_day_can_have_comment():
    # Given a date
    given_date = datetime.date(2022, 1, 24)

    # Given a comment
    given_comment = "Hello World!"

    # When creating a day with comment
    day = Day(given_date, given_comment)

    # Then the comment is saved
    assert day.comment == given_comment


def test_when_adding_a_shift_the_duration_is_equal_to_shift():
    # Given a date
    given_date = datetime.date(2021, 12, 6)

    # Given a shift with a duration
    given_shift = Shift(Project("ProjectX"), given_date)
    given_shift.start(datetime.datetime.combine(given_date, datetime.time(9)))
    given_shift.stop(datetime.datetime.combine(given_date, datetime.time(17)))
    assert given_shift.duration > datetime.timedelta()

    # Given a day
    given_day = Day(given_date)
    assert given_day.worked_hours != given_shift.duration

    # When adding the shift to the day
    given_day.add_shift(given_shift)

    # Then the day has the same duration as the shift
    assert given_day.worked_hours == given_shift.duration


def test_when_adding_multiple_shift_the_duration_is_equal_to_sum_of_shift_durations():
    # Given a date
    given_date = datetime.date(2021, 12, 6)

    # Given two shifts with durations
    given_shift_1 = Shift(Project("ProjectX"), given_date)
    given_shift_1.start(datetime.datetime.combine(given_date, datetime.time(9)))
    given_shift_1.stop(datetime.datetime.combine(given_date, datetime.time(14)))
    assert given_shift_1.duration > datetime.timedelta()

    given_shift_2 = Shift(Project("ProjectX"), given_date)
    given_shift_2.start(datetime.datetime.combine(given_date, datetime.time(14)))
    given_shift_2.stop(datetime.datetime.combine(given_date, datetime.time(17)))
    assert given_shift_2.duration > datetime.timedelta()

    # Given a day
    given_day = Day(given_date)
    assert given_day.worked_hours != given_shift_1.duration + given_shift_2.duration

    # When adding the shifts to the day
    given_day.add_shift(given_shift_1)
    given_day.add_shift(given_shift_2)

    # Then the day has the same duration as the sum of the shifts durations
    assert given_day.worked_hours == given_shift_1.duration + given_shift_2.duration


def test_added_shift_must_have_same_date_as_day():
    # Given two dates
    given_first_date = datetime.date(2021, 12, 10)
    given_second_date = datetime.date(2021, 12, 11)

    # Given a day
    given_day = Day(given_first_date)

    # Given a shift
    given_shift = Shift(Project("AnyProject"), given_second_date)

    # Given the shift and the date have different dates
    assert given_shift.date != given_day.date

    # When adding the shift to the day
    # Then the day raises
    with pytest.raises(DayInconsistencyError):
        given_day.add_shift(given_shift)


def test_added_shift_cant_overlap_with_previous_shift():
    # Given a project
    given_project = Project("AnyProject")

    # Given a date
    given_date = datetime.date(2021, 12, 10)

    # Given a day
    given_day = Day(given_date)

    # Given two shifts
    given_first_shift = Shift(given_project, given_date)
    given_second_shift = Shift(given_project, given_date)

    # Given the shifts are overlapping
    given_first_shift.start(datetime.datetime(2021, 12, 10, 8))
    given_first_shift.stop(datetime.datetime(2021, 12, 10, 13, 0, 1))

    given_second_shift.start(datetime.datetime(2021, 12, 10, 13))
    given_second_shift.stop(datetime.datetime(2021, 12, 10, 17))

    # Given the first shift is added to the day
    given_day.add_shift(given_first_shift)

    # When adding the second shift to the day
    # Then the shift raises
    with pytest.raises(DayInconsistencyError):
        given_day.add_shift(given_second_shift)


def test_project_durations_sum_completed_shifts_per_project():
    # Given three projects
    given_project_a = Project("A")
    given_project_b = Project("B")
    given_project_c = Project("C")

    # Given a date
    given_date = datetime.date(2023, 9, 5)

    # Given a day
    given_day = Day(given_date)

    # Given two completed shifts for one of the projects
    completed_shift_1 = Shift(given_project_a, given_date)
    completed_shift_1.start(datetime.datetime(2023, 9, 5, 8))
    completed_shift_1.stop(datetime.datetime(2023, 9, 5, 9))
    given_day.add_shift(completed_shift_1)

    completed_shift_2 = Shift(given_project_a, given_date)
    completed_shift_2.start(datetime.datetime(2023, 9, 5, 9))
    completed_shift_2.stop(datetime.datetime(2023, 9, 5, 10))
    given_day.add_shift(completed_shift_2)

    # Given one completed shift for another project
    completed_shift_3 = Shift(given_project_b, given_date)
    completed_shift_3.start(datetime.datetime(2023, 9, 5, 10))
    completed_shift_3.stop(datetime.datetime(2023, 9, 5, 11))
    given_day.add_shift(completed_shift_3)

    # Given an incomplete shift for the third project
    incomplete_shift = Shift(given_project_c, given_date)
    incomplete_shift.start(datetime.datetime(2023, 9, 5, 12))
    given_day.add_shift(incomplete_shift)

    # When calling project_durations
    project_durations = given_day.project_durations()

    # Then only the projects for the completed shifts are included
    assert given_project_a.key in project_durations
    assert given_project_b.key in project_durations
    assert given_project_c.key not in project_durations

    # And the projects have the expected durations
    assert project_durations[given_project_a.key] == datetime.timedelta(hours=2)
    assert project_durations[given_project_b.key] == datetime.timedelta(hours=1)
