from textwrap import dedent

import pytest

from heath.project import Project


@pytest.mark.parametrize(
    "given_key, given_name, given_report, given_allday",
    (
        ("A", None, None, True),
        ("A", None, None, False),
        ("A", "Project A", None, True),
        ("A", "Project A", None, False),
        ("A", None, "P-A", True),
        ("A", None, "P-A", False),
        ("A", "Project A", "P-A", True),
        ("A", "Project A", "P-A", False),
    ),
)
def test_projects_with_same_values_are_equal(
    given_key, given_name, given_report, given_allday
):
    # Given two projects with the same values
    project_1 = Project(given_key, given_name, given_report, given_allday)
    project_2 = Project(given_key, given_name, given_report, given_allday)

    # When comparing the projects
    are_equal = project_1 == project_2

    # They are the same
    assert are_equal


@pytest.mark.parametrize(
    "given_configuration, expected_project_values",
    (
        (
            "",
            (),
        ),
        (
            """
            [P1]
            Name: Project 1
            Report: Project-123456
            AllDay: False
            """,
            (("P1", "Project 1", "Project-123456", False),),
        ),
        (
            """
            [P1]
            Name: Project 1
            Report: Project-123456
            AllDay: False

            [P2]
            Name: Project 2
            Report: Project-654321
            AllDay: True
            """,
            (
                ("P1", "Project 1", "Project-123456", False),
                ("P2", "Project 2", "Project-654321", True),
            ),
        ),
        (
            """
            [P2]
            Name: Project 2
            Report: Project-654321
            AllDay: True

            [P1]
            Name: Project 1
            Report: Project-123456
            AllDay: False
            """,
            (
                ("P2", "Project 2", "Project-654321", True),
                ("P1", "Project 1", "Project-123456", False),
            ),
        ),
    ),
)
def test_parse_project_roundtrip(
    given_configuration: str, expected_project_values: tuple
):
    # Given a projects configuration
    given_configuration = dedent(given_configuration)

    # When parsing the string
    parsed_projects = Project.from_configuration_string(given_configuration)

    # Then the expected projects are parsed
    expected_projects = [Project(*args) for args in expected_project_values]
    assert parsed_projects == expected_projects

    # And when exporting a projects configuration
    exported_configuration = Project.to_configuration_string(parsed_projects)

    # Then the configuration is identical with the given configuration
    assert exported_configuration.strip() == given_configuration.strip()
