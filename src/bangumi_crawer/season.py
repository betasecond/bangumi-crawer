import calendar
import os
import json
from datetime import date
from pathlib import Path
import time
from typing import Optional

import typer
from dotenv import load_dotenv
from httpx import Timeout
from rich.console import Console
from rich.table import Table

season_app = typer.Typer()
console = Console()


def get_season_air_date_filter(year: int, season: int) -> list[str]:
    """
    Generates the air_date filter strings for the given year and season.
    Season mapping: 1 -> Jan-Mar, 4 -> Apr-Jun, 7 -> Jul-Sep, 10 -> Oct-Dec
    """
    month_map = {1: 1, 4: 4, 7: 7, 10: 10}
    start_month = month_map.get(season)
    if not start_month:
        raise ValueError("Season must be one of 1, 4, 7, 10.")

    end_month = start_month + 2
    _, last_day = calendar.monthrange(year, end_month)

    start_date = date(year, start_month, 1)
    end_date = date(year, end_month, last_day)

    return [f">={start_date.isoformat()}", f"<={end_date.isoformat()}"]


def _fetch_and_display_single_season(
    year: int,
    season: int,
    token: str,
    search_tags: list[str],
    sort_by, # Intentionally left untyped to avoid top-level import
    timeout: Timeout,
):
    """Helper function to fetch, cache, and display data for a single season."""
    # Defer SDK imports until they are actually needed
    from bangumi_api_client import AuthenticatedClient
    from bangumi_api_client.api.条目 import search_subjects
    from bangumi_api_client.models import (
        PagedSubject,
        SearchSubjectsBody,
        SearchSubjectsBodyFilter,
        SubjectType,
    )
    console.print(f"--- Processing {year} Season {season} ---")
    
    # --- Caching Logic ---
    cache_dir = Path("result")
    cache_dir.mkdir(exist_ok=True)
    
    month_map = {1: 1, 4: 4, 7: 7, 10: 10}
    quarter = (month_map.get(season, 0) - 1) // 3 + 1
    safe_tags = "_".join(sorted(search_tags)).replace('-', '_') or "all"
    cache_filename = f"{year}-Q{quarter}-{safe_tags}-{sort_by.value}.json"
    cache_file = cache_dir / cache_filename

    if cache_file.exists():
        console.print(f"[cyan]Found cached result at {cache_file}. Loading from disk...[/cyan]")
        with cache_file.open("r", encoding="utf-8") as f:
            response_data = json.load(f)
        response = PagedSubject.from_dict(response_data)
    else:
        client = AuthenticatedClient(base_url="https://api.bgm.tv", token=token, timeout=timeout)
        try:
            air_date_filter = get_season_air_date_filter(year, season)
        except ValueError as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            raise typer.Exit(1)

        filter_args = {
            "type_": [SubjectType.ANIME],
            "air_date": air_date_filter,
        }
        if search_tags:
            filter_args["tag"] = search_tags

        search_filter = SearchSubjectsBodyFilter(**filter_args)
        search_body = SearchSubjectsBody(
            keyword="",
            sort=sort_by,
            filter_=search_filter,
        )

        with console.status(f"Fetching rankings for {year}, season {season}... (no cache)"):
            with client as c:
                response = search_subjects.sync(client=c, body=search_body, limit=25)
        
        if response:
            console.print(f"[cyan]Saving result to cache file: {cache_file}[/cyan]")
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(response.to_dict(), f, ensure_ascii=False, indent=2)
        
        # Add a small delay to be polite to the API
        time.sleep(1)

    if not response or not response.data:
        console.print("[yellow]No results found for the given season.[/yellow]")
        return

    table = Table(
        "Rank", "Title", "Date", "Score", "URL", title=f"Anime Rankings - {year} Q{quarter}"
    )

    for item in response.data:
        if item.name_cn or item.name:
            title = item.name_cn or item.name
            score = (
                f"{item.rating.score:.2f} ({item.rating.total} votes)"
                if item.rating and item.rating.score and item.rating.total
                else "N/A"
            )
            table.add_row(
                str(item.rating.rank),
                title,
                str(item.date),
                score,
                f"https://bgm.tv/subject/{item.id}",
            )

    console.print(table)


def _parse_year_range(year_str: str) -> list[int]:
    """Parses a year string which can be a single year or a range (e.g., '2022-2023')."""
    if "-" in year_str:
        try:
            start_year, end_year = map(int, year_str.split('-'))
            if start_year > end_year:
                raise ValueError("Start year cannot be greater than end year.")
            return list(range(start_year, end_year + 1))
        except ValueError:
            raise typer.BadParameter("Year range must be in the format YYYY-YYYY (e.g., 2022-2023).")
    else:
        try:
            return [int(year_str)]
        except ValueError:
            raise typer.BadParameter("Year must be a number or a range (e.g., 2023 or 2022-2023).")


@season_app.command()
def get(
    year: str = typer.Option(..., "--year", "-y", help="The year or year range (e.g., 2023 or 2022-2023) to fetch."),
    season: Optional[int] = typer.Option(
        None, "--season", "-s", help="The season to fetch (1, 4, 7, 10). If omitted, all seasons are fetched."
    ),
):
    """
    Fetch and display the anime rankings for a specific season or range of seasons.
    """
    # Import here for sort enum, which is needed before the main loop
    from bangumi_api_client.models import SearchSubjectsBodySort

    load_dotenv()
    token = os.getenv("BANGUMI_ACCESS_TOKEN")
    if not token:
        console.print("[bold red]Error: BANGUMI_ACCESS_TOKEN is not set in .env file.[/bold red]")
        raise typer.Exit(1)

    # Read search settings from .env file
    search_tags_str = os.getenv("BANGUMI_SEARCH_TAGS")
    search_tags = [tag.strip() for tag in search_tags_str.split(',')] if search_tags_str else []
    
    sort_by_str = os.getenv("BANGUMI_SEARCH_SORT_BY", "rank").upper()
    try:
        sort_by = SearchSubjectsBodySort[sort_by_str]
    except KeyError:
        console.print(f"[bold red]Error: Invalid sort option '{sort_by_str}' in BANGUMI_SEARCH_SORT_BY.[/bold red]")
        console.print("Allowed values are: 'match', 'heat', 'rank', 'score'.")
        raise typer.Exit(1)

    # Read timeout from .env file
    try:
        timeout_seconds = int(os.getenv("BANGUMI_REQUEST_TIMEOUT", "30"))
        timeout = Timeout(timeout_seconds)
    except ValueError:
        console.print("[bold red]Error: Invalid timeout value in BANGUMI_REQUEST_TIMEOUT. Must be an integer.[/bold red]")
        raise typer.Exit(1)
    
    console.print(f"Search settings: Tags={search_tags or 'None'}, Sort by={sort_by.value}, Timeout={timeout_seconds}s")
    
    years_to_fetch = _parse_year_range(year)
    seasons_to_fetch = [season] if season else [1, 4, 7, 10]

    for y in years_to_fetch:
        for s in seasons_to_fetch:
            _fetch_and_display_single_season(
                year=y,
                season=s,
                token=token,
                search_tags=search_tags,
                sort_by=sort_by,
                timeout=timeout,
            ) 