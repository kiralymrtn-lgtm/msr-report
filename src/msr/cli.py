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
import typer
from rich.console import Console
from pathlib import Path
import pandas as pd
from .charts.bar import save_column
from .charts.radar import save_radar

console = Console()

# belső segédek
from .utils.paths import local_path, ensure_dir, local_root
from .html.builder import render_to_html_file
from .pdf.html_to_pdf import html_to_pdf
#from .charts.bar import save_simple_bar  # a render-demo-hoz
from .brand import get_brand
from .data.manifest import load_structure, summarize


def resolve_brand_css_paths() -> list[str]:
    """
    Csak a publikus repo-beli brand.css-t keressük (src/templates/assets/css/brand.css).
    Lokális override-ot NEM használunk, hogy ne zavarjon be.
    """
    repo_css = Path(__file__).resolve().parent.parent / "templates" / "assets" / "css" / "brand.css"
    return [str(repo_css.resolve())] if repo_css.exists() else []

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
    Brandelt CSS: a repo-beli src/templates/assets/css/brand.css kerül betöltésre (nincs local override).
    """
    css_paths = resolve_brand_css_paths()
    if not css_paths:
        console.print("[red]Hiányzik brand.css:[/red] repo-beli 'src/templates/assets/css/brand.css' nem található.")
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
        "brand_css_paths": css_paths,
        "brand_css_path": css_paths[0],
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
    Szükséges fájlok (local/assets alatt):
      - LOGÓ:  local/assets/logos/logo.png
      - BG:    local/assets/backgrounds/cover_bg.png
      - BG2:   local/assets/backgrounds/cover_bg_bottom.png (opcionális)
    A brandelt CSS automatikusan a repo-ból jön: src/templates/assets/css/brand.css
    """
    brand = get_brand()                # központi brand beállítások
    css_paths = resolve_brand_css_paths()
    if not css_paths:
        console.print("[red]Hiányzik brand.css:[/red] repo-beli 'src/templates/assets/css/brand.css' nem található.")
        raise typer.Exit(code=1)
    primary_css = css_paths[0]

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
        "brand_css_paths": css_paths,
        "brand_css_path": primary_css,
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
    css_paths = resolve_brand_css_paths()
    if not css_paths:
        console.print("[red]Hiányzik brand.css:[/red] repo-beli 'src/templates/assets/css/brand.css' nem található.")
        raise typer.Exit(code=1)
    primary_css = css_paths[0]

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
        "brand_css_paths": css_paths,
        "brand_css_path": primary_css,
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
    css_paths = resolve_brand_css_paths()
    if not css_paths:
        console.print("[red]Hiányzik brand.css:[/red] repo-beli 'src/templates/assets/css/brand.css' nem található.")
        raise typer.Exit(code=1)
    primary_css = css_paths[0]

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
        "brand_css_paths": css_paths,
        "brand_css_path": primary_css,
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



