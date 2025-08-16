"""
minimális CLI Typer-rel.
parancsok:
- hello: próba
- doctor: létrehozza/ellenőrzi a ./local struktúrát (git-ignored)
"""
import typer
from rich import print
from .utils.paths import local_path, ensure_dir, local_root

app = typer.Typer(help="msr-report – riport generátor")

@app.command("hello")
def hello() -> None:
    """egyszerű próba parancs"""
    print("[green]hello![/green] a CLI működik.")

@app.command("doctor")
def doctor() -> None:
    """
    létrehozza/ellenőrzi a lokális (git-ignored) mappákat:
    - local/assets/{css,logos,backgrounds,fonts}
    - local/data/input
    - local/output/{html,pdf,assets}
    """
    print("[bold]környezet ellenőrzése ('doctor'):[/bold]")
    print(f"local root: {local_root()}")

    folders = [
        local_path("assets", "css"),
        local_path("assets", "logos"),
        local_path("assets", "backgrounds"),
        local_path("assets", "fonts"),
        local_path("data", "input"),
        local_path("output", "html"),
        local_path("output", "pdf"),
        local_path("output", "assets"),
    ]
    for d in folders:
        ensure_dir(d)
        print(f"[green]OK[/green] mappa: {d}")

    print("[bold green]minden rendben![/bold green]")

def main() -> None:
    app()

if __name__ == "__main__":
    main()
