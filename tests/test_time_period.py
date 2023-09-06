import datetime

import pytest

from heath.day import Day
from heath.project import Project
from heath.time_period import TimePeriod, lossless_round

from tests.utilities import given_completed_shift_for_project_between_times


def test_get_project_durations_for_time_period():
    # Given two sequential days
    given_day_1 = Day(datetime.date(2023, 9, 5))
    given_day_2 = Day(datetime.date(2023, 9, 6))

    # Given two projects
    given_project_1 = Project("Project 1")
    given_project_2 = Project("Project 2")

    # Given the first day has completed shifts
    given_day_1.add_shift(
        given_completed_shift_for_project_between_times(
            given_project_1,
            datetime.datetime(2023, 9, 5, 9),
            datetime.datetime(2023, 9, 5, 17),
        ),
    )
    expected_duration_project_1_date_1 = datetime.timedelta(hours=8)

    # Given the second day has completed shifts in both of the projects
    given_day_2.add_shift(
        given_completed_shift_for_project_between_times(
            given_project_2,
            datetime.datetime(2023, 9, 6, 8, 30),
            datetime.datetime(2023, 9, 6, 11),
        ),
    )

    given_day_2.add_shift(
        given_completed_shift_for_project_between_times(
            given_project_1,
            datetime.datetime(2023, 9, 6, 11),
            datetime.datetime(2023, 9, 6, 15),
        ),
    )

    given_day_2.add_shift(
        given_completed_shift_for_project_between_times(
            given_project_2,
            datetime.datetime(2023, 9, 6, 15),
            datetime.datetime(2023, 9, 6, 16, 45),
        ),
    )

    expected_duration_project_1_date_2 = datetime.timedelta(hours=4)
    expected_duration_project_2_date_2 = datetime.timedelta(hours=4, minutes=15)

    # Given a time period with the days
    given_time_period = SimpleTimePeriod([given_day_1, given_day_2])

    # When calling project_durations
    project_durations = given_time_period.project_durations()

    # Then the project_durations has the two project
    assert len(project_durations) == 2
    assert given_project_1.key in project_durations
    assert given_project_2.key in project_durations

    # And the first project has both dates
    assert len(project_durations[given_project_1.key]) == 2
    assert given_day_1.date in project_durations[given_project_1.key]
    assert given_day_2.date in project_durations[given_project_1.key]

    # And the second project has one date
    assert len(project_durations[given_project_2.key]) == 1
    assert given_day_2.date in project_durations[given_project_2.key]

    # And each entry has the expected duration
    assert (
        project_durations[given_project_1.key][given_day_1.date]
        == expected_duration_project_1_date_1
    )
    assert (
        project_durations[given_project_1.key][given_day_2.date]
        == expected_duration_project_1_date_2
    )
    assert (
        project_durations[given_project_2.key][given_day_2.date]
        == expected_duration_project_2_date_2
    )


@pytest.mark.parametrize(
    "given_durations, expected_durations",
    (
        ({}, {}),
        (
            {datetime.date(2023, 9, 6): datetime.timedelta(hours=8)},
            {datetime.date(2023, 9, 6): datetime.timedelta(hours=8)},
        ),
        (
            {
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8),
                datetime.date(2023, 9, 7): datetime.timedelta(hours=8, minutes=30),
            },
            {
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8),
                datetime.date(2023, 9, 7): datetime.timedelta(hours=8, minutes=30),
            },
        ),
        (
            # Round up biggest value even if it would round up on its own
            {
                datetime.date(2023, 9, 4): datetime.timedelta(hours=8, minutes=5),
                datetime.date(2023, 9, 5): datetime.timedelta(hours=8, minutes=5),
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8, minutes=10),
                datetime.date(2023, 9, 7): datetime.timedelta(hours=8, minutes=5),
                datetime.date(2023, 9, 8): datetime.timedelta(hours=8, minutes=5),
            },
            {
                datetime.date(2023, 9, 4): datetime.timedelta(hours=8),
                datetime.date(2023, 9, 5): datetime.timedelta(hours=8),
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8, minutes=30),
                datetime.date(2023, 9, 7): datetime.timedelta(hours=8),
                datetime.date(2023, 9, 8): datetime.timedelta(hours=8),
            },
        ),
        (
            # Round up latest value even if earlier values have same remainder
            {
                datetime.date(2023, 9, 4): datetime.timedelta(hours=8, minutes=10),
                datetime.date(2023, 9, 5): datetime.timedelta(hours=8, minutes=10),
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8, minutes=10),
            },
            {
                datetime.date(2023, 9, 4): datetime.timedelta(hours=8),
                datetime.date(2023, 9, 5): datetime.timedelta(hours=8),
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8, minutes=30),
            },
        ),
        (
            # *:15 and *:45 are handled equaly.
            {
                datetime.date(2023, 9, 4): datetime.timedelta(hours=7, minutes=45),
                datetime.date(2023, 9, 5): datetime.timedelta(hours=8, minutes=15),
                datetime.date(2023, 9, 6): datetime.timedelta(hours=7, minutes=45),
                datetime.date(2023, 9, 7): datetime.timedelta(hours=8, minutes=15),
            },
            {
                datetime.date(2023, 9, 4): datetime.timedelta(hours=7, minutes=30),
                datetime.date(2023, 9, 5): datetime.timedelta(hours=8, minutes=00),
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8, minutes=00),
                datetime.date(2023, 9, 7): datetime.timedelta(hours=8, minutes=30),
            },
        ),
        (
            # Smaller values might become zero.
            {
                datetime.date(2023, 9, 4): datetime.timedelta(hours=0, minutes=20),
                datetime.date(2023, 9, 5): datetime.timedelta(hours=8, minutes=20),
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8, minutes=25),
                datetime.date(2023, 9, 7): datetime.timedelta(hours=8, minutes=25),
            },
            {
                datetime.date(2023, 9, 4): datetime.timedelta(),
                datetime.date(2023, 9, 5): datetime.timedelta(hours=8, minutes=30),
                datetime.date(2023, 9, 6): datetime.timedelta(hours=8, minutes=30),
                datetime.date(2023, 9, 7): datetime.timedelta(hours=8, minutes=30),
            },
        ),
    ),
)
def test_lossless_round_on_compliant_data(given_durations, expected_durations):
    # Given durations
    # When using lossless_round
    rounded_durations = lossless_round(given_durations)

    # Then the result should have the same total duration as the input
    assert sum(rounded_durations.values(), datetime.timedelta()) == sum(
        given_durations.values(), datetime.timedelta()
    )

    # And the result should match the expexted durations
    assert rounded_durations == expected_durations


@pytest.mark.parametrize(
    "given_durations",
    (
        {
            datetime.date(2023, 9, 6): datetime.timedelta(hours=8, minutes=35)
        },  # Single day, not even half hours
        {
            datetime.date(2023, 9, 6): datetime.timedelta(
                hours=8, minutes=20
            ),  # Multiple days, not even half hours
            datetime.date(2023, 9, 7): datetime.timedelta(hours=7, minutes=25),
            datetime.date(2023, 9, 7): datetime.timedelta(hours=8, minutes=20),
        },
    ),
)
def test_lossless_round_on_non_compliant_data_returns_input_unchanged(given_durations):
    # Given durations
    # When using lossless_round
    rounded_durations = lossless_round(given_durations)

    # Then the input is returned
    assert rounded_durations == given_durations


class SimpleTimePeriod(TimePeriod):
    def __init__(self, days: list):
        super().__init__()
        self._days = days
