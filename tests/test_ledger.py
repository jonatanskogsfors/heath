from datetime import date, datetime, time, timedelta
from pydoc import describe
from textwrap import dedent

import pytest

from heath import exceptions
from heath.ledger import Ledger
from heath.month import Month
from heath.project import Project
from tests import test_utilities


def test_day_with_no_shifts_can_be_parsed_from_string():
    # Given a year, month and day
    given_year = 2021
    given_month_number = 12
    given_day = 1

    # Given a month without days
    given_month = Month(given_year, given_month_number)
    assert len(given_month.days) == 0

    # Given a string expressing a day with no shifts
    given_day_string = f"{given_day}."

    # Given a ledger with the month
    given_ledger = Ledger()
    given_ledger.add_month(given_month)

    # When parsing the string
    given_ledger.parse_day(given_year, given_month_number, given_day_string)

    # Then a day is added to the month
    assert len(given_month.days) == 1

    # And the added day has the correct date
    assert given_month.days[0].date == date(given_year, given_month_number, given_day)

    # And the day has no shifts
    assert len(given_month.days[0].shifts) == 0


def test_day_with_unstarted_shift_can_be_parsed_from_string():
    # Given a project name
    given_project_key = "SpecificProject"
    given_project = Project(given_project_key)

    # Given a year, month and day
    given_year = 2021
    given_month_number = 12
    given_day = 1

    # Given a month without days
    given_month = Month(given_year, given_month_number)
    assert len(given_month.days) == 0

    # Given a string expressing a day with no shifts
    given_day_string = f"{given_day}. {given_project_key}"

    # Given a ledger with the project and the month
    given_ledger = Ledger()
    given_ledger.add_month(given_month)
    given_ledger.add_project(given_project)

    # When parsing the string
    given_ledger.parse_day(given_year, given_month_number, given_day_string)

    # Then a day is added to the month
    assert len(given_month.days) == 1

    # And the added day has the correct date
    actual_day = given_month.days[0]
    assert actual_day.date == date(given_year, given_month_number, given_day)

    # And the day has one shift
    assert len(given_month.days[0].shifts) == 1
    created_shift = given_month.days[0].shifts[0]

    # And the shift has the correct project
    assert created_shift.project.key == given_project_key

    # Without start, lunch and stop
    assert created_shift.start_time is None
    assert created_shift.lunch_duration == timedelta()
    assert created_shift.stop_time is None

    # And the information is propagated to the day
    assert actual_day.worked_hours == timedelta()
    assert len(actual_day.projects) == 1
    assert actual_day.projects[0].key == given_project_key

    # And the information is propagated to the month
    assert given_month.worked_hours == timedelta()
    assert len(given_month.projects) == 1
    assert given_month.projects[0].key == given_project_key

    # And the information is propagated to the ledger
    assert len(given_ledger.projects) == 1
    assert given_project_key in given_ledger.projects


def test_day_with_comment_can_be_parsed():
    # Given a year, month and day
    given_year = 2021
    given_month_number = 12

    # Given a month without days
    given_month = Month(given_year, given_month_number)
    assert len(given_month.days) == 0

    # Given a project
    given_project_key = "Work"
    given_project = Project(given_project_key)

    # Given a ledger with the project and a month
    given_ledger = Ledger()
    given_ledger.add_project(given_project)
    given_ledger.add_month(given_month)

    # Given a comment
    given_comment = "What a way to make a living!"

    # Given a string expressing a day with the comment
    given_day_string = f"1. {given_project_key} 9:00 - 17:00 # {given_comment}"

    # When parsing the string
    given_ledger.parse_day(given_year, given_month_number, given_day_string)

    # Then the comment is preserved
    parsed_day = given_ledger.current_month.days[-1]
    assert parsed_day.comment == given_comment