@app.command("charts-demo")
def charts_demo(
    xlsx: str = typer.Option(
        "data/input/MCC demo eredmények.xlsx",
        help="Excel helye (relatív a local/ gyökeréhez)",
    ),
    partner_id: str | None = typer.Option(
        None,
        help="Kiemelendő PartnerId (STRING). Ha nincs megadva vagy nem található, az első sort használjuk.",
    ),
) -> None:
    """
    Példa: csoportátlag (column) + kiválasztott partner vs. csoport (radar).
    Kimenet: local/output/assets/charts/*.png
    """
    # 1) adat betöltése
    xls_path = local_path(*xlsx.split("/"))
    if not xls_path.exists():
        console.print(f"[red]Nem találom az Excelt:[/red] {xls_path}")
        raise typer.Exit(code=1)

    df = pd.read_excel(xls_path, sheet_name=0)
    # várjuk: PartnerId + Kérdés1..KérdésN (számok)
    metric_cols = [c for c in df.columns if c.lower().startswith("kérdés")]
    if not metric_cols:
        console.print("[red]Nem találtam 'Kérdés*' oszlopokat az Excelben.[/red]")
        raise typer.Exit(code=1)

    # 2) csoportátlag (column)
    means = df[metric_cols].mean().values.tolist()
    labels = metric_cols
    col_path = save_column(
        values=means, labels=labels,
        title="Csoportátlag kérdésenként",
        y_range=(1, 5),  # tipikus 1–5 Likert
        annotate=True,
        size_cm=(30.0, 10.0),
        filename="group_means.png",
    )
    console.print(f"[green]OK[/green] column: {col_path}")

    # 3) kiválasztott partner vs. csoport (radar)
    pid_col = "PartnerId"
    # PartnerId-k tipikusan alfanumerikusak (pl. "P01203012"). Kezeljük STRING-ként.
    if partner_id:
        row = df.loc[df[pid_col].astype(str) == str(partner_id)]
    else:
        row = pd.DataFrame()  # üres, hogy a fallback ágat aktiváljuk

    if row.empty:
        console.print(
            f"[yellow]Figyelem:[/yellow] nincs ilyen PartnerId: {partner_id!r}, az első sort használom."
        )
        row = df.iloc[[0]]

    pid_for_title = str(row[pid_col].iloc[0])

    series_main = row[metric_cols].iloc[0].tolist()
    series_comp = df[metric_cols].mean().tolist()
    rad_path = save_radar(
        labels=labels,
        series_main=series_main,
        series_comp=series_comp,
        title=f"Partner {pid_for_title} vs. csoport",
        r_range=(1, 5),
        size_cm=(18.0, 18.0),
        filename="partner_vs_group_radar.png",
    )
    console.print(f"[green]OK[/green] radar: {rad_path}")

    console.print("[bold green]Kész![/bold green] A képek a local/output/assets/charts alatt vannak.")
    console.print("Használd a YAML-ben: output/assets/charts/group_means.png  (röviden: írhatsz assets/charts/…-t is; ilyenkor automatikusan az output/ alá mutat).")


# ──────────────────────────────────────────────────────────────
# köszönetnyilvánítás demo (alapesetben 2. oldal)
# ──────────────────────────────────────────────────────────────
@app.command("render-thanks")
def render_thanks() -> None:
    """
    'Köszönetnyilvánítás' oldalt renderel:
    - normál CONTENT háttér (bal felső sáv + jobb felső logó),
    - a törzsben 'text' layout, a szöveg a local/data/content/thanks.html-ből jön.
    """
    # 1) CSS megvan?
    css_paths = resolve_brand_css_paths()
    if not css_paths:
        console.print("[red]Hiányzik brand.css:[/red] repo-beli 'src/templates/assets/css/brand.css' nem található.")
        raise typer.Exit(code=1)
    primary_css = css_paths[0]

    # 2) brand + default content logó (jobb felső sarok)
    brand = get_brand()
    content_logo_path = str(brand.assets.logo_path.resolve()) if brand.assets.logo_path else None

    # 3) köszönet szöveg beolvasása (HTML-ként)
    thanks_file = local_path("data", "content", "thanks.html")
    if not thanks_file.exists():
        console.print(f"[yellow]Figyelem:[/yellow] hiányzik: {thanks_file}")
        console.print("Hozd létre a fájlt (HTML-lel), és futtasd újra.")
        raise typer.Exit(code=1)
    thanks_html = thanks_file.read_text(encoding="utf-8")

    # 4) SECTION – NEM nullázzuk a fejlécet → látszik a 'secondary' sáv
    section = {
        "layout": "text",                 # ← a törzs text-only doboz
        # FEJLÉC (bal felső sáv)
        "header_width":  "66.666%",       # kb. két harmad szélesség
        "header_height": "20mm",          # sáv magassága
        "title_main": "KÖSZÖNETNYILVÁNÍTÁS",  # főcím a sávban (Rubik, CAPS)
        "title_sub":  "",                 # alcím itt most nincs (Times italic lenne)
        # JOBB FELSŐ LOGÓ – megjelenik (ha nem szeretnéd: "hide_logo": True)
        #"logo_height": "14mm",            # tetszőlegesen állítható (brand.css-ben a var-hoz kötve)
        # TEXT LAYOUT finomhangolás (a törzsben) – használjuk a brand.css defaultjait, ne írjuk felül!
        "text_html": thanks_html,         # ← a beolvasott HTML
    }

    # 5) oldalszám: jellemzően 1 cover van előtte → ez legyen 2. oldal
    page_config = {
        "start": 1,
        "pre_content_pages": 1,   # ha cover van előtte
        "enabled": True,
    }

    # Egy 'content' típusú slide-ot is adunk a contexthez a modern sablonhoz
    slide = dict(section)
    slide["kind"] = "content"

    context = {
        "title": "Riport – Köszönetnyilvánítás",
        "brand_css_paths": css_paths,
        "brand_css_path": primary_css,
        "content_logo_path": content_logo_path,
        "slides": [slide],          # ← ÚJ: egységes slide-lista (a sablon elsődlegesen ezt használja)
        "sections": [section],      # ← Fallback a régi sablon útvonalhoz
        "page_config": page_config,
        # NINCS 'cover' a contextben → most csak a content oldalt rendereljük külön
    }

    out_html = render_to_html_file(
        template_name="base.html.j2",
        context=context,
        output_filename="thanks.html",
    )
    console.print(f"[green]OK[/green] HTML létrehozva: {out_html}")
    console.print("→ PDF:  msr pdf-from-html thanks.html")



