"""
minimális CLI Typer-rel.
parancsok:
- hello: próba
- doctor: létrehozza/ellenőrzi a ./local struktúrát (git-ignored)
- render-cover-demo: címlap (cover) demó
- render-content-demo: tartalmi oldal (content) demó – sorszámozással
- pdf-from-html: HTML -> PDF konvertálás
- pages-validate: riport struktúra bemutatása
"""
import typer
from rich.console import Console
from pathlib import Path

console = Console()

# belső segédek
from .utils.paths import local_path, ensure_dir, local_root
from .html.builder import render_to_html_file
from .pdf.html_to_pdf import html_to_pdf
from .charts.bar import save_simple_bar  # a render-demo-hoz
from .brand import get_brand


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
# egyszerű demo (grafikonnal)
# ──────────────────────────────────────────────────────────────
@app.command("render-demo")
def render_demo() -> None:
    """
    minimál demo HTML-riport a local/output/html alá (base.html.j2 sablonból).
    brandelt CSS: local/assets/css/brand.css
    """
    brand_css_path = local_path("assets", "css", "brand.css")
    if not brand_css_path.exists():
        console.print(f"[red]Hiányzik a CSS:[/red] {brand_css_path}")
        console.print("Hozd létre: local/assets/css/brand.css (brand színek, tipó stb.)")
        raise typer.Exit(code=1)

    # demo adatok + grafikon
    demo_labels = ["Q1", "Q2", "Q3", "Q4"]
    demo_values = [3.8, 4.2, 4.6, 4.0]
    chart_path = save_simple_bar(
        values=demo_values,
        labels=demo_labels,
        highlight_index=2,          # pl. „saját/csoport” kiemelése a 3. oszlopon
        usable_width_cm=30.0,       # a Te lapod hasznos szélessége
        height_cm=10.0,
        filename="bar_demo.png"
    )

    context = {
        "title": "Riport (demo)",
        "report_title": "Piaci felmérés – Demo",
        "report_subtitle": "HTML → PDF cső próba",
        "prepared_for": "Belső használatra",
        "brand_css_path": str(brand_css_path.resolve()),
        "sections": [
            {
                "title": "Bevezetés",
                "text": "Ez egy próbaszekció...",
                "cards": [
                    {
                        "title": "Kiemelt pont",
                        "text": "Itt később dinamikus tartalom...",
                        "image_path": str(chart_path.resolve()),  # itt az ábra
                        "table": [
                            ["Mutató", "Érték"],
                            ["Összes átlag", "4.1"],
                            ["Saját/csoport átlag", "4.6"],
                        ],
                    }
                ],
            }
        ],
    }

    out_html = render_to_html_file(
        template_name="base.html.j2",
        context=context,
        output_filename="demo_report.html",
    )
    console.print(f"[green]OK[/green] HTML létrehozva: {out_html}")


# ──────────────────────────────────────────────────────────────
# HTML -> PDF
# ──────────────────────────────────────────────────────────────
@app.command("pdf-from-html")
def pdf_from_html(file: str = typer.Argument(..., help="HTML fájl neve a local/output/html alatt")) -> None:
    """
    a megadott (már létező) HTML-t PDF-fé konvertálja és a local/output/pdf alá menti.
    példa: msr pdf-from-html demo_report.html
    """
    html_file = local_path("output", "html", file)
    pdf_path = html_to_pdf(html_file)
    console.print(f"[green]OK[/green] PDF létrehozva: {pdf_path}")