@pytest.mark.parametrize(
    "given_day_string, expected_day, expected_project, expected_start, expected_stop, expected_lunch, expected_duration",
    [
        (
            "1. Project1",
            1,
            "Project1",
            None,
            None,
            timedelta(),
            timedelta(),
        ),
        (
            "1. Project2 8:00",
            1,
            "Project2",
            time(8),
            None,
            timedelta(),
            timedelta(),
        ),
        (
            "1. Project3 7:30,",
            1,
            "Project3",
            time(7, 30),
            None,
            timedelta(),
            timedelta(),
        ),
        (
            "1. MonkeyBusiness 8:15 -, Lunch",
            1,
            "MonkeyBusiness",
            time(8, 15),
            None,
            timedelta(),
            timedelta(),
        ),
        (
            "1. ACME 8:30 , Lunch 0:50",
            1,
            "ACME",
            time(8, 30),
            None,
            timedelta(minutes=50),
            timedelta(),
        ),
        (
            "1. Something 9:00 - 17:00",
            1,
            "Something",
            time(9),
            time(17),
            timedelta(),
            timedelta(hours=8),
        ),
        (
            "1. SomethingElse 8:00 - 16:00, Lunch 0:30",
            1,
            "SomethingElse",
            time(8),
            time(16),
            timedelta(minutes=30),
            timedelta(hours=7, minutes=30),
        ),
    ],
)
def test_various_day_strings_with_one_shift(
    given_day_string,
    expected_day,
    expected_project,
    expected_start,
    expected_stop,
    expected_lunch,
    expected_duration,
):
    # Given a year and a month
    given_year = 2021
    given_month_number = 12

    expected_date = date(given_year, given_month_number, expected_day)
    if expected_start:
        expected_start = datetime.combine(expected_date, expected_start)

    if expected_stop:
        expected_stop = datetime.combine(expected_date, expected_stop)

    # Given a month without days
    given_month = Month(given_year, given_month_number)
    assert len(given_month.days) == 0

    # Given ledger with the given month and the expected project
    given_ledger = Ledger()
    given_ledger.add_month(given_month)
    given_ledger.add_project(Project(expected_project))

    # When parsing the string
    given_ledger.parse_day(given_year, given_month_number, given_day_string)

    # Then a day is added to the month
    assert len(given_month.days) == 1

    # And the added day has the correct date
    parsed_day = given_month.days[0]
    assert parsed_day.date == expected_date

    # And the day has one shift
    assert len(parsed_day.shifts) == 1
    parsed_shift = parsed_day.shifts[0]

    # And the shift has the expected project, start, lunch, stop and duration
    assert parsed_shift.start_time == expected_start
    assert parsed_shift.lunch_duration == expected_lunch
    assert parsed_shift.stop_time == expected_stop
    assert parsed_shift.duration == expected_duration

    # And the information is propagated to the day
    assert parsed_day.worked_hours == expected_duration
    assert len(parsed_day.projects) == 1
    assert parsed_day.projects[0].key == expected_project

    # And the information is propagated to the month
    assert given_month.worked_hours == expected_duration
    assert len(given_month.projects) == 1
    assert given_month.projects[0].key == expected_project

    # And the information is propagated to the ledger
    assert len(given_ledger.projects) == 1
    assert expected_project in given_ledger.projects


def test_unknown_projects_are_rejected():
    # Given a ledger
    given_ledger = Ledger()

    # Given there are no projects
    assert len(given_ledger.projects) == 0
    
    # Given a day string with a project
    given_day_string = f"1. ProjectX 8:00 - 17:00. Lunch 1:00"

    # When parsing the string
    # Then the ledger raises
    with pytest.raises(exceptions.UnknownProjectError):
        given_ledger.parse_day(2023, 8, given_day_string)


def test_known_projects_are_used():
    # Given a ledger
    given_ledger = Ledger()

    # Given a Project known to the ledger
    given_project_name = "ProjectX"
    given_project = Project(given_project_name)
    given_ledger.add_project(given_project)

    # Given a month known to the ledger
    given_month = Month(2021, 12)
    given_ledger.add_month(given_month)

    # Given a day string with a shift
    given_day_string = f"1. {given_project_name} 8:00 - 17:00, Lunch 1:00"

    # When parsing the string
    given_ledger.parse_day(given_month.year, given_month.month, given_day_string)

    # Then a day is created with
    assert len(given_month.days) == 1
    actual_day = given_month.days[0]

    # And the day has a shift
    assert len(actual_day.shifts) == 1
    actual_shift = actual_day.shifts[0]

    # And the shift, the day, the month and the ledger all point to the same project
    assert actual_shift.project is given_project
    assert actual_day.projects[0] is given_project
    assert given_month.projects[0] is given_project
    assert given_ledger.projects[given_project_name] is given_project


