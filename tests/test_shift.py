from datetime import datetime, date, timedelta

import pytest

from heath.shift import Shift
from heath.project import Project
from heath.exceptions import ShiftConsistencyError, ShiftError


def test_create_a_minimal_shift():
    # Given a date
    given_date = date(2021, 12, 6)
    given_project = Project("ProjectX")

    # When creating a shift
    new_shift = Shift(given_project, given_date)

    # Then project and date can be read
    assert new_shift.project is given_project
    assert new_shift.date == given_date


def test_add_start_time_to_shift():
    # Given a shift without start
    given_shift = Shift(Project("ProjectX"), date(2021, 12, 6))
    assert given_shift.start_time is None

    # Given a start time
    given_start_time = datetime(2021, 12, 6, 8, 0)

    # When the shift is started
    given_shift.start(given_start_time)

    # Then it has a start time
    assert given_shift.start_time == given_start_time


@pytest.mark.parametrize(
    "given_start_time,given_read_time,expected_duration",
    [
        (
            datetime(2021, 12, 6, 8),
            datetime(2021, 12, 6, 7),
            timedelta(hours=0),
        ),
        (
            datetime(2021, 12, 6, 8),
            datetime(2021, 12, 6, 8),
            timedelta(hours=0),
        ),
        (
            datetime(2021, 12, 6, 8),
            datetime(2021, 12, 5, 18),
            timedelta(hours=0),
        ),
        (
            datetime(2021, 12, 6, 8),
            datetime(2021, 12, 6, 9),
            timedelta(hours=1),
        ),
        (
            datetime(2021, 12, 6, 8, 30),
            datetime(2021, 12, 6, 10, 31),
            timedelta(hours=2, minutes=1),
        ),
        (
            datetime(2021, 12, 6, 8, 4, 1),
            datetime(2021, 12, 7, 18, 45, 59),
            timedelta(days=1, hours=10, minutes=41, seconds=58),
        ),
    ],
)
def test_duration_at_time_for_started_shift(
    given_start_time, given_read_time, expected_duration
):
    # Given a shift without start and thus without duration
    given_shift = Shift(Project("ProjectX"), date(2021, 12, 6))
    assert given_shift.start_time is None
    assert given_shift.duration == timedelta()

    # When the shift is started
    given_shift.start(given_start_time)

    # Then the duration_at for a given test time is as expected
    assert given_shift.duration_at(given_read_time) == expected_duration

    # And the duration is still 0
    assert given_shift.duration == timedelta()


@pytest.mark.parametrize(
    "given_start_time,given_lunch_duration, given_read_time, expected_duration",
    [
        (
            datetime(2021, 12, 6, 8),
            timedelta(),
            datetime(2021, 12, 6, 8, 0, 1),
            timedelta(seconds=1),
        ),
        (
            datetime(2021, 12, 6, 9),
            timedelta(hours=1),
            datetime(2021, 12, 6, 17),
            timedelta(hours=7),
        ),
        (
            datetime(2021, 12, 6, 8),
            timedelta(minutes=30),
            datetime(2021, 12, 6, 15, 45),
            timedelta(hours=7, minutes=15),
        ),
        (
            datetime(2021, 12, 6, 22, 15),
            timedelta(hours=1, minutes=5),
            datetime(2021, 12, 7, 5, 10),
            timedelta(hours=5, minutes=50),
        ),
        (
            datetime(2021, 12, 6, 0),
            timedelta(days=1, hours=1, minutes=1, seconds=1),
            datetime(2021, 12, 8, 2, 2, 2),
            timedelta(days=1, hours=1, minutes=1, seconds=1),
        ),
    ],
)
def test_duration_at_time_for_started_shift_with_lunch(
    given_start_time, given_lunch_duration, given_read_time, expected_duration
):
    # Given a shift without start and thus without duration
    given_shift = Shift(Project("ProjectX"), date(2021, 12, 6))
    assert given_shift.start_time is None
    assert given_shift.duration == timedelta()

    # When the shift is started and lunch is taken
    given_shift.start(given_start_time)
    given_shift.lunch(given_lunch_duration)

    # Then the duration_at for a given test time is as expected
    assert given_shift.duration_at(given_read_time) == expected_duration

    # And the duration is still 0
    assert given_shift.duration == timedelta()


