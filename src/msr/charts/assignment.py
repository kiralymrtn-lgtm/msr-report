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
    avg_pairs: dict[str, str],
) -> tuple[list[str], list[float], list[float]]:
    L = label_map_from_dict(ddf)   # bázisnév -> emberi label
    labels, s_main, s_comp = [], [], []
    for base in metrics:
        if base in db.columns and base in avg_pairs:
            labels.append(L.get(base, base))
            s_main.append(db.loc[row_index, base])           # partner
            s_comp.append(db.loc[row_index, avg_pairs[base]])# csoport-átlag ugyanazon sorból
    return labels, s_main, s_comp

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
        labels, s_main, s_comp = _build_series_for_metrics(db, ddf, row_index, spec["metrics"], avg_pairs)
        if not labels: continue
        p = save_radar(
            labels=labels, series_main=s_main, series_comp=s_comp,
            title=spec.get("title"),
            filename=_fmt_filename(spec.get("filename", "radar.png"), partner_id),
            r_range=spec.get("r_range"),
            legend_below=spec.get("legend_below", True),
            legend_pad=spec.get("legend_pad", 0.12),
            legend_ncol=spec.get("legend_ncol", 2),
            palette=DEFAULT_PALETTE,
        )
        results["radar"].append(p)

    # COLUMN: partner oszlop + csoport overlay vonal
    for spec in assignment.get("column", []):
        labels, s_main, s_comp = _build_series_for_metrics(db, ddf, row_index, spec["metrics"], avg_pairs)
        if not labels: continue
        p = save_column(
            values=s_main, labels=labels, # partner oszlop
            overlay_values=s_comp,  # csoport overlay vonal
            title=spec.get("title"),
            annotate=spec.get("annotate", True),
            filename=_fmt_filename(spec.get("filename", "column.png"), partner_id),
            show_x_labels=spec.get("show_x_labels", True),
            x_label_rotation=spec.get("x_label_rotation", 0),
            x_label_fontsize=spec.get("x_label_fontsize", 9.0),
            x_label_wrap=10,  # kb. 10 karakterenként új sor
            bar_spacing=0.25,  # nagyobb hézag a kategóriák között
            bar_width=0.55,  # kicsit keskenyebb oszlop, hogy a label is elférjen
            x_margin=0.06,  # kicsit több margó bal/jobb
            legend_below=spec.get("legend_below", True),
            legend_pad=spec.get("legend_pad", 0.12),
            legend_ncol=spec.get("legend_ncol", 2),
            main_label=spec.get("main_label", "Az Ön értékei"),
            overlay_label=spec.get("overlay_label", "Hasonló árbevételű cégek átlagos értékei"),
            palette=DEFAULT_PALETTE,
        )
        results["column"].append(p)

    # BAR: partner oszlop + csoport overlay vonal
    for spec in assignment.get("bar", []):
        labels, s_main, s_comp = _build_series_for_metrics(db, ddf, row_index, spec["metrics"], avg_pairs)
        if not labels: continue
        p = save_bar(
            values=s_main, labels=labels, # partner oszlop
            overlay_values=s_comp, # csoport overlay
            title=spec.get("title"),
            annotate=spec.get("annotate", True),
            filename=_fmt_filename(spec.get("filename", "bar.png"), partner_id),
            legend_below=spec.get("legend_below", True),
            legend_pad=spec.get("legend_pad", 0.12),
            legend_ncol=spec.get("legend_ncol", 2),
            main_label=spec.get("main_label", "Az Ön értékei"),
            overlay_label=spec.get("overlay_label", "Hasonló árbevételű cégek átlagos értékei"),
            palette=DEFAULT_PALETTE,
        )
        results["bar"].append(p)

    # TABLE
    for spec in assignment.get("table", []):
        labels, s_main, s_comp = _build_series_for_metrics(db, ddf, row_index, spec["metrics"], avg_pairs)
        if not labels: continue
        p = Path(save_partner_group_table(
            labels=labels, partner_values=s_main, group_values=s_comp,
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
    apply_minimal_theme()  # Rubik + brand színek + rcParams
    pages = config.get("pages", [])
    out: dict[str, dict[str, list[Path]]] = {}
    for i, page in enumerate(pages):
        page_id = page.get("id") or page.get("title") or f"page_{i+1}"
        adict: dict[str, list[dict]] = {"radar": [], "column": [], "bar": [], "table": []}
        for ch in page.get("charts", []):
            t = ch.get("type")
            if t in adict:
                adict[t].append(ch)
        out[page_id] = render_assignment(
            db=db, ddf=ddf, row_index=row_index, assignment=adict, partner_id=partner_id
        )
    return out