@pytest.mark.parametrize(
    "given_projects, given_day_string, expected_day, expected_shifts, expected_worked_hours",
    [
        (
            ("Project1", "Project2"),
            "1. Project1 8:00 - 13:00, Lunch 0:30; Project2",
            1,
            (
                (
                    "Project1",
                    time(8),
                    time(13),
                    timedelta(minutes=30),
                    timedelta(hours=4, minutes=30),
                ),
                ("Project2", None, None, timedelta(), timedelta()),
            ),
            timedelta(hours=4, minutes=30),
        ),
        (
            ("Project1", "Project2"),
            "1. Project1 8:00 - 13:00, Lunch 0:30; Project2 13:00",
            1,
            (
                (
                    "Project1",
                    time(8),
                    time(13),
                    timedelta(minutes=30),
                    timedelta(hours=4, minutes=30),
                ),
                ("Project2", time(13), None, timedelta(), timedelta()),
            ),
            timedelta(hours=4, minutes=30),
        ),
        (
            ("Project1", "Project2"),
            "1. Project1 8:00 - 13:00, Lunch 0:30; Project2 13:00 - 17:00",
            1,
            (
                (
                    "Project1",
                    time(8),
                    time(13),
                    timedelta(minutes=30),
                    timedelta(hours=4, minutes=30),
                ),
                ("Project2", time(13), time(17), timedelta(), timedelta(hours=4)),
            ),
            timedelta(hours=8, minutes=30),
        ),
        (
            ("Project1",),
            "1. Project1 8:00 - 14:00, Lunch 0:45; Project1 16:00 - 17:00",
            1,
            (
                (
                    "Project1",
                    time(8),
                    time(14),
                    timedelta(minutes=45),
                    timedelta(hours=5, minutes=15),
                ),
                ("Project1", time(16), time(17), timedelta(), timedelta(hours=1)),
            ),
            timedelta(hours=6, minutes=15),
        ),
        (
            ("Project1", "Project2", "Project3"),
            "1. Project1 8:00 - 10:00; Project2 10:00 - 14:00, Lunch 1:00; Project3 14:00 - 17:00",
            1,
            (
                ("Project1", time(8), time(10), timedelta(), timedelta(hours=2)),
                (
                    "Project2",
                    time(10),
                    time(14),
                    timedelta(hours=1),
                    timedelta(hours=3),
                ),
                ("Project3", time(14), time(17), timedelta(), timedelta(hours=3)),
            ),
            timedelta(hours=8),
        ),
    ],
)
def test_various_day_strings_with_multiple_shifts(
    given_projects,
    given_day_string,
    expected_day,
    expected_shifts,
    expected_worked_hours,
):
    # Given a year and a month
    given_year = 2021
    given_month_number = 12

    expected_date = date(given_year, given_month_number, expected_day)

    # Given a month without days
    given_month = Month(given_year, given_month_number)
    assert len(given_month.days) == 0

    # Given a ledger with given projects and month
    given_ledger = Ledger()
    for project_name in given_projects:
        given_ledger.add_project(Project(project_name))
    given_ledger.add_month(given_month)

    # When parsing the string
    given_ledger.parse_day(given_year, given_month_number, given_day_string)

    # Then a day is added to the month
    assert len(given_month.days) == 1

    # And the added day has the correct date
    parsed_day = given_month.days[0]
    assert parsed_day.date == expected_date

    # And the day has the correct number of shift
    assert len(parsed_day.shifts) == len(expected_shifts)

    # And each shift has the correct project, start, stop, lunch and duration
    for parsed_shift, expected_shift in zip(parsed_day.shifts, expected_shifts):
        expected_start = (
            datetime.combine(expected_date, expected_shift[1])
            if expected_shift[1]
            else None
        )
        expected_stop = (
            datetime.combine(expected_date, expected_shift[2])
            if expected_shift[2]
            else None
        )
        assert parsed_shift.project.key == expected_shift[0]
        assert parsed_shift.start_time == expected_start
        assert parsed_shift.stop_time == expected_stop
        assert parsed_shift.lunch_duration == expected_shift[3]
        assert parsed_shift.duration == expected_shift[4]

    # And the day has the correct projects
    assert {p.key for p in parsed_day.projects} == {
        shift[0] for shift in expected_shifts
    }

    # And the day has the correct start time
    expected_start = (
        datetime.combine(expected_date, expected_shifts[0][1])
        if expected_shifts[0][1]
        else None
    )
    assert parsed_day.start_time == expected_start

    # And the day has the correct stop time
    expected_stop = (
        datetime.combine(expected_date, expected_shifts[-1][2])
        if expected_shifts[-1][2]
        else None
    )
    assert parsed_day.stop_time == expected_stop

    # And the day has the correct worked hours
    assert parsed_day.worked_hours == expected_worked_hours


