import configparser
import io
from pathlib import Path
from typing import Iterable, Self


class Project:
    def __init__(
        self, key: str, name: str = "", report: str = "", all_day: bool = False
    ) -> None:
        self.key = key
        self.name = name
        self.report = report
        self.all_day = all_day

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return (
                self.key == other.key
                and self.name == other.name
                and self.report == other.report
                and self.all_day == other.all_day
            )
        else:
            return other == self

    @classmethod
    def from_configuration_path(cls, configuration: Path) -> list[Self]:
        return cls.from_configuration_string(configuration.read_text())

    @classmethod
    def from_configuration_string(cls, configuration: str) -> list[Self]:
        projects_config = configparser.ConfigParser()
        projects_config.read_string(configuration)
        projects = []
        for project_key in projects_config.sections():
            project_data = projects_config[project_key]
            new_project = cls(
                project_key,
                name=project_data.get("Name", ""),
                report=project_data.get("Report", ""),
                all_day=project_data.getboolean("AllDay"),
            )
            projects.append(new_project)
        return projects

    @classmethod
    def to_configuration_string(cls, projects: Iterable[Self]):
        export_parser = configparser.ConfigParser(delimiters=[": "])
        export_parser.optionxform = lambda o: o
        for project in projects:
            export_parser[project.key] = {
                "Name": project.name,
                "Report": project.report,
                "AllDay": project.all_day,
            }
        configuration_string = io.StringIO()
        export_parser.write(configuration_string, space_around_delimiters=False)
        configuration_string.seek(0)
        return configuration_string.read()
