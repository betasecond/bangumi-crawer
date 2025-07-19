import os
from pathlib import Path

import requests
import typer
from dotenv import load_dotenv
from rich.console import Console
import json
import subprocess
import sys

from .models import OpenAPI

parser_app = typer.Typer()
console = Console()


@parser_app.command()
def init():
    """
    init bangumi sdk from swagger file
    """
    console.print("[yellow]Starting init command...[/yellow]")
    console.print(f"Current working directory: {os.getcwd()}")
    load_dotenv()
    console.print("Attempting to load environment variables from .env file.")

    if not (url := os.getenv("BANGUMI_SWAGGER")):
        console.print("[bold red]Error: BANGUMI_SWAGGER is not set in .env file[/bold red]")
        raise typer.Exit(1)

    console.print(f"BANGUMI_SWAGGER found: {url}")
    console.print(f"Fetching swagger file from {url}")

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error fetching swagger file: {e}[/bold red]")
        raise typer.Exit(1)

    console.print(f"Successfully fetched file, status code: {resp.status_code}")
    dist_path = Path("bangumi.json")
    dist_path.write_bytes(resp.content)
    console.print(f"[bold green]Swagger file saved to {dist_path}[/bold green]")
    # todo gen sdk
    console.print("[yellow]Init command finished.[/yellow]")


@parser_app.command()
def parse(
    file: Path = typer.Option(
        "bangumi.json",
        "--file",
        "-f",
        help="Path to the OpenAPI JSON file.",
        exists=True,
        readable=True,
        resolve_path=True,
    )
):
    """
    Parse the OpenAPI specification file.
    """
    console.print(f"Parsing OpenAPI spec from {file}...")
    try:
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        spec = OpenAPI.model_validate(data)
        console.print("[bold green]Successfully parsed the OpenAPI specification.[/bold green]")
        console.print(f"  Title: {spec.info.title}")
        console.print(f"  Version: {spec.info.version}")
        console.print(f"  Servers: {[s.url for s in spec.servers]}")
        console.print(f"  Paths found: {len(spec.paths)}")
        if spec.components.schemas:
            console.print(f"  Schemas found: {len(spec.components.schemas)}")

    except Exception as e:
        console.print(f"[bold red]Error parsing spec file: {e}[/bold red]")
        raise typer.Exit(1)


@parser_app.command()
def generate(
    file: Path = typer.Option(
        "bangumi.json",
        "--file",
        "-f",
        help="Path to the OpenAPI JSON file.",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    output_dir: Path = typer.Option(
        "bangumi_sdk",
        "--output",
        "-o",
        help="Directory to write the generated client to.",
        writable=True,
        resolve_path=True,
    ),
    config_file: Path = typer.Option(
        "openapi-client-config.yaml",
        "--config",
        "-c",
        help="Path to the openapi-python-client config file.",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
):
    """
    Generate a Python client from an OpenAPI specification file.
    """
    console.print(f"Generating Python client from {file}...")
    console.print(f"Output directory: {output_dir}")

    command = [
        "openapi-python-client",
        "generate",
        "--path",
        str(file),
        "--config",
        str(config_file),
        "--output-path",
        str(output_dir),
        "--overwrite",
    ]

    try:
        # Generate the client
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        console.print(process.stdout)
        console.print(
            f"[bold green]Successfully generated Python client in {output_dir}[/bold green]"
        )

        # Install the generated client
        console.print(f"Installing generated client from {output_dir}...")
        install_command = [
            "uv",
            "pip",
            "install",
            "-e",
            str(output_dir),
        ]
        install_process = subprocess.run(
            install_command,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        console.print(install_process.stdout)
        console.print("[bold green]Generated client installed successfully.[/bold green]")

    except subprocess.CalledProcessError as e:
        console.print("[bold red]Error during generation or installation:[/bold red]")
        console.print(e.stderr)
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print(
            "[bold red]Error: 'openapi-python-client' or 'uv' command not found.[/bold red]"
        )
        console.print(
            "Please ensure it is installed and in your PATH. You may need to reactivate your virtual environment."
        )
        raise typer.Exit(1) 