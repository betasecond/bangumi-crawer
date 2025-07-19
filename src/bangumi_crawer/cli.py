import typer

from .parser import parser_app
from .season import season_app

app = typer.Typer()

app.add_typer(parser_app, name="parser")
app.add_typer(season_app, name="season")


@app.callback()
def main():
    """
    A CLI for interacting with the Bangumi API.
    """
    # This callback will run before any command, acting as a main entry point.
    # You can add global options or context here if needed.
    pass

if __name__ == "__main__":
    app() 