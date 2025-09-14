"""
minimális CLI Typer-rel.
parancsok:
- hello: próba
- doctor: létrehozza/ellenőrzi a ./local struktúrát (git-ignored)
- render-cover-demo: címlap (cover) demó
- render-content-demo: tartalmi oldal (content) demó – sorszámozással
- pdf-from-html: HTML -> PDF konvertálás
- pages-validate: riport struktúra bemutatása
- render-structure: teljes riport a YAML-manifesztből
"""
import typer, yaml
from rich.console import Console
from pathlib import Path

console = Console()

# belső segédek
from .utils.paths import local_path, ensure_dir, local_root
from .utils.templating import format_tree
from .data.manifest import load_structure, summarize
from .commands.utils import resolve_brand_css_paths
from .commands import rendering as R
from .commands import charts as C
from .commands.charts_from_yaml import charts_from_yaml


app = typer.Typer(help="msr-report – riport generátor")


# ──────────────────────────────────────────────────────────────
# alapparancsok
# ──────────────────────────────────────────────────────────────
@app.command("hello")
def hello() -> None:
    """egyszerű próba parancs"""
    console.print("[green]hello![/green] a CLI működik.")


@app.command("doctor")
def doctor() -> None:
    """
    létrehozza/ellenőrzi a lokális (git-ignored) mappákat:
    - local/assets/{css,logos,backgrounds,fonts}
    - local/data/input
    - local/output/{html,pdf,assets}
    """
    console.print("[bold]környezet ellenőrzése ('doctor'):[/bold]")
    console.print(f"local root: {local_root()}")

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
        console.print(f"[green]OK[/green] mappa: {d}")

    console.print("[bold green]minden rendben![/bold green]")

# ──────────────────────────────────────────────────────────────
# HTML -> PDF
# ──────────────────────────────────────────────────────────────
@app.command("pdf-from-html")
def cmd_pdf_from_html(file: str = typer.Argument(..., help="HTML fájl neve a local/output/html alatt")):
    R.pdf_from_html(file)


# ──────────────────────────────────────────────────────────────
# cover demó (két rétegű háttér + felső fehér logósáv + 3-részes cím)
# ──────────────────────────────────────────────────────────────
@app.command("render-cover-demo")
def cmd_render_cover_demo():
    R.render_cover_demo()


# ──────────────────────────────────────────────────────────────
# content demó (fejléc-sáv + jobb felső logó + sorszámozás)
# ──────────────────────────────────────────────────────────────
@app.command("render-content-demo")
def cmd_render_content_demo():
    R.render_content_demo()


# ──────────────────────────────────────────────────────────────
# cover and content demo (cover + 2 minta oldal)
# ──────────────────────────────────────────────────────────────
@app.command("render-cover-and-content-demo")
def cmd_render_cover_and_content_demo():
    R.render_cover_and_content_demo()


# ──────────────────────────────────────────────────────────────
# charts demo ()
# ──────────────────────────────────────────────────────────────
@app.command("charts-demo")
def cmd_charts_demo(
    xlsx: str = typer.Option("data/input/MCC demo eredmények.xlsx",
                             help="Excel helye (relatív a local/ gyökeréhez)"),
    partner_id: str | None = typer.Option(None, help="Kiemelendő PartnerId (STRING)…"),
):
    C.charts_demo(xlsx=xlsx, partner_id=partner_id)


# ──────────────────────────────────────────────────────────────
# köszönetnyilvánítás demo (alapesetben 2. oldal)
# ──────────────────────────────────────────────────────────────
@app.command("render-thanks")
def cmd_render_thanks():
    R.render_thanks()


# ──────────────────────────────────────────────────────────────
# teljes riport renderelése YAML-ből (több COVER is támogatott)
# ──────────────────────────────────────────────────────────────
@app.command("render-structure")
def cmd_render_structure(
    struct_path: str = typer.Option(
        None, help="Opcionális: egyedi YAML útvonal. Alapértelmezés: local/config/report_structure.yaml"
    ),
    partner_id: str | None = typer.Option(
        None, "--partner-id", help="Helyettesítő változó a YAML-ben (pl. {partner})."
    ),
):
    fmt_ctx = {"partner": partner_id} if partner_id else None
    R.render_structure(struct_path, fmt_ctx=fmt_ctx)

# ──────────────────────────────────────────────────────────────
# chart-ok renderelése YAML-ből
# ──────────────────────────────────────────────────────────────
app.command("charts-from-yaml")(charts_from_yaml)


# ──────────────────────────────────────────────────────────────
# oldalszerkezet ellenőrzése (YAML) – csak listáz
# ──────────────────────────────────────────────────────────────
@app.command("pages-validate")
def pages_validate(struct_path: str = typer.Option(
    None,
    help="Opcionális: egyedi YAML útvonal. Alapértelmezés: local/config/report_structure.yaml"
)) -> None:
    """
    Beolvassa a local/config/report_structure.yaml fájlt és kilistázza az oldalakat:
    sorszám, típus (COVER/CONTENT), és a címek kivonata.
    """
    # 1) betöltés
    path = Path(struct_path) if struct_path else None
    struct = load_structure(path)
    pages = struct["pages"]

    # 2) összegzés
    total, covers, contents = summarize(struct)
    console.print(f"[bold]Manifeszt:[/bold] {struct['path']}")
    console.print(f"Összes oldal: [cyan]{total}[/cyan]  |  Cover: [magenta]{covers}[/magenta]  |  Content: [green]{contents}[/green]")
    console.print("-" * 60)

    # 3) részletes lista
    for idx, p in enumerate(pages, start=1):
        kind = p["kind"]
        if kind == "cover":
            label = "COVER   "
        elif kind == "content":
            label = "CONTENT "
        elif kind == "closing":
            label = "CLOSING "
        else:
            label = f"{kind.upper():8}"
        if kind == "cover":
            t = p.get("cover", {}).get("title", {})
            title_preview = " ".join(x for x in [t.get("line1"), t.get("line2"), t.get("year")] if x)
        elif kind == "content":
            c = p.get("content", {})
            title_preview = " ".join(x for x in [c.get("title_main"), c.get("title_sub")] if x)
        elif kind == "closing":
            # No title fields; could optionally show a fixed string or empty
            title_preview = ""
        else:
            title_preview = ""

        console.print(f"{idx:>2}. {label:8} {title_preview}")



def main() -> None:
    app()


if __name__ == "__main__":
    main()
