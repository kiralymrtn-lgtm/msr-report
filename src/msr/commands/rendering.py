import typer
from rich.console import Console
console = Console()

from pathlib import Path
from ..utils.paths import local_path
from ..html.builder import render_to_html_file
from ..pdf.html_to_pdf import html_to_pdf
from ..brand import get_brand
from ..data.manifest import load_structure, summarize
from .utils import resolve_brand_css_paths


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
# teljes riport renderelése YAML-ből (több COVER is támogatott)
# ──────────────────────────────────────────────────────────────
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

                # ÚJ: tömb-alapú több-blokkos támogatás és per-slide slot gap
                if c.get("left_blocks"):    section["left_blocks"]  = c["left_blocks"]
                if c.get("right_blocks"):   section["right_blocks"] = c["right_blocks"]
                if c.get("split_slot_gap"): section["split_slot_gap"] = c["split_slot_gap"]

                # Számozott fallback kulcsok másolása (1..3) – left_*/right_* tartalmak
                for i in range(1, 4):
                    ex_key_l = f"left_explain_title{i}"
                    ex_key_r = f"right_explain_title{i}"
                    if ex_key_l in c: section[ex_key_l] = c[ex_key_l]
                    if ex_key_r in c: section[ex_key_r] = c[ex_key_r]

                    for suffix in ("_html", "_paragraph", "_image_path"):
                        ck_l = f"left_content{i}{suffix}"
                        ck_r = f"right_content{i}{suffix}"
                        if ck_l in c: section[ck_l] = c[ck_l]
                        if ck_r in c: section[ck_r] = c[ck_r]

                # Extra: támogatjuk a 'content{i}_*' és 'explain_title{i}' rövid kulcsokat is (jobb oldalra)
                for i in range(1, 4):
                    ex_key = f"explain_title{i}"
                    if ex_key in c: section[ex_key] = c[ex_key]
                    for suffix in ("_html", "_paragraph", "_image_path"):
                        ck = f"content{i}{suffix}"
                        if ck in c: section[ck] = c[ck]

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
# HTML -> PDF
# ──────────────────────────────────────────────────────────────
def pdf_from_html(file: str = typer.Argument(..., help="HTML fájl neve a local/output/html alatt")) -> None:
    """
    a megadott (már létező) HTML-t PDF-fé konvertálja és a local/output/pdf alá menti.
    példa: msr pdf-from-html demo_report.html
    """
    html_file = local_path("output", "html", file)
    pdf_path = html_to_pdf(html_file)
    console.print(f"[green]OK[/green] PDF létrehozva: {pdf_path}")