import datetime
from textwrap import dedent

import pytest

from heath.day import Day
from heath.ledger import Ledger
from heath.month import Month
from heath.exceptions import (
    MonthDateInconsistencyError,
    MonthPreviousDayNotCompletedError,
)
from heath.project import Project
from heath.shift import Shift

from tests.utilities import (
    given_completed_day_for_date,
    given_completed_shift_for_date,
)


def test_day_can_be_added_to_month():
    # Given a month
    given_month = Month(2021, 12)

    # Given a day
    given_day = Day(datetime.date(2021, 12, 1))

    # When adding the day to the month
    given_month.add_day(given_day)

    # Then the day is kept in the month
    assert len(given_month.days) == 1
    assert given_month.days[0] is given_day


def test_date_of_day_must_be_in_month_to_be_added_to_month():
    # Given a month
    given_month = Month(2021, 12)

    # Given a day
    given_day = Day(datetime.date(2021, 11, 1))

    # Given month and day have different months
    assert given_month.month != given_day.date.month

    # When adding the day to the month
    # Then the month raises
    with pytest.raises(MonthDateInconsistencyError):
        given_month.add_day(given_day)


def test_date_of_day_must_be_in_same_year_to_be_added_to_month():
    # Given a month
    given_month = Month(2021, 12)

    # Given a day
    given_day = Day(datetime.date(2020, 12, 1))

    # Given month and day have different months
    assert given_month.year != given_day.date.year

    # When adding the day to the month
    # Then the month raises
    with pytest.raises(MonthDateInconsistencyError):
        given_month.add_day(given_day)


def test_if_first_day_skips_workday_the_month_raises():
    # Given a month
    given_month = Month(2022, 1)

    # Given day after first workday date
    given_first_workdate = datetime.date(2022, 1, 3)
    given_second_workdate = given_first_workdate.replace(
        day=given_first_workdate.day + 1
    )

    # Given a day on the date after the given date
    given_day = Day(given_second_workdate)

    # When adding the day to the month
    # Then the month raises
    with pytest.raises(MonthDateInconsistencyError):
        given_month.add_day(given_day)


def test_explicitly_skipping_workdays_can_be_ok_for_first_day_in_month():
    # Given a month
    given_month = Month(2023, 8)

    # Given day after first workday date
    given_first_workdate = datetime.date(2023, 8, 1)
    given_second_workdate = given_first_workdate.replace(
        day=given_first_workdate.day + 1
    )

    # Given a day on the date after the given date
    given_day = Day(given_second_workdate)

    # When adding the day to the month and explicitly allowing a late start
    given_month.add_day(given_day, allow_late_start=True)

    # Then the day is kept in the month
    assert len(given_month.days) == 1
    assert given_month.days[0] is given_day


def test_explicitly_skipping_workdays_can_is_not_ok_for_subsequent_days_in_month():
    # Given a month
    given_month = Month(2023, 8)

    # Given first workday
    first_work_date = datetime.date(2023, 8, 1)
    given_first_day = Day(first_work_date)

    # Given first day is completed
    given_first_day.add_shift(given_completed_shift_for_date(first_work_date))

    # Given third workday
    third_work_date = first_work_date.replace(day=first_work_date.day + 2)
    given_third_day = Day(third_work_date)

    # Given a day on the first workday has been added to month
    given_month.add_day(given_first_day)

    # When adding the third day to the month and explicitly allowing a late start
    # Then the month still raises
    with pytest.raises(MonthDateInconsistencyError):
        given_month.add_day(given_third_day, allow_late_start=True)


def test_if_additional_day_skips_a_workday_month_raises():
    # Given a month
    given_month = Month(2022, 1)

    # Given first workday
    first_work_date = datetime.date(2022, 1, 3)
    given_first_day = Day(first_work_date)

    # Given first day is completed
    given_first_day.add_shift(given_completed_shift_for_date(first_work_date))

    # Given third workday
    third_work_date = first_work_date.replace(day=first_work_date.day + 2)
    given_third_day = Day(third_work_date)

    # Given a day on the first workday has been added to month
    given_month.add_day(given_first_day)

    # When adding the third day to the month
    # Then the month raises
    with pytest.raises(MonthDateInconsistencyError):
        given_month.add_day(given_third_day)


