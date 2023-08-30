import datetime
import locale
import sys
from pathlib import Path
from typing import Optional

import click
from tabulate import tabulate

from heath.day import Day
from heath.exceptions import ProjectError
from heath.folder import LedgerFolder
from heath.ledger import Ledger
from heath.shift import Shift
from heath.time_period import CustomTimePeriod


@click.group()
@click.option("-f", "--folder", type=Path, envvar="HEATH_FOLDER")
@click.option("-V", "--validate", is_flag=True)
@click.pass_context
def cli(ctx, folder: Path, validate: bool):
    if not folder:
        folder = Path.cwd()
    ledger_folder = LedgerFolder(folder)
    if validate:
        print(str(ledger_folder) + "\n")

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


@cli.command(help="Show ledger for year.")
@click.argument("year", type=int, required=False)
@click.option(
    "-a",
    "--include_active_day",
    is_flag=True,
    help="Show current duration for any non complete day.",
)
@click.option("-p", "--by-project", is_flag=True, help="Group by project per day.")
@click.option(
    "-P",
    "--by-project-total",
    is_flag=True,
    help="Group by project for the whole year.",
)
@click.option("-s", "--stats", is_flag=True, help="Show statistics.")
@click.option("-o", "--overview", is_flag=True, help="Brief overview of year.")
@click.pass_context
def year(
    ctx,
    year: Optional[int],
    include_active_day: bool,
    by_project: bool,
    by_project_total: bool,
    stats: bool,
    overview: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]

    year_ledger = ledger.get_year(year) if year else ledger.current_year

    if stats:
        report = year_ledger.statistics_report()
    elif overview:
        report = year_ledger.overview()
    else:
        report = year_ledger.report(
            include_active_day=include_active_day,
            by_project=by_project,
            by_project_total=by_project_total,
        )
    print("\n" + report + "\n")


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
@click.option("-p", "--by-project", is_flag=True, help="Group by project per day.")
@click.option(
    "-P",
    "--by-project-total",
    is_flag=True,
    help="Group by project for the whole month.",
)
@click.option("-s", "--stats", is_flag=True, help="Show statistics.")
@click.option("-o", "--overview", is_flag=True, help="Brief overview of month.")
@click.pass_context
def month(
    ctx,
    month_number: Optional[int],
    year: Optional[int],
    include_active_day: bool,
    include_comments: bool,
    by_project: bool,
    by_project_total: bool,
    stats: bool,
    overview: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]

    month_ledger = (
        ledger.get_month(month_number, year) if month_number else ledger.current_month
    )

    if stats:
        report = month_ledger.statistics_report()
    elif overview:
        report = month_ledger.overview()
    else:
        report = month_ledger.report(
            include_active_day=include_active_day,
            include_comments=include_comments,
            by_project=by_project,
            by_project_total=by_project_total,
        )
    print("\n" + report + "\n")


@cli.command(help="Show ledger for custom interval.")
@click.argument("start_date", type=str)
@click.argument("end_date", type=str)
@click.option(
    "-a",
    "--include_active_day",
    is_flag=True,
    help="Show current duration for any non complete day.",
)
@click.option(
    "-c", "--include-comments", is_flag=True, help="Show any comments for days."
)
@click.option("-p", "--by-project", is_flag=True, help="Group by project per day.")
@click.option(
    "-P",
    "--by-project-total",
    is_flag=True,
    help="Group by project for the whole interval.",
)
@click.option("-s", "--stats", is_flag=True, help="Show statistics.")
@click.option("-o", "--overview", is_flag=True, help="Brief overview of interval.")
@click.pass_context
def interval(
    ctx,
    start_date: str,
    end_date: str,
    include_active_day: bool,
    include_comments: bool,
    by_project: bool,
    by_project_total: bool,
    stats: bool,
    overview: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]

    interval_ledger = ledger.get_custom_time_period(
        datetime.datetime.strptime(start_date, "%Y-%m-%d").date(),
        datetime.datetime.strptime(end_date, "%Y-%m-%d").date(),
    )

    if stats:
        report = interval_ledger.statistics_report()
    elif overview:
        report = interval_ledger.overview()
    else:
        report = interval_ledger.report(
            include_active_day=include_active_day,
            include_comments=include_comments,
            by_project=by_project,
            by_project_total=by_project_total,
        )

    print("\n" + report + "\n")


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
@click.option("-p", "--by-project", is_flag=True, help="Group by project per day.")
@click.option(
    "-P",
    "--by-project-total",
    is_flag=True,
    help="Group by project for the whole week.",
)
@click.option("-s", "--stats", is_flag=True, help="Show statistics.")
@click.option("-o", "--overview", is_flag=True, help="Brief overview of week.")
@click.pass_context
def week(
    ctx,
    week_number: Optional[int],
    year: Optional[int],
    include_active_day: bool,
    include_comments: bool,
    by_project: bool,
    by_project_total: bool,
    stats: bool,
    overview: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]

    week_ledger = (
        ledger.get_week(week_number, year)
        if week_number is not None
        else ledger.current_week
    )

    if stats:
        report = week_ledger.statistics_report()
    elif overview:
        report = week_ledger.overview()
    else:
        report = week_ledger.report(
            include_active_day=include_active_day,
            include_comments=include_comments,
            by_project=by_project,
            by_project_total=by_project_total,
        )

    print("\n" + report + "\n")


