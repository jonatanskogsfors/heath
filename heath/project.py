import configparser
from pathlib import Path
from typing import Self


class Project:
    def __init__(
        self, key: str, name: str = "", description: str = "", all_day: bool = False
    ) -> None:
        self.key = key
        self.name = name
        self.description = description
        self.all_day = all_day

    @classmethod
    def from_configuration_string(cls, configuration: str) -> list[Self]:
        projects_config = configparser.ConfigParser()
        projects_config.read_string(configuration)
        projects = []
        for project_key in projects_config.sections():
            project_data = projects_config[project_key]
            new_project = cls(
                project_key,
                project_data["name"],
                description=project_data.get("description"),
                all_day=project_data.getboolean("all_day"),
            )
            projects.append(new_project)
        return projects

    @classmethod
    def from_configuration_path(cls, configuration: Path) -> list[Self]:
        return cls.from_configuration_string(configuration.read_text())