def test_if_last_day_is_not_complete_adding_a_new_day_raises():
    # Given a month
    given_month = Month(2022, 1)

    # Given a day added to the month
    given_day = Day(given_month.next_work_date)
    given_month.add_day(given_day)

    # Given the day is not started
    assert not given_day.completed

    # When adding an additional day
    # Then the month raises
    with pytest.raises(MonthPreviousDayNotCompletedError):
        given_month.add_day(Day(given_month.next_work_date))


def test_get_number_of_days_for_all_day_project():
    # Given a project
    given_project = Project("AllDayLong", all_day=True)

    # Given a month
    given_month = Month(2022, 1)

    # Given the number of days for project is 0
    assert given_month.days_for_project("AllDayLong") == 0

    # When adding three days with the project as all day shifts
    day_1 = Day(datetime.date(2022, 1, 3))
    shift_1 = Shift(given_project, day_1.date)
    day_1.add_shift(shift_1)
    given_month.add_day(day_1)

    day_2 = Day(datetime.date(2022, 1, 4))
    shift_2 = Shift(given_project, day_2.date)
    day_2.add_shift(shift_2)
    given_month.add_day(day_2)

    day_3 = Day(datetime.date(2022, 1, 5))
    shift_3 = Shift(given_project, day_3.date)
    day_3.add_shift(shift_3)
    given_month.add_day(day_3)

    # Then the number of days for project is 3
    assert given_month.days_for_project("AllDayLong") == 3


def test_it_is_possible_to_get_day_by_date():
    # Given a specific date
    year = 2022
    month = 2
    given_date = datetime.date(year, month, 3)

    # Given a month including the date
    given_month = Month(year, month)

    # Given a comment
    given_comment = "Specific day"

    # Given multiple days added to the month, one beeing the specific date having the
    # given comment
    given_month.add_day(given_completed_day_for_date(datetime.date(year, month, 1)))
    given_month.add_day(given_completed_day_for_date(datetime.date(year, month, 2)))

    given_day = Day(given_date, given_comment)
    given_day.add_shift(given_completed_shift_for_date(given_date))
    given_month.add_day(given_day)

    given_month.add_day(Day(datetime.date(year, month, 4)))

    # When asking fo a specific day
    specific_day = given_month.get_day(given_date.day)

    # Then the correct day is retrieved
    assert specific_day is given_day
    assert specific_day.comment == given_comment


def test_month_is_aware_of_next_work_date():
    # Given a month
    given_month = Month(2022, 1)

    # Given the next working day for the month
    first_work_date = given_month.next_work_date

    # Given the next working date does not increase on its own
    assert given_month.next_work_date == first_work_date
    assert given_month.next_work_date == first_work_date
    assert given_month.next_work_date == first_work_date

    # When adding a day for that date
    given_month.add_day(Day(first_work_date))

    # Then the next working date is updated
    second_work_date = given_month.next_work_date
    assert second_work_date != first_work_date


def test_month_will_increase_next_work_day_untill_end_of_month_then_none():
    number_of_workdays_in_january_2022 = 21
    last_workday_in_january_2022 = datetime.date(2022, 1, 31)
    weekend = {6, 7}

    # Given a month
    given_month = Month(2022, 1)

    # Given the days beeing continuosly added from the next work date
    for _ in range(number_of_workdays_in_january_2022 - 1):
        given_month.add_day(given_completed_day_for_date(given_month.next_work_date))

    # When the month runs out of work dates
    assert given_month.next_work_date == last_workday_in_january_2022
    given_month.add_day(given_completed_day_for_date(given_month.next_work_date))

    # Then the month  will return None
    assert given_month.next_work_date is None

    # And all added days will only be work weekdays
    added_weekdays = {day.date.isoweekday for day in given_month.days}
    assert added_weekdays.isdisjoint(weekend)