@pytest.mark.parametrize(
    "given_year, given_month, given_month_string, given_projects, given_all_day_projects, expected_dates, expected_projects, expected_worked_hours",
    [
        (
            2022,
            1,
            "3. Project 8:00-17:00, lunch 1:00",
            ("project",),
            (),
            {date(2022, 1, 3)},
            1,
            timedelta(hours=8),
        ),
        (
            2022,
            1,
            """3. Project1 8:00-17:00, lunch 1:00
4. Project1 8:00-13:00, lunch 1:00; Project2 13:00-16:00""",
            ("project1", "Project2",),
            {date(2022, 1, 3), date(2022, 1, 4)},
            2,
            timedelta(hours=15),
        ),
        (
            2022,
            3,
            """1. Project1 8:00-17:00, lunch 0:45
2. Project2 9:00-17:00, lunch 0:30
3. Semester
4. Project1 10:00-12:30, lunch 0:30; Project2 12:30-15:00""",
            ("project1", "Project2"),
            ("Semester",),
            {date(2022, 3, 1), date(2022, 3, 2), date(2022, 3, 3), date(2022, 3, 4)},
            3,
            timedelta(hours=20, minutes=15),
        ),
    ],
)
def test_various_month_strings(
    given_year,
    given_month,
    given_month_string,
    given_projects,
    given_all_day_projects,
    expected_dates,
    expected_projects,
    expected_worked_hours,
):
    # Given ledger with the given projects
    given_ledger = Ledger()
    for project_name in given_projects:
        given_ledger.add_project(Project(project_name))

    # Given any all day projects
    for project_name in given_all_day_projects:
        given_ledger.add_project(Project(project_name, all_day=True))

    # When parsing the month
    given_ledger.parse_month(given_year, given_month, given_month_string)

    # Then the expected dates are added
    assert {day.date for day in given_ledger.current_month.days} == expected_dates

    # And the number of projects is correct
    assert len(given_ledger.projects) == expected_projects

    # And the number of worked hours is correct
    assert given_ledger.current_month.worked_hours == expected_worked_hours


def test_complete_month_example():
    # Given ledger
    given_ledger = Ledger()

    # Given three projects (from example month)
    given_ledger.add_project(Project("Project1"))
    given_ledger.add_project(Project("Project2"))
    given_ledger.add_project(Project("Project3"))

    # Given two all day projects
    vacation_project = Project("Vacation", all_day=True)
    sick_leave_project = Project("SickLeave", all_day=True)
    given_ledger.add_project(vacation_project)
    given_ledger.add_project(sick_leave_project)

    # When parsing the month
    given_ledger.parse_month(2022, 2, dedent(EXAMPLE_MONTH))

    # Then the number of months is 1
    assert len(given_ledger.months) == 1

    # And the number of days in current month are 20
    current_month = given_ledger.current_month
    assert len(current_month.days) == 20

    # And the number of projects in month is 3
    assert len(current_month.projects) == 5

    # And the number of vacation days is 2
    assert current_month.days_for_project("Vacation") == 2

    # And the number of sick leave days is 1
    assert current_month.days_for_project("SickLeave") == 1

    # And the 8th, 23rd amd 25th has comments
    assert current_month.get_day(8).comment == "Needed a break"
    assert current_month.get_day(23).comment == "## Doctor's visit ###"
    assert current_month.get_day(25).comment == "Project1 8:30 - 17:00; Lunch 0:30"

    # And the total worked hours on Project3 is 10:15
    assert current_month.worked_hours_for_project("Project3") == timedelta(
        hours=12, minutes=45
    )

    # And the total worked hours for the month is
    assert current_month.worked_hours == timedelta(hours=133)


def test_empty_year_file_does_nothing():
    # Given a year
    given_year = 2022

    # Given a ledger
    given_ledger = Ledger()

    # Given there are no months
    assert len(given_ledger.months) == 0

    # Given an empty year string
    given_year_string = ""

    # When parsing an empty year string
    given_ledger.parse_year(given_year, given_year_string)

    # Then thee are still no months
    assert len(given_ledger.months) == 0


