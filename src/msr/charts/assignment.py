from __future__ import annotations
from typing import Sequence
from pathlib import Path
import pandas as pd

from ..data.loaders import find_pairs, label_map_from_dict  # ezek a korábbi segédek
from ..utils.paths import local_path, ensure_dir
from ..charts.theme import apply_minimal_theme, DEFAULT_PALETTE
from ..charts.bar import save_column, save_bar
from ..charts.radar import save_radar
from ..charts.table import save_partner_group_table


def _build_series_for_metrics(
    db: pd.DataFrame,
    ddf: pd.DataFrame,
    row_index: int,
    metrics: Sequence[str],
    avg_pairs: dict[str, str] | None = None,
    *,
    mode: str = "pair",
    labels_override: Sequence[str] | None = None,
) -> tuple[list[str], list[float], list[float] | None]:
    """
    Visszaadja a (labels, partner_értékek, csoport_értékek_vagy_None) hármast.
    - mode="pair": csak akkor vesz fel egy metrikát, ha van hozzá átlag pár is az adatbázisban.
    - mode="single": nem használ összehasonlítást.
    - labels_override: ha meg van adva (YAML-ből), akkor azt használja a label-ekhez; egyébként a ddf-ből képzett map alapján dolgozik.
    """
    L = label_map_from_dict(ddf)

    # Ha a YAML adott labels-t, akkor azt preferáljuk, különben ddf map
    if labels_override is not None:
        lo = list(labels_override)
        # szükség esetén igazítsuk a hosszát a metrics-hez
        if len(lo) < len(metrics):
            lo += [L.get(m, m) for m in metrics[len(lo):]]
        elif len(lo) > len(metrics):
            lo = lo[:len(metrics)]
    else:
        lo = [L.get(m, m) for m in metrics]

    labels: list[str] = []
    s_main: list[float] = []
    s_comp: list[float] = []

    if mode == "pair":
        avg_pairs = avg_pairs or {}
        for base, lab in zip(metrics, lo):
            # csak akkor vesszük fel, ha a pár oszlop is létezik
            if base in db.columns and base in avg_pairs and avg_pairs[base] in db.columns:
                labels.append(lab)
                s_main.append(db.loc[row_index, base])
                s_comp.append(db.loc[row_index, avg_pairs[base]])
        return labels, s_main, s_comp
    else:
        # single mód: nincs összehasonlítás
        for base, lab in zip(metrics, lo):
            if base in db.columns:
                labels.append(lab)
                s_main.append(db.loc[row_index, base])
        return labels, s_main, None

def _fmt_filename(name: str, partner_id: str | None) -> str:
    if not name:
        return "chart.png"
    if partner_id is None:
        return name
    try:
        return name.format(partner=str(partner_id), partner_id=str(partner_id))
    except KeyError:
        return name