@pytest.mark.parametrize(
    "given_start_time,given_end_time,expected_duration",
    [
        (
            datetime(2021, 12, 6, 8),
            datetime(2021, 12, 6, 8, 0, 1),
            timedelta(seconds=1),
        ),
        (
            datetime(2021, 12, 6, 9),
            datetime(2021, 12, 6, 17),
            timedelta(hours=8),
        ),
        (
            datetime(2021, 12, 6, 8),
            datetime(2021, 12, 6, 15, 30),
            timedelta(hours=7, minutes=30),
        ),
        (
            datetime(2021, 12, 6, 22, 15),
            datetime(2021, 12, 7, 5, 10),
            timedelta(hours=6, minutes=55),
        ),
        (
            datetime(2021, 12, 6, 0),
            datetime(2021, 12, 7, 1, 1, 1),
            timedelta(days=1, hours=1, minutes=1, seconds=1),
        ),
    ],
)
def test_duration_for_completed_shift(
    given_start_time, given_end_time, expected_duration
):
    # Given a shift without start and thus without duration
    given_shift = Shift(Project("ProjectX"), date(2021, 12, 6))
    assert given_shift.start_time is None
    assert given_shift.duration == timedelta()

    # Given the shift is started
    given_shift.start(given_start_time)
    assert given_shift.duration == timedelta()

    # When the the shift is stopped
    given_shift.stop(given_end_time)

    # Then the duration is as expected
    assert given_shift.duration == expected_duration


@pytest.mark.parametrize(
    "given_start_time,given_lunch_duration,given_end_time,expected_duration",
    [
        (
            datetime(2021, 12, 6, 8),
            timedelta(),
            datetime(2021, 12, 6, 8, 0, 1),
            timedelta(seconds=1),
        ),
        (
            datetime(2021, 12, 6, 9),
            timedelta(hours=1),
            datetime(2021, 12, 6, 17),
            timedelta(hours=7),
        ),
        (
            datetime(2021, 12, 6, 8),
            timedelta(minutes=30),
            datetime(2021, 12, 6, 15, 45),
            timedelta(hours=7, minutes=15),
        ),
        (
            datetime(2021, 12, 6, 22, 15),
            timedelta(hours=1, minutes=15),
            datetime(2021, 12, 7, 5, 10),
            timedelta(hours=5, minutes=40),
        ),
        (
            datetime(2021, 12, 6, 0),
            timedelta(hours=1, minutes=1, seconds=1),
            datetime(2021, 12, 7, 2, 2, 2),
            timedelta(days=1, hours=1, minutes=1, seconds=1),
        ),
    ],
)
def test_duration_for_completed_shift_with_lunch(
    given_start_time, given_lunch_duration, given_end_time, expected_duration
):
    # Given a shift without start and thus without duration
    given_shift = Shift(Project("ProjectX"), date(2021, 12, 6))
    assert given_shift.start_time is None
    assert given_shift.duration == timedelta()

    # Given the shift is started and lunch is taken
    given_shift.start(given_start_time)
    given_shift.lunch(given_lunch_duration)
    assert given_shift.duration == timedelta()

    # When the the shift is stopped
    given_shift.stop(given_end_time)

    # Then the duration is as expected
    assert given_shift.duration == expected_duration


def test_shift_with_start_and_stop_is_marked_complete():
    # Given a shift
    given_shift = Shift(Project("AnyProject"), date(2021, 12, 10))

    # Given shift is not started and not completed
    assert given_shift.start_time is None
    assert not given_shift.completed

    # When shift is started, it is still not completed
    given_shift.start(datetime(2021, 12, 10, 8))
    assert not given_shift.completed

    # When shift is stopped
    given_shift.stop(datetime(2021, 12, 10, 8, 1))

    # Then shift is marked completed
    assert given_shift.completed


def test_shift_is_started_if_there_is_a_start_time():
    # Given a shift
    given_shift = Shift(Project("AnyProject"), date(2022, 1, 24))

    # Given shift has no start tiome
    assert given_shift.start_time is None

    # Given shift is not started
    assert not given_shift.started

    # When shifts is given a start time
    given_shift.start(datetime(2022, 1, 24, 23, 59))

    # Then shift is started
    assert given_shift.started


def test_shift_must_be_started_to_have_a_lunch():
    # Given shift
    given_shift = Shift(Project("AnyProject"), date(2022, 1, 24))

    # Given shift is not started
    assert not given_shift.started

    # Given a lunch duration
    given_lunch_duration = timedelta(minutes=1)

    # When giving shift a lunch
    # Then shift raises
    with pytest.raises(ShiftConsistencyError):
        given_shift.lunch(given_lunch_duration)

    # And if shift is started
    given_shift.start(datetime(2022, 1, 24, 11))

    # Then lunch is accepted
    given_shift.lunch(given_lunch_duration)