def test_year_file_with_only_comments_does_nothing():
    # Given a year
    given_year = 2022

    # Given a ledger
    given_ledger = Ledger()

    # Given there are no months
    assert not given_ledger.months

    # Given there are no previous non working dates
    assert not given_ledger.non_working_dates

    # Given a year string with only blank lines and comments
    given_year_string = """

    # Ignore this

    # 2022-01-01: Pizza day

    # I
     # n
      # d
       # e
        # n
         # t
          # a
           # t
            # i
             # o
              # n
    
    """

    # When parsing the year string
    given_ledger.parse_year(given_year, dedent(given_year_string))

    # Then there are still no months
    assert not given_ledger.months

    # And there are no non working dates
    assert not given_ledger.non_working_dates


def test_non_working_date_is_stored():
    # Given a year
    given_year = 2022

    # Given a ledger
    given_ledger = Ledger()

    # Given there are no months
    assert not given_ledger.months

    # Given there are no previous non working dates
    assert not given_ledger.non_working_dates

    # Given a non working date in a year string
    given_date = date(given_year, 1, 6)
    given_description = "Epiphany"
    given_year_string = f"{given_date.isoformat()}: {given_description}"

    # When parsing the year string
    given_ledger.parse_year(given_year, given_year_string)

    # Then the non working date is stored
    assert len(given_ledger.non_working_dates) == 1
    assert len(given_ledger.non_working_dates[given_year]) == 1
    assert given_ledger.non_working_dates[given_year][given_date] == given_description

    # And there is still no month
    assert not given_ledger.months


def test_non_working_date_are_automatically_added_to_an_added_month():
    # Given a year and a month
    given_year = 2022
    given_month = 1

    # Given a ledger
    given_ledger = Ledger()

    # Given there are no months added
    assert not given_ledger.months

    # Given a non working date for the year and month in a year string
    given_date = date(given_year, given_month, 6)
    given_description = "Epiphany"
    given_year_string = f"{given_date.isoformat()}: {given_description}"

    # Given the year string has been parsed
    given_ledger.parse_year(given_year, given_year_string)
    assert given_ledger.non_working_dates[given_year][given_date] == given_description

    # When adding a month
    given_ledger.add_month(Month(given_year, given_month))

    # Then the non working date is added to the month
    non_working_day = given_ledger.months[0].get_day(given_date.day)
    assert non_working_day.comment == given_description


def test_complete_year_example():
    # Given a year
    given_year = 2022

    # Given a ledger
    given_ledger = Ledger()

    # Given there are no non working dates
    assert not given_ledger.non_working_dates

    # When parsing the year
    given_ledger.parse_year(given_year, dedent(EAMPLE_YEAR))

    # Then the year is added to non working dates
    assert given_year in given_ledger.non_working_dates

    # And there are 5 non working days
    year_non_working_dates = given_ledger.non_working_dates[given_year]
    assert len(year_non_working_dates) == 5
    assert year_non_working_dates[date(2022, 1, 17)] == "Blue Monday"
    assert year_non_working_dates[date(2022, 5, 4)] == "May the fourth"
    assert year_non_working_dates[date(2022, 5, 7)] == "Naked Gardening Day"
    assert year_non_working_dates[date(2022, 9, 19)] == "Talk Like a Pirate Day"
    assert year_non_working_dates[date(2022, 10, 31)] == "Base-n Jokes Day"


def test_year_file_with_out_of_year_dates_raises():
    # Given two years
    given_year_1 = 2023
    given_year_2 = 2022

    # Given a ledger
    given_ledger = Ledger()

    # Given a non working date for one of the years in a year string for the other year
    given_date = date(given_year_1, 1, 6)
    given_year_string = f"{given_date.isoformat()}: Epiphany"

    # When the string is parsed
    # Then the ledger raises
    with pytest.raises(exceptions.DateInconsistencyError):
        given_ledger.parse_year(given_year_2, given_year_string)


def test_adding_non_working_days_when_corresponding_month_allready_are_added_raises():
    # Given a year and month
    given_year = 2022
    given_month = 1

    # Given a ledger
    given_ledger = Ledger()

    # Given a month added to the ledger
    given_ledger.add_month(Month(given_year, given_month))

    # When adding a non working date for the month to the ledger
    # Then the ledger raises
    with pytest.raises(exceptions.MonthDateInconsistencyError):
        given_ledger.add_non_working_date(date(given_year, given_month, 6), "Epiphany")