def render_assignment(
    *,
    db: pd.DataFrame,
    ddf: pd.DataFrame,
    row_index: int,
    assignment: dict,
    partner_id: str | None = None,
    out_dir_charts: Path | None = None,
    out_dir_tables: Path | None = None,
) -> dict[str, list[Path]]:
    avg_pairs = find_pairs(db, suffix="_átlag")
    results: dict[str, list[Path]] = {"radar": [], "column": [], "bar": [], "table": []}
    out_dir_charts = out_dir_charts or local_path("output", "assets", "charts")
    out_dir_tables = out_dir_tables or local_path("output", "assets", "tables")
    ensure_dir(out_dir_charts); ensure_dir(out_dir_tables)
    apply_minimal_theme()

    # RADAR
    for spec in assignment.get("radar", []):
        mode = "pair" if spec.get("source_type") == "pair" else "single"
        # Per-chart style overrides (palette + size)
        pal = {**DEFAULT_PALETTE, **(spec.get("palette") or {})}
        # Shorthand: main_color felülírja a fő sorozat (secondary) színét
        if spec.get("main_color"):
            pal["secondary"] = spec["main_color"]
        size_cm = tuple(spec["size_cm"]) if spec.get("size_cm") else None
        pairs = find_pairs(db, suffix=spec.get("compare_suffix", "_átlag")) if mode == "pair" else None
        labels, s_main, s_comp = _build_series_for_metrics(
            db, ddf, row_index, spec["metrics"], pairs, mode=mode, labels_override=spec.get("labels")
        )
        # Fallback: ha pair-t kértünk, de nincs egyetlen összepárosítható metrika sem,
        # essünk vissza single módra, hogy legalább a partner értékek kirajzolódjanak.
        if not labels and mode == "pair":
            labels, s_main, s_comp = _build_series_for_metrics(
                db, ddf, row_index, spec["metrics"], None, mode="single", labels_override=spec.get("labels")
            )
        if not labels:
            continue
        p = save_radar(
            labels=labels,
            series_main=s_main,
            series_comp=(s_comp if mode == "pair" else None),
            size_cm=size_cm,
            title=spec.get("title"),
            filename=_fmt_filename(spec.get("filename", "radar.png"), partner_id),
            r_range=spec.get("r_range"),
            legend_below=spec.get("legend_below", True),
            legend_pad=spec.get("legend_pad", 0.12),
            legend_ncol=spec.get("legend_ncol", 2),
            palette=pal,
        )
        results["radar"].append(p)

    # COLUMN: partner oszlop + csoport overlay vonal
    for spec in assignment.get("column", []):
        mode = "pair" if spec.get("source_type") == "pair" else "single"
        pairs = find_pairs(db, suffix=spec.get("compare_suffix", "_átlag")) if mode == "pair" else None
        # Per-chart style overrides (palette + size + overlay color)
        pal = {**DEFAULT_PALETTE, **(spec.get("palette") or {})}
        if spec.get("main_color"):
            pal["secondary"] = spec["main_color"]
        size_cm = tuple(spec["size_cm"]) if spec.get("size_cm") else None
        labels, s_main, s_comp = _build_series_for_metrics(
            db, ddf, row_index, spec["metrics"], pairs, mode=mode, labels_override=spec.get("labels")
        )
        # Fallback: ha pair-t kértünk, de nincs egyetlen összepárosítható metrika sem,
        # essünk vissza single módra, hogy legalább a partner értékek kirajzolódjanak.
        if not labels and mode == "pair":
            labels, s_main, s_comp = _build_series_for_metrics(
                db, ddf, row_index, spec["metrics"], None, mode="single", labels_override=spec.get("labels")
            )
        if not labels:
            continue
        p = save_column(
            values=s_main,
            labels=labels,  # partner oszlop
            overlay_values=(s_comp if mode == "pair" else None),  # csoport overlay vonal
            title=spec.get("title"),
            annotate=spec.get("annotate", True),
            size_cm=size_cm,
            filename=_fmt_filename(spec.get("filename", "column.png"), partner_id),
            value_label_color=spec.get("value_label_color"),
            show_x_labels=spec.get("show_x_labels", True),
            x_label_rotation=spec.get("x_label_rotation", 0),
            x_label_fontsize=spec.get("x_label_fontsize", 9.0),
            x_label_wrap=spec.get("x_label_wrap", 10),
            bar_spacing=spec.get("bar_spacing", 0.25),
            bar_width=spec.get("bar_width", 0.55),
            x_margin=spec.get("x_margin", 0.06),
            legend_below=spec.get("legend_below", True),
            legend_pad=spec.get("legend_pad", 0.12),
            legend_ncol=spec.get("legend_ncol", 2),
            main_label=spec.get("main_label", "Az Ön értékei"),
            overlay_label=spec.get("overlay_label", "Hasonló árbevételű cégek átlagos értékei"),
            palette=pal,
        )
        results["column"].append(p)

    # BAR: partner oszlop + csoport overlay vonal
    for spec in assignment.get("bar", []):
        mode = "pair" if spec.get("source_type") == "pair" else "single"
        pairs = find_pairs(db, suffix=spec.get("compare_suffix", "_átlag")) if mode == "pair" else None
        # Per-chart style overrides (palette + size + overlay color)
        pal = {**DEFAULT_PALETTE, **(spec.get("palette") or {})}
        if spec.get("main_color"):
            pal["secondary"] = spec["main_color"]
        size_cm = tuple(spec["size_cm"]) if spec.get("size_cm") else None
        labels, s_main, s_comp = _build_series_for_metrics(
            db, ddf, row_index, spec["metrics"], pairs, mode=mode, labels_override=spec.get("labels")
        )
        # Fallback: ha pair-t kértünk, de nincs egyetlen összepárosítható metrika sem,
        # essünk vissza single módra, hogy legalább a partner értékek kirajzolódjanak.
        if not labels and mode == "pair":
            labels, s_main, s_comp = _build_series_for_metrics(
                db, ddf, row_index, spec["metrics"], None, mode="single", labels_override=spec.get("labels")
            )
        if not labels:
            continue
        p = save_bar(
            values=s_main,
            labels=labels,  # partner oszlop
            overlay_values=(s_comp if mode == "pair" else None),  # csoport overlay
            title=spec.get("title"),
            annotate=spec.get("annotate", True),
            size_cm=size_cm,
            filename=_fmt_filename(spec.get("filename", "bar.png"), partner_id),
            value_label_color=spec.get("value_label_color"),
            legend_below=spec.get("legend_below", True),
            legend_pad=spec.get("legend_pad", 0.12),
            legend_ncol=spec.get("legend_ncol", 2),
            main_label=spec.get("main_label", "Az Ön értékei"),
            overlay_label=spec.get("overlay_label", "Hasonló árbevételű cégek átlagos értékei"),
            palette=pal,
        )
        results["bar"].append(p)

    # TABLE
    for spec in assignment.get("table", []):
        # tábláknál alapértelmezetten pair-t várunk; de ha single-t kér, csak a partner értékek jelennek meg és a csoport üresen marad
        mode = "pair" if spec.get("source_type") == "pair" else "single"
        pairs = find_pairs(db, suffix=spec.get("compare_suffix", "_átlag")) if mode == "pair" else None
        labels, s_main, s_comp = _build_series_for_metrics(
            db, ddf, row_index, spec["metrics"], pairs, mode=mode, labels_override=spec.get("labels")
        )
        # Fallback: ha pair-t kértünk, de nincs egyetlen összepárosítható metrika sem,
        # essünk vissza single módra, hogy legalább a partner értékek kirajzolódjanak.
        if not labels and mode == "pair":
            labels, s_main, s_comp = _build_series_for_metrics(
                db, ddf, row_index, spec["metrics"], None, mode="single", labels_override=spec.get("labels")
            )
        if not labels:
            continue
        if s_comp is None:
            s_comp = [None] * len(s_main)
        p = Path(save_partner_group_table(
            labels=labels,
            partner_values=s_main,
            group_values=s_comp,
            filename=_fmt_filename(spec.get("filename", "table.png"), partner_id),
            title=spec.get("title"),
            col_widths=spec.get("col_widths", (0.52, 0.24, 0.24)),
            zebra_colors=spec.get("zebra_colors"),
            font_size=spec.get("font_size", 9.0),
        ))
        results["table"].append(p)

    return results