# ──────────────────────────────────────────────────────────────
# cover demó (két rétegű háttér + felső fehér logósáv + 3-részes cím)
# ──────────────────────────────────────────────────────────────
@app.command("render-cover-demo")
def render_cover_demo() -> None:
    """
    CÍMLAP DEMÓ: háttér + logó + címblokk.
    szükséges fájlok (local/assets alatt):
      - CSS:   local/assets/css/brand.css
      - LOGÓ:  local/assets/logos/logo.png
      - BG:    local/assets/backgrounds/cover_bg.png
      - BG2:   local/assets/backgrounds/cover_bg_bottom.png (opcionális)
    """
    brand = get_brand()                # központi brand beállítások
    brand.assets.ensure_css()          # a CSS-nek léteznie kell

    missing = brand.assets.missing_assets()
    if missing:
        console.print("[yellow]Figyelem – hiányzó asset(ek):[/yellow]")
        for m in missing:
            console.print(f"  - {m}")
        console.print("Ahol hiányzik, ott egyszerűen háttér/logó nélkül renderelünk.")

    bg_bottom = local_path("assets", "backgrounds", "cover_bg_bottom.png")
    if not bg_bottom.exists():
        console.print("[yellow]Figyelem:[/yellow] nincs második háttér (cover_bg_bottom.png) – csak a felső réteg jelenik meg.")

    context = {
        "title": "Riport (demo cover)",
        "brand_css_path": str(brand.assets.css_path.resolve()),
        "cover": {
            "logo_path": str(brand.assets.logo_path.resolve()) if brand.assets.logo_path else None,
            "background_path": str(brand.assets.cover_background_path.resolve()) if brand.assets.cover_background_path else None,
            "background_bottom_path": str(bg_bottom.resolve()) if bg_bottom.exists() else None,
            "title": {
                "line1": "VÁLLALKOZÓI",
                "line2": "egyedi riport",
                "year":  "2025",
            },
        },
        "sections": [],
        # fontos: a cover sosem jelenít meg oldalszámot, de beleszámíthat a sorszámozásba (lásd render_content_demo)
    }

    out_html = render_to_html_file(
        template_name="base.html.j2",
        context=context,
        output_filename="demo_cover.html",
    )
    console.print(f"[green]OK[/green] Cover HTML létrehozva: {out_html}")
    console.print("→ Készíts PDF-et ezzel:  msr pdf-from-html demo_cover.html")


# ──────────────────────────────────────────────────────────────
# content demó (fejléc-sáv + jobb felső logó + sorszámozás)
# ──────────────────────────────────────────────────────────────
@app.command("render-content-demo")
def render_content_demo() -> None:
    """
    Csak content oldalak (cover nélkül), hogy lásd a sorszámozást.
    Itt a page_config.pre_content_pages = 0, mert nincs cover az elején.
    """
    # 1) CSS ellenőrzés
    brand_css_path = local_path("assets", "css", "brand.css")
    if not brand_css_path.exists():
        console.print(f"[red]Hiányzik a CSS:[/red] {brand_css_path}")
        raise typer.Exit(code=1)

    # 2) BRAND + alapértelmezett content-logó
    brand = get_brand()
    content_logo_path = str(brand.assets.logo_path.resolve()) if brand.assets.logo_path else None

    # 3) Formai váz (nincs kép/tábla, csak fejléc + test)
    sections = [
        {
            "header_width":  "66.666%",
            "header_height": "20mm",
            "title_main": "VÁLLALATI",
            "title_sub":  "teljesítmény az elmúlt 12 hónapban",
            # opcionális per-oldal finomhangolás:
            # "logo_height": "10mm",   # → jobb felső sarokban lévő logó fix magassága
            # "title_main_size": "9mm",
            # "title_sub_size":  "7mm",
        },
    ]

    # 4) Oldalszámozás beállítás (csak content oldalak jelenítik meg)
    page_config = {
        "start": 1,               # az első számozott oldal száma
        "pre_content_pages": 0,   # cover nincs előttünk, így 0
        "enabled": True,          # mutassuk az oldalszámot
    }

    # 5) Render
    context = {
        "title": "Riport (content demo – váz)",
        "brand_css_path": str(brand_css_path.resolve()),
        "content_logo_path": content_logo_path,
        "sections": sections,
        "page_config": page_config,
        # fontos: NINCS 'cover' kulcs → a cover nem jelenik meg
    }

    out_html = render_to_html_file(
        template_name="base.html.j2",
        context=context,
        output_filename="demo_content.html",
    )
    console.print(f"[green]OK[/green] Content HTML (váz) létrehozva: {out_html}")
    console.print("→ PDF:  msr pdf-from-html demo_content.html")


