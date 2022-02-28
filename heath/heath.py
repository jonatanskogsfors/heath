import datetime
import locale
import sys
from pathlib import Path
from typing import Optional

import click

from heath.day import Day
from heath.exceptions import ProjectError
from heath.folder import LedgerFolder
from heath.ledger import Ledger
from heath.shift import Shift


@click.group()
@click.option("-f", "--folder", type=Path, envvar="HEATH_FOLDER")
@click.option("-V", "--validate", is_flag=True)
@click.pass_context
def cli(ctx, folder: Path, validate: bool):
    if not folder:
        folder = Path.cwd()
    ledger_folder = LedgerFolder(folder)
    if validate:
        print(ledger_folder)
        print()

    if not ledger_folder.valid:
        sys.exit("Ledger folder not valid")

    ledger = Ledger()
    ctx.ensure_object(dict)
    ctx.obj["LEDGER"] = ledger
    ctx.obj["FOLDER"] = ledger_folder

    if ledger_folder.projects:
        ledger.parse_projects(ledger_folder.projects.content)

    for year_file in ledger_folder.years:
        ledger.parse_year(year_file.year, year_file.content)

    for month_file in ledger_folder.ordered_months:
        ledger.parse_month(month_file.year, month_file.month, month_file.content)


@cli.command(help="Show ledger for month.")
@click.argument("month_number", type=click.IntRange(1, 12), required=False)
@click.argument("year", type=int, required=False)
@click.option(
    "-a",
    "--include_active_day",
    is_flag=True,
    help="Show current duration for any non complete day.",
)
@click.option(
    "-c", "--include-comments", is_flag=True, help="Show any comments for days."
)
@click.pass_context
def month(
    ctx,
    month_number: Optional[int],
    year: Optional[int],
    include_active_day: bool,
    include_comments: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]

    month = (
        ledger.get_month(month_number, year) if month_number else ledger.current_month
    )

    print()
    print(
        month.report(
            include_active_day=include_active_day, include_comments=include_comments
        )
    )
    print()


@cli.command(help="Show ledger for week.")
@click.argument("week_number", type=click.IntRange(0, 53), required=False)
@click.argument("year", type=int, required=False)
@click.option(
    "-a",
    "--include_active_day",
    is_flag=True,
    help="Show current duration for any non complete day.",
)
@click.option(
    "-c", "--include-comments", is_flag=True, help="Show any comments for days."
)
@click.option("-p", "--by-project", is_flag=True, help="Group by project.")
@click.pass_context
def week(
    ctx,
    week_number: Optional[int],
    year: Optional[int],
    include_active_day: bool,
    include_comments: bool,
    by_project: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]

    week = (
        ledger.get_week(week_number, year)
        if week_number is not None
        else ledger.current_week
    )

    report = week.report(
        include_active_day=include_active_day,
        include_comments=include_comments,
        by_project=by_project,
    )

    print("\n" + report + "\n")


@cli.command(help="Show ledger for day.")
@click.argument("day_number", type=click.IntRange(1, 31), required=False)
@click.argument("month_number", type=click.IntRange(1, 12), required=False)
@click.argument("year", type=int, required=False)
@click.option(
    "-a",
    "--include_active_day",
    is_flag=True,
    help="Show current duration for any non complete day.",
)
@click.option(
    "-c", "--include-comments", is_flag=True, help="Show any comment for day."
)
@click.pass_context
def day(
    ctx,
    day_number: Optional[int],
    month_number: Optional[int],
    year: Optional[int],
    include_active_day: bool,
    include_comments: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]

    if (
        day := ledger.get_day(day_number, month_number, year)
        if day_number
        else ledger.today
    ):
        print(
            "\n"
            + day.report(
                include_active_day=include_active_day,
                include_comments=include_comments,
            )
            + "\n"
        )

    else:
        print("No information for day.")


@cli.command(help="List all known projects.")
@click.pass_context
def projects(ctx):
    ledger: Ledger = ctx.obj["LEDGER"]

    width = 20
    print("-" * width)
    print("Projects".center(width))
    print("-" * width)
    for project in sorted(ledger.projects.values(), key=lambda p: p.key):
        project_name = f" - {project.name}" if project.name else ""
        print(project.key + project_name)
        print(f"  All day:     {('No', 'Yes')[project.all_day]}")
        print(f"  Description: {project.description or ''}")
        print()


@cli.command(help="Start a new shift for a project.")
@click.argument("project")
@click.argument("start_time")
@click.option("-s", "--same-day", is_flag=True, help="Do not create a new day.")
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Do not write change to file but show results.",
)
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def start(
    ctx, project: str, start_time: str, same_day: bool, dry_run: bool, verbose: bool
):
    ledger: Ledger = ctx.obj["LEDGER"]
    folder: LedgerFolder = ctx.obj["FOLDER"]
    verbose |= dry_run

    today = datetime.date.today()
    if ledger.last_day.date != today and not same_day:
        ledger.add_day(Day(today))

    new_shift = Shift(ledger.new_or_existing_project(project), ledger.last_day.date)
    start_datetime = datetime.datetime.combine(
        new_shift.date,
        datetime.time(*(int(number) for number in start_time.split(":"))),
    )
    new_shift.start(start_datetime)
    ledger.last_day.add_shift(new_shift)

    if not dry_run:
        _write_month_to_disk(
            ledger, folder, ledger.current_month.year, ledger.current_month.month
        )

    if verbose:
        print("\n" + ledger.last_day.report() + "\n")