@cli.command(help="Show ledger for day.")
@click.argument("day_number", type=click.IntRange(1, 31), required=False)
@click.argument("month_number", type=click.IntRange(1, 12), required=False)
@click.argument("year_number", type=int, required=False)
@click.option(
    "-a",
    "--include_active_shift",
    is_flag=True,
    help="Show current duration for any non complete shift.",
)
@click.option(
    "-c", "--include-comments", is_flag=True, help="Show any comment for day."
)
@click.option("-p", "--by-project", is_flag=True, help="Sum worked hours by project.")
@click.option("-o", "--overview", is_flag=True, help="Brief overview of day.")
@click.pass_context
def day(
    ctx,
    day_number: Optional[int],
    month_number: Optional[int],
    year_number: Optional[int],
    include_active_shift: bool,
    include_comments: bool,
    by_project: bool,
    overview: bool,
):
    ledger: Ledger = ctx.obj["LEDGER"]

    if (
        day_ledger := ledger.get_day(day_number, month_number, year_number)
        if day_number
        else ledger.today
    ):
        if overview:
            week_year, week_number, _ = day_ledger.date.isocalendar()
            days_in_week = [
                d
                for d in ledger.get_week(week_number, week_year).all_days
                if d.date <= day_ledger.date
            ]
            partial_week = CustomTimePeriod(
                days_in_week[0].date, days_in_week[-1].date, days_in_week
            )
            day_string = day_ledger.overview(week_balance=partial_week.balance)
        else:
            day_string = day_ledger.report(
                include_active_shift=include_active_shift,
                include_comments=include_comments,
                by_project=by_project,
            )
        print("\n" + day_string + "\n")

    else:
        print("No information for day.")


@cli.command(help="List all known projects.")
@click.pass_context
def projects(ctx):
    ledger: Ledger = ctx.obj["LEDGER"]
    projects_data = [
        (
            project.key,
            project.name,
            ("No", "Yes")[project.all_day],
            project.description,
        )
        for project in sorted(ledger.projects.values(), key=lambda p: p.key)
    ]
    print(
        "\n"
        + tabulate(
            projects_data,
            headers=("Projekt", "Rapporteras som", "Heldag", "Beskrivning"),
        )
        + "\n"
    )


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

    new_shift = Shift(ledger.get_project(project), ledger.last_day.date)
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


@cli.command(help="Switch to a new shift.")
@click.argument("project")
@click.argument("start_time")
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Do not write change to file but show results.",
)
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def switch(ctx, project: str, start_time: str, dry_run: bool, verbose: bool):
    ledger: Ledger = ctx.obj["LEDGER"]
    folder: LedgerFolder = ctx.obj["FOLDER"]
    verbose |= dry_run

    if ledger.current_shift.completed:
        sys.exit("There is no ongoing shift to switch from.")

    new_shift = Shift(ledger.get_project(project), ledger.last_day.date)
    switch_datetime = datetime.datetime.combine(
        new_shift.date,
        datetime.time(*(int(number) for number in start_time.split(":"))),
    )

    ledger.current_shift.stop(switch_datetime)

    new_shift.start(switch_datetime)
    ledger.last_day.add_shift(new_shift)

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
        all_day_project = ledger.get_project(project, all_day=True)
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
        folder.next_month.write(serialized_month)


def main():
    locale.setlocale(locale.LC_TIME, "")
    cli(obj={})


if __name__ == "__main__":
    main()