def test_adding_a_project_makes_it_available():
    # Given a project with a description
    given_description = "THIS project"
    given_project = Project("SpecificProject", description=given_description)

    # Given a ledger
    given_ledger = Ledger()

    # Given the project is added to the ledger
    given_ledger.add_project(given_project)

    # Given a month string using the given project name
    given_month_string = f"1. {given_project.key} 9:00 - 17:00"

    # When the project is used in a month string
    given_ledger.parse_month(2022, 2, given_month_string)

    # Then the project is used
    shift_project = given_ledger.current_month.days[0].shifts[0].project
    assert shift_project is given_project

    # And the description can be accessed
    assert shift_project.description == given_description


def test_adding_an_all_day_project_makes_it_available():
    # Given an all day project with a description
    given_description = "All day long!"
    given_all_day_project = Project(
        "GoodTimes", description=given_description, all_day=True
    )

    # Given a ledger
    given_ledger = Ledger()

    # Given the project is added to the ledger
    given_ledger.add_project(given_all_day_project)

    # Given a month string using the given project name for a day
    given_month_string = f"1. {given_all_day_project.key}"

    # When the project is used in a month string
    given_ledger.parse_month(2022, 2, given_month_string)

    # Then the day is all day
    assert given_ledger.current_month.days[0].all_day

    # And the project is used
    shift_project = given_ledger.current_month.days[0].shifts[0].project
    assert shift_project is given_all_day_project

    # And the description can be accessed
    assert shift_project.description == given_description


def test_parse_project_file_adds_projects():
    # Given a ledger
    given_ledger = Ledger()

    # Given details for an all day project
    given_all_day_project_key = "ADP"
    given_all_day_project_name = "All Day Project"
    given_all_day_project_description = "All day long!"

    # Given details for an ordinary project
    given_ordinary_project_key = "Job"
    given_ordinary_project_name = "The job project"
    given_ordinary_project_description = "Work work work"

    # Given a projects string with the projects
    given_projects_string = f"""\
        [{given_all_day_project_key}]
        name: {given_all_day_project_name}
        description: {given_all_day_project_description}
        all_day: true

        [{given_ordinary_project_key}]
        name: {given_ordinary_project_name}
        description: {given_ordinary_project_description}
        all_day: false
        """

    # Given there are no projects added
    assert not given_ledger.projects

    # When parsing the project string
    given_ledger.parse_projects(dedent(given_projects_string))

    # Then the projects are added to the ledger
    assert len(given_ledger.projects) == 2

    assert given_all_day_project_key in given_ledger.projects
    assert given_ordinary_project_key in given_ledger.projects

    all_day_project = given_ledger.projects[given_all_day_project_key]
    ordinary_project = given_ledger.projects[given_ordinary_project_key]

    assert all_day_project.all_day
    assert all_day_project.name == given_all_day_project_name
    assert all_day_project.description == given_all_day_project_description

    assert not ordinary_project.all_day
    assert ordinary_project.name == given_ordinary_project_name
    assert ordinary_project.description == given_ordinary_project_description


def test_ledger_is_aware_of_next_work_date():
    # Given a ledger
    given_ledger = Ledger()

    # Given a month added to the ledger
    given_ledger.add_month(Month(2022, 1))

    # Given the next working day for the ledger
    first_work_date = given_ledger.next_work_date

    # Given the next working date does not increase on its own
    assert given_ledger.next_work_date == first_work_date
    assert given_ledger.next_work_date == first_work_date
    assert given_ledger.next_work_date == first_work_date

    # When adding a day for that date
    given_ledger.add_day(test_utilities.given_completed_day_for_date(first_work_date))

    # Then the next working date is updated
    second_work_date = given_ledger.next_work_date
    assert second_work_date != first_work_date