def test_shift_must_be_started_to_have_a_stop():
    # Given shift
    given_shift = Shift(Project("AnyProject"), date(2022, 1, 24))

    # Given shift is not started
    assert not given_shift.started

    # Given a start time and a stop time
    given_start_time = datetime(2022, 1, 24, 8)
    given_stop_time = datetime(2022, 1, 24, 16)

    # When stopping shift
    # Then shift raises
    with pytest.raises(ShiftConsistencyError):
        given_shift.stop(given_stop_time)

    # And when shift is started
    given_shift.start(given_start_time)

    # Then shift can be stopped
    given_shift.stop(given_stop_time)

    # And there is a duration
    assert given_shift.duration == given_stop_time - given_start_time


def test_stop_time_must_be_later_than_start_plus_lunch():
    # Given a shift
    given_shift = Shift(Project("AnyProject"), date(2022, 1, 24))

    # Given a start time, a lunch duration and a stop time
    given_start_time = datetime(2022, 1, 24, 11, 30)
    given_lunch_duration = timedelta(hours=1)
    given_early_stop_time = datetime(2022, 1, 24, 12, 29)
    given_late_stop_time = datetime(2022, 1, 24, 12, 30)

    # Given shift is started and have a lunch
    given_shift.start(given_start_time)
    given_shift.lunch(given_lunch_duration)

    # When stop time is before start plus lunch
    # Then shift raises
    with pytest.raises(ShiftConsistencyError):
        given_shift.stop(given_early_stop_time)

    # And if stop time is same as start plus lunch stop is accepted
    given_shift.stop(given_late_stop_time)

    # And there is a duration
    assert given_shift.duration == given_late_stop_time - (
        given_start_time + given_lunch_duration
    )


@pytest.mark.parametrize(
    "given_start_time, given_stop_time, expected_duration",
    [
        (
            datetime(2022, 1, 24, 16),
            datetime(2022, 1, 25, 0, 5),
            timedelta(hours=8, minutes=5),
        ),
        (
            datetime(2022, 1, 3, 0),
            datetime(2022, 1, 4, 23, 59, 59),
            timedelta(days=1, hours=23, minutes=59, seconds=59),
        ),
        (
            datetime(2020, 2, 28, 18),
            datetime(2020, 2, 29, 2),
            timedelta(hours=8),
        ),
    ],
)
def test_stop_time_on_day_after_is_ok(
    given_start_time, given_stop_time, expected_duration
):
    # Given a shift
    given_shift = Shift(Project("AnyProject"), given_start_time.date())

    # Given the shift is started
    given_shift.start(given_start_time)

    # Given the stop time is on the next calendar day
    start_date = datetime.combine(given_start_time.date(), datetime.min.time())
    stop_date = datetime.combine(given_stop_time.date(), datetime.min.time())
    assert stop_date - start_date == timedelta(days=1)

    # When shift is stopped on the next day
    given_shift.stop(given_stop_time)

    # Then the shift is completed
    assert given_shift.completed

    # And the durations is correct
    assert given_shift.duration == expected_duration


@pytest.mark.parametrize(
    "given_start_time, given_stop_time",
    [
        (datetime(2022, 1, 3, 8), datetime(2023, 1, 3, 17)),
        (datetime(2022, 1, 24, 8), datetime(2022, 1, 26, 0, 0, 1)),
        (datetime(2020, 2, 28, 20), datetime(2020, 3, 1, 1)),
    ],
)
def test_stop_time_on_date_to_long_out_raises(given_start_time, given_stop_time):
    # Given a shift
    given_shift = Shift(Project("AnyProject"), given_start_time.date())

    # Given the shift is started
    given_shift.start(given_start_time)

    # Given the stop time is more than a calendar day off
    start_date = datetime.combine(given_start_time.date(), datetime.min.time())
    stop_date = datetime.combine(given_stop_time.date(), datetime.min.time())
    assert stop_date - start_date > timedelta(days=1)

    # When shift is stopped on a bad date
    # Then shift raises
    with pytest.raises(ShiftConsistencyError):
        given_shift.stop(given_stop_time)


def test_all_day_shift_will_raise_if_started():
    # Given an all day project
    given_project = Project("AllDayProject", all_day=True)

    # Given a shift for the project
    whenever = datetime.now()
    given_shift = Shift(given_project, whenever.date())

    # When starting the project
    # Then the shift raises
    with pytest.raises(ShiftError):
        given_shift.start(whenever)