@cli.command(help="Set lunch duration for an ongoing shift.")
@click.argument("lunch_duration")
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Do not write change to file but show results.",
)
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def lunch(ctx, lunch_duration: str, dry_run: bool, verbose: bool):
    ledger: Ledger = ctx.obj["LEDGER"]
    folder: LedgerFolder = ctx.obj["FOLDER"]
    verbose |= dry_run

    hours, minutes = map(int, lunch_duration.split(":"))
    lunch_timedelta = datetime.timedelta(hours=hours, minutes=minutes)
    ledger.current_shift.lunch(lunch_timedelta)

    if not dry_run:
        _write_month_to_disk(
            ledger, folder, ledger.current_month.year, ledger.current_month.month
        )

    if verbose:
        print("\n" + ledger.last_day.report() + "\n")


@cli.command(help="Set stop time for an ongoing shift.")
@click.argument("stop_time")
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Do not write change to file but show results.",
)
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def stop(ctx, stop_time: str, dry_run: bool, verbose: bool):
    ledger: Ledger = ctx.obj["LEDGER"]
    folder: LedgerFolder = ctx.obj["FOLDER"]
    verbose |= dry_run

    stop_datetime = datetime.datetime.combine(
        ledger.last_day.date,
        datetime.time(*(int(number) for number in stop_time.split(":"))),
    )
    ledger.current_shift.stop(stop_datetime)

    if not dry_run:
        _write_month_to_disk(
            ledger, folder, ledger.current_month.year, ledger.current_month.month
        )

    if verbose:
        print("\n" + ledger.last_day.report() + "\n")


@cli.command(help="Add all day project for day")
@click.argument("project")
@click.argument("day_number", type=click.IntRange(1, 31), required=False)
@click.argument("month_number", type=click.IntRange(1, 12), required=False)
@click.argument("year", type=int, required=False)
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Do not write change to file but show results.",
)
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def allday(
    ctx,
    project: str,
    day_number: Optional[int],
    month_number: Optional[int],
    year: Optional[int],
    dry_run: bool,
    verbose: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]
    folder: LedgerFolder = ctx.obj["FOLDER"]
    verbose |= dry_run

    try:
        all_day_project = ledger.new_or_existing_project(project, all_day=True)
    except ProjectError:
        sys.exit(f"Project {project} is not an all day project.")

    today = datetime.date.today()
    year = year or today.year
    month_number = month_number or today.month
    day_number = day_number or today.day
    date = datetime.date(year, month_number, day_number)

    day = Day(date)
    day.add_shift(Shift(all_day_project, date))
    ledger.add_day(day)

    if not dry_run:
        _write_month_to_disk(
            ledger, folder, ledger.current_month.year, ledger.current_month.month
        )

    if verbose:
        print("\n" + ledger.last_day.report() + "\n")


@cli.command(help="Add comment for day.")
@click.argument("comment_string")
@click.argument("day_number", type=click.IntRange(1, 31), required=False)
@click.argument("month_number", type=click.IntRange(1, 12), required=False)
@click.argument("year", type=int, required=False)
@click.option("-e", "--edit", is_flag=True, help="Edit existing comment.")
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Do not write change to file but show results.",
)
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def comment(
    ctx,
    comment_string: str,
    day_number: int,
    month_number: int,
    year: int,
    edit: bool,
    dry_run: bool,
    verbose: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]
    folder: LedgerFolder = ctx.obj["FOLDER"]
    verbose |= dry_run

    if (
        day := ledger.get_day(day_number, month_number, year)
        if day_number
        else ledger.today
    ):
        if day.comment and not edit:
            sys.exit(
                f"{day.date} already has a comment. "
                "Use flag '--edit' to change existing comment"
            )
        day.comment = comment_string

        if not dry_run:
            _write_month_to_disk(ledger, folder, day.date.year, day.date.month)

        if verbose:
            print("\n" + ledger.last_day.report(include_comments=True) + "\n")


def _write_month_to_disk(
    ledger: Ledger, folder: LedgerFolder, year: int, month_number: int
):
    month = ledger.get_month(month_number, year)

    serialized_month = month.serialize()
    if month_file := folder.months.get(ledger.current_month.key):
        if serialized_month != month_file.content:
            month_file.write(serialized_month)
    else:
        sys.exit("Could not find month file for " f"{year}-{month_number:02}.")


def main():
    locale.setlocale(locale.LC_TIME, "")
    cli(obj={})


if __name__ == "__main__":
    main()