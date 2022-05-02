from pathlib import Path
import re
from typing import Optional


class FileObject:
    def __init__(self, file_path: Path):
        self.path = file_path

    @property
    def content(self):
        return self.path.read_text()

    def write(self, content: str):
        self.path.write_text(content)

    def __bool__(self):
        return self.path.exists()


class YearFile(FileObject):
    PATTERN = re.compile("(\d{4})\.txt")

    @property
    def year(self) -> Optional[int]:
        if match := YearFile.PATTERN.match(self.path.name):
            return int(match.group(1))
        return None


class MonthFile(FileObject):
    PATTERN = re.compile("(\d{4})-(\d{1,2})\.txt")

    @property
    def month(self):
        if match := MonthFile.PATTERN.match(self.path.name):
            return int(match.group(2))
        return None

    @property
    def year(self):
        if match := MonthFile.PATTERN.match(self.path.name):
            return int(match.group(1))
        return None

    @property
    def key(self):
        if match := MonthFile.PATTERN.match(self.path.name):
            return f"{int(match.group(1))}-{int(match.group(2)):02}"
        return None


class ProjectsFile(FileObject):
    def __init__(self, folder_path: Path):
        self.path = folder_path / "projects.cfg"


class LedgerFolder:
    def __init__(self, folder_path: Path):
        self.path = folder_path
        self._months = {}
        self._years = []
        self._projects = ProjectsFile(self.path)

    @property
    def valid(self) -> bool:
        status = self.path.exists()
        status &= self._month_files_are_valid()
        return status

    def _month_files_are_valid(self):
        if self.months:
            available_months = sorted([(m.year, m.month) for m in self.months.values()])
            first_month = available_months[0]
            for n in range(len(available_months)):
                month = first_month[1] + n
                year = first_month[0] + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                if (year, month) not in available_months:
                    return False
        return True

    @property
    def months(self) -> dict[str, MonthFile]:
        if not self._months and self.path.exists():
            self._months = {
                month_file.key: month_file
                for month_file in (
                    MonthFile(path)
                    for path in self.path.iterdir()
                    if MonthFile.PATTERN.match(path.name)
                )
            }
        return self._months

    @property
    def next_month(self) -> MonthFile:
        last_month = self.ordered_months[-1]
        next_month_number = last_month.month % 12 + 1
        next_year_number = last_month.year + (last_month.month == 12)
        next_month_path = last_month.path.parent / f"{next_year_number}-{next_month_number}.txt"
        return MonthFile(next_month_path)

    @property
    def ordered_months(self) -> list[MonthFile]:
        return sorted(self.months.values(), key=lambda m: (m.year, m.month))

    @property
    def years(self) -> list[YearFile]:
        if not self._years and self.path.exists():
            self._years = sorted(
                [
                    YearFile(path)
                    for path in self.path.iterdir()
                    if YearFile.PATTERN.match(path.name)
                ],
                key=lambda m: f"{m.year}",
            )
        return self._years

    @property
    def projects(self) -> bool:
        return self._projects

    def __str__(self) -> str:
        strings = (
            f"Path: {self.path.absolute()}",
            f"Years: {len(self.years)}",
            f"Months: {len(self.months)}",
            f"Projects: {self.projects}",
            f"Valid: {self.valid}",
        )
        return "\n".join(strings)

    def __repr__(self) -> str:
        return f"LedgerFolder({self.path})"

    @staticmethod
    def year_month_from_month_file(month_file: Path):
        if match := MonthFile.PATTERN.match(month_file.name):
            return match.group(1), match.group(2)
        return None, None