# ──────────────────────────────────────────────────────────────
# cover and content demo (cover + 2 minta oldal)
# ──────────────────────────────────────────────────────────────
@app.command("render-cover-and-content-demo")
def render_cover_and_content_demo() -> None:
    """
    Cover + 2 content oldal demó, helyes oldalszámozással.
    A cover NEM jelenít meg oldalszámot, de beleszámít (cover = 1, utána első content = 2).
    """
    # 1) CSS ellenőrzés
    brand_css_path = local_path("assets", "css", "brand.css")
    if not brand_css_path.exists():
        console.print(f"[red]Hiányzik a CSS:[/red] {brand_css_path}")
        raise typer.Exit(code=1)

    brand = get_brand()
    content_logo_path = str(brand.assets.logo_path.resolve()) if brand.assets.logo_path else None

    # 2) Cover assetek (felső + alsó háttér opcionális)
    bg_bottom = local_path("assets", "backgrounds", "cover_bg_bottom.png")
    cover = {
        "logo_path": str(brand.assets.logo_path.resolve()) if brand.assets.logo_path else None,
        "background_path": str(brand.assets.cover_background_path.resolve()) if brand.assets.cover_background_path else None,
        "background_bottom_path": str(bg_bottom.resolve()) if bg_bottom.exists() else None,
        "title": {
            "line1": "VÁLLALKOZÓI",
            "line2": "egyedi riport",
            "year":  "2025",
        },
    }

    # 3) Két egyszerű content oldal
    sections = [
        {
            "header_width":  "66.666%",
            "header_height": "20mm",
            "title_main": "VÁLLALATI",
            "title_sub":  "teljesítmény az elmúlt 12 hónapban",
        },
        {
            "header_width":  "66.666%",
            "header_height": "20mm",
            "title_main": "MEGÍTÉLÉS",
            "title_sub":  "ügyfél-visszajelzések összegzése",
        },
    ]

    # 4) Oldalszámozás:
    #    - a cover az 1. oldal (nem jelenít meg számot)
    #    - az utána következő első content tehát 2-es számot kap
    page_config = {
        "start": 1,               # kezdő sorszám
        "pre_content_pages": 1,   # cover az elején → 1
        "enabled": True,          # content oldalakon jelenjen meg
    }

    # 5) Render
    context = {
        "title": "Riport (cover + content demo)",
        "brand_css_path": str(brand_css_path.resolve()),
        "cover": cover,
        "content_logo_path": content_logo_path,
        "sections": sections,
        "page_config": page_config,
    }

    out_html = render_to_html_file(
        template_name="base.html.j2",
        context=context,
        output_filename="demo_cover_content.html",
    )
    console.print(f"[green]OK[/green] Cover+Content HTML létrehozva: {out_html}")
    console.print("→ PDF:  msr pdf-from-html demo_cover_content.html")



# ──────────────────────────────────────────────────────────────
# oldalszerkezet ellenőrzése (YAML) – csak listáz
# ──────────────────────────────────────────────────────────────
from .data.manifest import load_structure, summarize  # ← tedd a többi import közé

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
        label = "COVER " if kind == "cover" else "CONTENT"
        if kind == "cover":
            t = p.get("cover", {}).get("title", {})
            title_preview = " ".join(x for x in [t.get("line1"), t.get("line2"), t.get("year")] if x)
        else:
            c = p.get("content", {})
            title_preview = " ".join(x for x in [c.get("title_main"), c.get("title_sub")] if x)

        console.print(f"{idx:>2}. {label:8} {title_preview}")



def main() -> None:
    app()


if __name__ == "__main__":
    main()
