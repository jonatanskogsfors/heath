class HeathError(Exception):
    """Base exception for project"""


class DayError(HeathError):
    """Base exception for Day"""


class DayInconsistencyError(DayError):
    """Inconsistent data in Day"""


class MonthError(HeathError):
    """Base exception for Month"""


class MonthPreviousDayNotCompletedError(MonthError):
    """Bad state for Month"""


class MonthDateInconsistencyError(MonthError):
    """Inconsistent data in Month"""


class ProjectError(HeathError):
    """ "Base exception for Projects"""


class ShiftError(HeathError):
    """Base exception for Shift"""


class ShiftConsistencyError(ShiftError):
    """Inconsistent data in Shift"""


class DateInconsistencyError(HeathError):
    """Bad state concerning dates"""
