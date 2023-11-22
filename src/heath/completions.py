import os
from pathlib import Path

from heath.project import Project


def complete_projects(ctx, param, incomplete: str, all_day: bool = False):
    if heath_folder := os.environ.get("HEATH_FOLDER"):
        projects_file = Path(heath_folder) / "projects.cfg"
        projects = Project.from_configuration_path(projects_file)
        return [
            project.key
            for project in projects
            if project.key.lower().startswith(incomplete.lower()) and project.all_day == all_day
        ]
    return []


def complete_allday_projects(ctx, param, incomplete):
    return complete_projects(ctx, param, incomplete, all_day=True)