# ──────────────────────────────────────────────────────────────
# teljes riport renderelése YAML-ből (cover + content)
# ──────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────
# teljes riport renderelése YAML-ből (több COVER is támogatott)
# ──────────────────────────────────────────────────────────────
@app.command("render-structure")
def render_structure(
    struct_path: str = typer.Option(
        None,
        help="Opcionális: egyedi YAML útvonal. Alapértelmezés: local/config/report_structure.yaml",
    )
) -> None:
    """
    Beolvassa a report_structure.yaml-t és a teljes decket egyben rendereli:
    - TÖBB 'cover' oldal is támogatott (mind bekerül a kimenetbe).
    - 'content' oldalak a megszokott fejléc/logó/layout logikával.
    - Oldalszámozás: minden slide beleszámít, de csak a content oldalak JELENÍTIK MEG.
      (page_number = page_config.start + slide_index; a cover is számít, csak nem látszik rajta.)
    Kimenet: local/output/html/report_structure.html
    """
    # 1) CSS ellenőrzés
    css_paths = resolve_brand_css_paths()
    if not css_paths:
        console.print("[red]Hiányzik brand.css:[/red] repo-beli 'src/templates/assets/css/brand.css' nem található.")
        raise typer.Exit(code=1)
    primary_css = css_paths[0]

    # 2) Brand + logó
    brand = get_brand()
    default_logo = str(brand.assets.logo_path.resolve()) if brand.assets.logo_path else None

    # 3) YAML betöltése
    path = Path(struct_path) if struct_path else None
    struct = load_structure(path)
    pages = struct.get("pages", [])
    page_config = struct.get("page_config", {}) or {}

    # 4) Segédfüggvény: relatív local/ → abszolút path
    def _lp(rel: str) -> Path:
        rel = (rel or "").strip("/")
        if not rel:
            return local_path()  # local gyökér
        parts = [p for p in rel.split("/") if p]
        return local_path(*parts)

    # 5) Slides (egységes, sorrendtartó lista: cover VAGY content)
    slides: list[dict] = []

    # opcionális: alsó (második) cover háttér
    bg_bottom = local_path("assets", "backgrounds", "cover_bg_bottom.png")
    bg_bottom_abs = str(bg_bottom.resolve()) if bg_bottom.exists() else None

    for p in pages:
        kind = p.get("kind") or p.get("type")  # támogatjuk a 'type' régi kulcsot is

        if kind == "cover":
            cov = p.get("cover", {})
            title = cov.get("title") or p.get("title")  # fallback a rövid sémára

            if isinstance(title, str):
                title_dict = {"line1": title, "line2": "", "year": ""}
            elif isinstance(title, dict):
                title_dict = {
                    "line1": title.get("line1") or title.get("text") or "",
                    "line2": title.get("line2") or "",
                    "year":  title.get("year")  or "",
                }
            else:
                title_dict = {"line1": "", "line2": "", "year": ""}

            slides.append({
                "kind": "cover",
                "logo_path": default_logo,
                "background_path": str(brand.assets.cover_background_path.resolve()) if brand.assets.cover_background_path else None,
                "background_bottom_path": bg_bottom_abs,
                "title": title_dict,
            })

        elif kind == "content":
            c = p.get("content", {}) or {}
            section: dict = {"kind": "content"}

            # layout
            section["layout"] = c.get("layout") or "split"

            # fejléc (bal felső sáv)
            header = c.get("header") or {}
            show_header = header.get("show", True)
            if "height" in header:
                section["header_height"] = header["height"]
            elif not show_header:
                section["header_height"] = "0mm"
            if "width" in header:
                section["header_width"] = header["width"]
            elif not show_header:
                section["header_width"] = "0%"

            # címek a sávba
            if c.get("title_main"): section["title_main"] = c["title_main"]
            if c.get("title_sub"):  section["title_sub"]  = c["title_sub"]

            # per-oldal logó finomhangolás
            logo = c.get("logo") or {}
            if logo.get("show") is False:
                section["hide_logo"] = True
            if logo.get("height"):    section["logo_height"] = logo["height"]
            if logo.get("right_pad"): section["logo_right_pad"] = logo["right_pad"]

            # TEXT layout tartalom
            if section["layout"] == "text":
                txt = c.get("text") or {}
                if txt.get("max_width"):    section["text_only_max_width"]    = txt["max_width"]
                if txt.get("font_size"):    section["text_only_font_size"]    = txt["font_size"]
                if txt.get("line_height"):  section["text_only_line_height"]  = str(txt["line_height"])
                if txt.get("align"):        section["text_align"]             = txt["align"]
                if txt.get("file"):
                    f = _lp(txt["file"])
                    if not f.exists():
                        console.print(f"[yellow]Figyelem:[/yellow] hiányzik tartalom fájl: {f}")
                    else:
                        section["text_html"] = f.read_text(encoding="utf-8")

            # SPLIT layout tartalom
            if section["layout"] == "split":
                rel = c.get("image_path")
                if rel:
                    # default: resolve relative to local/
                    img = _lp(rel)
                    if not img.exists():
                        # Fallback: if YAML uses "assets/…" assume generated charts live under "output/assets/…"
                        parts = [p for p in rel.split("/") if p]
                        if parts and parts[0] == "assets":
                            img_candidate = local_path("output", *parts)
                            if img_candidate.exists():
                                img = img_candidate
                    section["image_path"] = str(img.resolve()) if img.exists() else str(img)
                if c.get("explain_title"):       section["explain_title"]       = c["explain_title"]
                if c.get("explain_paragraph"):   section["explain_paragraph"]   = c["explain_paragraph"]
                if c.get("explain_html"):        section["explain_html"]        = c["explain_html"]
                if c.get("split_left_width"):    section["split_left_width"]    = c["split_left_width"]
                if c.get("split_gap"):           section["split_gap"]           = c["split_gap"]
                if c.get("explain_title_size"):  section["explain_title_size"]  = c["explain_title_size"]

            slides.append(section)

        elif kind == "closing":
            clos = p.get("closing", {}) or {}

            # általános záró logó (local/assets/logos/logo_general.png), ha nincs: esünk vissza a brand logóra
            logo_general = local_path("assets", "logos", "logo_general.png")
            logo_path = (
                str(logo_general.resolve()) if logo_general.exists()
                else (str(brand.assets.logo_path.resolve()) if brand.assets.logo_path else None)
            )

            slides.append({
                "kind": "closing",
                "logo_path": logo_path,
                # a cover felső rétegét (cover_bg.png) használjuk
                "background_path": (
                    str(brand.assets.cover_background_path.resolve()) if brand.assets.cover_background_path else None
                ),
                # opcionális: YAML-ből jövő saját HTML
                "text_html": clos.get("text_html"),
            })

        else:
            console.print(f"[yellow]Ismeretlen 'kind':[/yellow] {kind!r} – oldal kihagyva.")

    # 6) Page numbering – YAML-ből, vagy defaultok
    page_config.setdefault("enabled", True)
    page_config.setdefault("start", 1)
    # (NINCS szükség pre_content_pages-re, mert a page_no = start + loop.index0 logikát használjuk.)

    # 7) Fallback mezők a régi sablonhoz (ha más parancsok használnák)
    first_cover = next((s for s in slides if s.get("kind") == "cover"), None)
    only_sections = [s for s in slides if s.get("kind") == "content"]

    # 8) Render
    context = {
        "title": "Riport (YAML-ből)",
        "brand_css_paths": css_paths,
        "brand_css_path": primary_css,
        "slides": slides,                          # ← ÚJ: egységes lista
        "cover": first_cover,                      # fallback
        "sections": only_sections,                 # fallback
        "content_logo_path": default_logo,         # jobb felső logó default
        "page_config": page_config,
    }

    out_html = render_to_html_file(
        template_name="base.html.j2",
        context=context,
        output_filename="report_structure.html",
    )
    console.print(f"[green]OK[/green] Teljes riport HTML létrehozva: {out_html}")
    console.print("→ PDF:  msr pdf-from-html report_structure.html")

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