def test_month_can_be_given_non_working_dates():
    # Given a month containing the date
    given_month = Month(2022, 1)

    # Giving the next work date for the month
    original_next_date = given_month.next_work_date

    # When adding the date as a non working date to the month
    given_month.add_non_working_date(original_next_date)

    # Then the next work date is changed
    new_next_date = given_month.next_work_date
    assert new_next_date != original_next_date

    # And the previous next working day kan be skipped
    given_month.add_day(Day(new_next_date))
    added_dates = [day.date for day in given_month.days]
    assert original_next_date not in added_dates
    assert new_next_date in added_dates


def test_it_is_possible_to_get_a_non_working_day_by_date():
    # Given a month
    given_month = Month(2022, 12)

    # Given a date in the month
    given_date = datetime.date(2022, 12, 25)

    # Given the date can not be retrieved
    assert given_month.get_day(given_date.day) is None

    # When the date is added as a non working date
    given_month.add_non_working_date(given_date)

    # Then the date can be retrieved as a date
    retrieved_day = given_month.get_day(given_date.day)
    assert retrieved_day.date == given_date


def test_non_working_days_can_have_a_comment():
    # Given a month
    given_month = Month(2022, 9)

    # Given a date in the month
    given_date = datetime.date(2022, 9, 19)

    # Given comment
    given_comment = "Talk Like a Pirate Day"

    # When adding the date as a non working day with a comment
    given_month.add_non_working_date(given_date, given_comment)

    # The comment can be read back
    assert given_month.get_day(given_date.day).comment == given_comment


@pytest.mark.parametrize(
    "given_projects, given_month_string",
    (
        ((), "\n"),
        ((), "1.\n"),
        ((), "1. # A comment.\n"),
        ((), "1. Project\n"),
        ((), "1. Project 8:00 -\n"),
        ((), "1. Project 8:00 - 17:00\n"),
        ((), "1. Project 8:00 - 17:00, Lunch 0:30\n"),
        ((), "1. Project 8:00 - 17:00, Lunch 0:30 # A comment.\n"),
        ((), "1. ProjectA 8:00 - 13:00, Lunch 0:30; ProjectB\n"),
        ((), "1. ProjectA 8:00 - 13:00, Lunch 0:30; ProjectB 13:00 - 17:00\n"),
        (
            (),
            "1. ProjectA 8:00 - 13:00, Lunch 0:30; ProjectB 13:00 - 17:00 # A comment.\n",
        ),
        (
            (),
            """\
        1. Project 8:00 - 17:00, Lunch 1:00
        2. Project 8:30 -
        """,
        ),
        (
            (),
            """\
        1. ProjectA 8:00 - 10:00; ProjectB 10:00 - 16:30, Lunch 1:00
        2. ProjectA 5:30 - 13:00 # Early bird catches the worm
        3. ProjectA 10:00 - 17:00
        4. ProjectB 8:00 - 13:00, Lunch 0:30; ProjectC 13:00 - 15:00; ProjectA 15:00 - 16:30
        7. Vacation # Finally!
        8. Vacation
        """,
        ),
    ),
)
def test_month_string_identical_roundtrip(given_month_string):
    # Given a month string
    given_month_string = dedent(given_month_string)

    # Given a ledger
    given_ledger = Ledger()

    # Given the wholeday project "Vacation"
    given_ledger.add_project(Project("Vacation", all_day=True))

    # Given the month string has been parsed
    given_ledger.parse_month(2022, 2, given_month_string)
    assert given_ledger.months

    # When serializing the month
    serialized_string = given_ledger.current_month.serialize()

    # Then the serialized string is identical to the original string
    assert serialized_string == given_month_string
