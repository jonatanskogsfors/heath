import datetime
from pathlib import Path

import pytest

from heath.folder import LedgerFolder


def test_non_existing_folder_is_not_valid(tmp_path: Path):
    # Given a non existing folder
    given_folder = tmp_path / "im_not_here"
    assert not given_folder.exists()

    # When creating a LedgerFolder
    ledger_folder = LedgerFolder(given_folder)

    # Then the folder is invalid
    assert not ledger_folder.valid

    # And the folder has 0 months
    assert len(ledger_folder.months) == 0


def test_empty_folder_is_valid(tmp_path: Path):
    # Given an empty directory
    given_folder = tmp_path / "empty"
    given_folder.mkdir()
    assert given_folder.exists()
    assert not list(given_folder.iterdir())

    # When creating a LedgerFolder
    ledger_folder = LedgerFolder(given_folder)

    # Then the folder invalid
    assert ledger_folder.valid

    # And the folder has 0 months
    assert len(ledger_folder.months) == 0


def test_folder_with_a_month_file_is_valid(tmp_path: Path):
    # Given a folder
    given_folder = tmp_path / "folder"
    given_folder.mkdir()

    # Given an empty month file
    month_file = given_folder / "2022-1.txt"
    month_file.touch()

    # When creating a LedgerFolder
    ledger_folder = LedgerFolder(given_folder)

    # Then the folder is valid
    assert ledger_folder.valid

    # Then the folder sees 1 month
    assert len(ledger_folder.months) == 1


@pytest.mark.parametrize(
    "filenames, expected_months, expected_years, has_projects",
    [
        (("2022-1.txt",), 1, 0, False),
        (("2022-12.txt",), 1, 0, False),
        (
            (
                "2022-2.txt",
                "2022-3.txt",
            ),
            2,
            0,
            False,
        ),
        (
            (
                "2022-1.txt",
                "2022-2.txt",
                "2022-3.txt",
                "2022-4.txt",
                "2022-5.txt",
                "2022-6.txt",
                "2022-7.txt",
                "2022-8.txt",
                "2022-9.txt",
                "2022-10.txt",
                "2022-11.txt",
                "2022-12.txt",
            ),
            12,
            0,
            False,
        ),
        (
            (
                "2021-12.txt",
                "2022-1.txt",
                "2022-2.txt",
            ),
            3,
            0,
            False,
        ),
        (("1997-3.txt", "1997-4.txt", "please_ignore_this_file.txt"), 2, 0, False),
        (("2022-1", "1997.cfg", "projects.txt"), 0, 0, False),
        (
            (
                "2021-12.txt",
                "2022-1.txt",
                "2022-2.txt",
                "2021.txt",
                "2022.txt",
                "projects.cfg",
            ),
            3,
            2,
            True,
        ),
    ],
)
def test_folders_with_various_content_are_valid(
    tmp_path: Path,
    filenames: tuple,
    expected_months: int,
    expected_years: int,
    has_projects: bool,
):
    # Given a folder
    given_folder = tmp_path / "folder"
    given_folder.mkdir()

    # Given empty month files
    for filename in filenames:
        month_file = given_folder / filename
        month_file.touch()

    # When creating a LedgerFolder
    ledger_folder = LedgerFolder(given_folder)

    # Then the folder is valid
    assert ledger_folder.valid

    # And the folder sees all the months
    assert len(ledger_folder.months) == expected_months

    # And the folder sees all the years
    assert len(ledger_folder.years) == expected_years

    # And the folder knows about any projects file
    assert bool(ledger_folder.projects) == has_projects


def test_folder_with_non_sequential_month_files_are_invalid(tmp_path: Path):
    # Given a folder
    given_folder = tmp_path / "folder"
    given_folder.mkdir()

    # Given two, non sequential month files
    (given_folder / "2022-1.txt").touch()
    (given_folder / "2022-3.txt").touch()

    # When creating a LedgerFolder
    ledger_folder = LedgerFolder(given_folder)

    # Then the folder is valid
    assert not ledger_folder.valid

    # Then the folder sees 1 month
    assert len(ledger_folder.months) == 2


def test_year_file_can_be_read(tmp_path: Path):
    # Given a folder
    given_folder = tmp_path / "folder"
    given_folder.mkdir()

    # Given a year
    given_year = 2022

    # Given an empty year file
    given_year_file = given_folder / f"{given_year}.txt"
    given_year_file.touch()

    # When creating a LedgerFolder
    ledger_folder = LedgerFolder(given_folder)

    # Then the folder is valid
    assert ledger_folder.valid

    # And the folder sees the year
    assert len(ledger_folder.years) == 1
    assert ledger_folder.years[0].year == given_year


#    # Given all day projects
#    given_all_days_projects = {"Vacation": "Good times", "SickLeave": "Bad times"}