def render_pages_from_yaml(
    *, db: pd.DataFrame, ddf: pd.DataFrame, row_index: int, config: dict, partner_id: str | None = None,
) -> dict[str, dict[str, list[Path]]]:
    """
    YAML séma: { pages: [ { id,title, charts:[{type, metrics, filename, ...}], ... } ] }
    """
    def _norm_type_name(t: str | None) -> str:
        t = (t or "").strip().lower()
        aliases = {
            "col": "column",
            "columns": "column",
            "column_chart": "column",
            "barh": "bar",
            "bars": "bar",
            "bar_chart": "bar",
            "radar_chart": "radar",
            "spider": "radar",
            "spiderweb": "radar",
            "tbl": "table",
            "table_chart": "table",
        }
        return aliases.get(t, t)

    apply_minimal_theme()  # Rubik + brand színek + rcParams
    pages = config.get("pages")
    if not pages and "charts" in config:
        # Allow root-level 'charts' as a single page
        pages = [{"id": config.get("id", "page_1"), "charts": config.get("charts", [])}]
    if pages is None:
        pages = []
    out: dict[str, dict[str, list[Path]]] = {}
    for i, page in enumerate(pages):
        page_id = page.get("id") or page.get("title") or f"page_{i+1}"
        adict: dict[str, list[dict]] = {"radar": [], "column": [], "bar": [], "table": []}
        for ch in page.get("charts", []) or []:
            t = _norm_type_name(ch.get("type"))
            if t in adict:
                adict[t].append(ch)
        out[page_id] = render_assignment(
            db=db, ddf=ddf, row_index=row_index, assignment=adict, partner_id=partner_id
        )
    return out