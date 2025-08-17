"""
minimális CLI Typer-rel.
parancsok:
- hello: próba
- doctor: létrehozza/ellenőrzi a ./local struktúrát (git-ignored)
- render-cover-demo: címlap (cover) demó
- render-content-demo: tartalmi oldal (content) demó – sorszámozással
- pdf-from-html: HTML -> PDF konvertálás
"""
import typer
from rich.console import Console

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
    tartalmi oldal demó (formai váz): bal felső sárga sáv + cím, jobb felső logó,
    és oldalszámozás a lap alján középen (a cover NEM jelenik meg, de ha lenne,
    a sorszámba beleszámíthatjuk).
    """
    # 1) css ellenőrzés
    brand_css_path = local_path("assets", "css", "brand.css")
    if not brand_css_path.exists():
        console.print(f"[red]Hiányzik a CSS:[/red] {brand_css_path}")
        raise typer.Exit(code=1)

    # 2) brand és default content logó
    brand = get_brand()
    content_logo_path = str(brand.assets.logo_path.resolve()) if brand.assets.logo_path else None

    # 3) egy példa tartalmi oldal – CSAK formai váz
    section = {
        "header_width":  "66.666%",                 # bal felső sáv szélesség
        "header_height": "20mm",                    # bal felső sáv magasság
        "title_main": "VÁLLALATI",                  # főcím (Rubik, CAPS)
        "title_sub":  "teljesítmény az elmúlt 12 hónapban",  # alcím (Times, italic)
        # jobb felső logó oldalanként állítható magassága:
        "logo_height": "8mm",                      # ← ha kihagyod, a CSS fallback érvényesül
        # "hide_logo": True,                        # ← ezzel el is rejtheted az adott oldalon
    }

    # 4) context összeállítás
    context = {
        "title": "Riport (content demo – váz)",
        "brand_css_path": str(brand_css_path.resolve()),
        "content_logo_path": content_logo_path,     # default content logó (coveren NEM jelenik meg)
        # oldalszámozás beállításai:
        # - start: honnan induljon a számozás
        # - enabled: globális ki/bekapcsolás
        # - pre_content_pages: NEM adjuk meg → a sablon automatikusan 1-et számol,
        #   ha lenne cover (mert: pre_content_pages = 1 if cover else 0).
        "page_config": {
            "start": 1,
            "enabled": True,
            # "pre_content_pages": 1,  # ha mindenáron felül akarod írni (pl. több előoldal van)
        },
        "sections": [section],
        # fontos: NINCS 'cover' kulcs → most nem renderelünk címlapot
    }

    # 5) render
    out_html = render_to_html_file(
        template_name="base.html.j2",
        context=context,
        output_filename="demo_content.html",
    )
    console.print(f"[green]OK[/green] Content HTML (váz) létrehozva: {out_html}")
    console.print("→ PDF:  msr pdf-from-html demo_content.html")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