def test_ledger_will_increase_next_work_day_past_end_of_month():
    number_of_workdays_in_january_2022 = 21
    last_workday_in_january_2022 = date(2022, 1, 31)

    # Given a ledger
    given_ledger = Ledger()

    # Given a month added to the ledger
    given_month = Month(2022, 1)
    given_ledger.add_month(given_month)

    # Given next working date is in the same month as the given month
    assert given_ledger.next_work_date.month == given_month.month

    # Given the days beeing continuosly added from the next work date
    for _ in range(number_of_workdays_in_january_2022 - 1):
        given_ledger.add_day(
            test_utilities.given_completed_day_for_date(given_ledger.next_work_date)
        )

    # When the month runs out of work dates
    assert given_ledger.next_work_date == last_workday_in_january_2022
    given_ledger.add_day(
        test_utilities.given_completed_day_for_date(given_ledger.next_work_date)
    )

    # Then the next working date will be in a new month
    assert given_ledger.next_work_date.month != given_month.month

    # And the current month is still the given month
    assert given_ledger.current_month is given_month

    # And after adding that day, the current month is not the given month
    given_ledger.add_day(
        test_utilities.given_completed_day_for_date(given_ledger.next_work_date)
    )
    assert given_ledger.current_month is not given_month


def test_first_month_can_start_in_the_middle_of_a_month():
    # Given a ledger
    given_ledger = Ledger()

    # Given a month added to the ledger
    given_month = Month(2023, 8)
    given_ledger.add_month(given_month)

    # Given a day in the middle of the month
    given_day = test_utilities.given_completed_day_for_date(
        date(given_month.year, given_month.month, 21)
    )
    assert given_day.date > given_ledger.next_work_date

    # When adding the date to the ledger
    given_ledger.add_day(given_day)

    # Then the day is accepted
    assert given_ledger.current_month.days[0] is given_day

    # And the next working day is advanced correspondingly
    expected_next_working_date = given_day.date.replace(day=given_day.date.day + 1)
    assert given_ledger.next_work_date == expected_next_working_date


def test_subsequent_months_can_not_start_in_the_middle_of_a_month():
    # Given a ledger
    given_ledger = Ledger()

    # Given a completed month added to the ledger
    given_month = test_utilities.given_completed_month(2023, 8)
    given_ledger.add_month(given_month)
    assert given_ledger.next_work_date.month == given_month.month + 1

    # Given a day in the middle of next month
    given_date = date(given_month.year, given_month.month + 1, 15)
    given_day = test_utilities.given_completed_day_for_date(given_date)

    # When adding the day to the ledger
    # Then the ledger raises
    with pytest.raises(exceptions.MonthDateInconsistencyError):
        given_ledger.add_day(given_day)


# def test_bad_month_file_raises()
# def test_bad_year_file_raises()
# def test_bad_project_file_raises()

EXAMPLE_MONTH = """\
    1. Project1 9:00 - 17:30, Lunch 0:30
    2. Project1 8:00 - 17:30, Lunch 0:30
    3. Project1 8:30 - 17:00, Lunch 1:00
    4. Project1 9:00 - 18:00, Lunch 0:30

    7. Project2 9:15 - 16:45, Lunch 0:30
    8. Vacation  # Needed a break 
    9. Vacation
    10. Project2 9:05 - 17:30, Lunch 0:30
    11. Project1 9:00 - 13:00, Lunch 0:30; Project2 13:00 - 15:00; Project3 15:00-17:30
    
    14. Project1 9:00 - 13:00, Lunch 0:30; Project2 13:00 - 17:30
    15. Project2 9:00 - 13:00, Lunch 1:30; Project1 13:00 - 17:15
    16. Project1 9:00 - 14:00, Lunch 0:30; Project3 15:00 - 17:30
    17. SickLeave
    18. Project1 9:00 - 11:00; Project2 11:00 - 17:30, Lunch 0:30
    
    # Working from home this week
    21. Project3 9:00 - 17:15, Lunch 0:30
    22. Project2 9:00 - 17:50, Lunch 0:30
    23. Project1 10:00 - 18:10, Lunch 1:00 ### Doctor's visit ###
    24. Project2 8:45 - 17:55, Lunch 0:40
    25. Project1 8:00 - 16:05, Lunch 0:30 # Project1 8:30 - 17:00; Lunch 0:30 
    
    28. Project2 9:00 - 17:30, Lunch 0:30
    """

EAMPLE_YEAR = """\
    # January
    2022-01-17: Blue Monday

    # May
    2022-05-04: May the fourth
    2022-05-07: Naked Gardening Day   # It's a thing #

    # September
    2022-09-19: Talk Like a Pirate Day   # Arrrrrrr!

    # October
    2022-10-31: Base-n Jokes Day        # Merry Christmas!
    """
