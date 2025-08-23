from __future__ import annotations
from typing import Sequence, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

from ..utils.paths import local_path, ensure_dir
from .theme import DEFAULT_PALETTE, ensure_rubik_font, cm_to_in, DEFAULT_DPI

# Rubik betűcsalád aktiválása (ha már betöltötted máshol is, ez harmless)
ensure_rubik_font()

def _fmt_cell(x: Any) -> str:
    # Egységes, szép formázás számokra
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.1f}"
    return str(x)

def save_table(
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    *,
    title: str | None = None,
    filename: str = "table.png",
    size_cm: tuple[float, float] | None = None,
    palette: dict[str, str] | None = None,
    header_bg: str | None = None,   # alap: pal["text"]
    header_fg: str | None = None,   # alap: pal["secondary"]
    body_fg: str | None = None,     # alap: pal["text"]
    zebra_colors: tuple[str, str] | None = None,  # alap: ("#FFFFFF", pal["background"])
    col_widths: Sequence[float] | None = None,    # az axes szélességének arányai, pl. [0.5, 0.25, 0.25]
    col_align: Sequence[str] | None = None,
    font_size: float = 9.0,
    grid: bool = False,
    grid_width: float = 0.6,
    align: str = "left",            # "left" | "center" | "right"
) -> str:
    """
    Brand-aligned táblázat mentése PNG-be (Rubik + brand színek).
    - Fejléc: text háttér, secondary felirat (alapértelmezés)
    - Törzs: text színű felirat, váltakozó háttér (zebra)
    """
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    header_bg = header_bg or pal["text"]
    header_fg = header_fg or pal["secondary"]
    body_fg   = body_fg or pal["text"]
    zebra_colors = zebra_colors or ("#FFFFFF", pal["background"])
    grid_color = pal["text"]

    ncols = len(columns)
    nrows = len(rows)

    # Dinamikus alapméret: kb. 3.0 cm / oszlop, ~0.8 cm / sor + fejlécre puffer
    if size_cm is None:
        width_cm  = max(10.0, 3.0 * ncols)
        height_cm = max(4.0, 1.6 + 0.8 * (nrows + 1))
        size_cm = (width_cm, height_cm)

    fig, ax = plt.subplots(
        figsize=(cm_to_in(size_cm[0]), cm_to_in(size_cm[1])),
        dpi=DEFAULT_DPI,
    )
    ax.set_axis_off()

    cell_text = [[_fmt_cell(x) for x in row] for row in rows]
    col_labels = [str(c) for c in columns]

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        colLoc=align,
        cellLoc=align,
        colWidths=col_widths,   # None → auto
        loc="upper left",
        bbox=[0, 0, 1, 1],      # kitölti az axes-t
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)

    # Oszloponkénti igazítás feloldása
    if col_align is None:
        _col_align = [align] * ncols
    else:
        _col_align = list(col_align)
        if len(_col_align) < ncols:
            _col_align += [align] * (ncols - len(_col_align))

    _align_map = {"left": "left", "center": "center", "right": "right"}

    # Fejléc styling (row=0)
    for j in range(ncols):
        cell = table[0, j]
        cell.set_facecolor(header_bg)
        cell.get_text().set_color(header_fg)
        cell.get_text().set_weight("bold")
        cell.get_text().set_ha(_align_map.get(_col_align[j], "left"))
        cell.get_text().set_va("center")
        cell.set_edgecolor(grid_color if grid else header_bg)
        cell.set_linewidth(grid_width if grid else 0)

    # Törzs styling (row=1..nrows)
    for i in range(1, nrows + 1):
        bg = zebra_colors[(i - 1) % 2]
        for j in range(ncols):
            cell = table[i, j]
            cell.set_facecolor(bg)
            cell.get_text().set_color(body_fg)
            cell.get_text().set_ha(_align_map.get(_col_align[j], _align_map.get(align, "left")))
            cell.get_text().set_va("center")
            cell.set_edgecolor(grid_color if grid else bg)
            cell.set_linewidth(grid_width if grid else 0)

    if title:
        ax.set_title(title, pad=8)

    out_dir = local_path("output", "assets", "tables")
    ensure_dir(out_dir)
    out_path = out_dir / filename

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)


# Kényelmi wrapper: partner vs. csoport táblázat a meglévő chart-adatokból
def save_partner_group_table(
    labels: Sequence[str],
    partner_values: Sequence[float],
    group_values: Sequence[float],
    *,
    filename: str = "partner_table.png",
    title: str | None = None,
    col_widths: Sequence[float] | None = (0.52, 0.24, 0.24),
    col_align: Sequence[str] | None = ("left", "center", "center"),
    zebra_colors: tuple[str, str] | None = None,
    font_size: float = 9.0,
) -> str:
    columns = ["Kérdés", "Partner", "Csoport"]
    rows = [[lab, p, g] for lab, p, g in zip(labels, partner_values, group_values)]
    return save_table(
        columns=columns,
        rows=rows,
        title=title,
        filename=filename,
        col_widths=col_widths,
        col_align=col_align,
        zebra_colors=zebra_colors,
        font_size=font_size,
        align="left",
    )