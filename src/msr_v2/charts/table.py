from typing import Sequence, Any
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from .base import fig_ax, wrap_title, ensure_out_dirs, OUT_TABLES
from ..config import Style
from ..theme import apply_theme

def _fmt(x: Any) -> str:
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.1f}"
    return str(x)

def save_table(
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    *,
    filename: str,
    title: str | None = None,
    style: Style,
    overrides: dict | None = None,
):
    s = style.merge_overrides(overrides); apply_theme(s); ensure_out_dirs()
    fig, ax = fig_ax(s)
    ax.set_axis_off()

    tbl = (overrides or {}).get("table", {}) if isinstance(overrides, dict) else {}
    cols_cfg = tbl.get("columns")  # lehet None
    align_cfg = tbl.get("align", None)  # pl. ["left","center","center"]

    # --- oszlopszélességek cm-ben → figura szélesség + colWidths ---
    col_widths = None  # ezt adjuk majd a ax.table(..., colWidths=...) paraméternek

    # 1) globális lista: col_widths_cm
    widths_cm = tbl.get("col_widths_cm")

    # 2) vagy per-column: columns[].width_cm
    if not widths_cm and cols_cfg:
        per = [c.get("width_cm") for c in cols_cfg]
        if any(w is not None for w in per):
            widths_cm = per

    if widths_cm:
        # szűrés + float
        widths_cm = [float(w) for w in widths_cm if w is not None]
        if widths_cm:
            total_cm = sum(widths_cm)
            # a matplotlib colWidths arányt vár → normalizáljuk
            col_widths = [w / total_cm for w in widths_cm]

            # a figura szélességét is állítsuk a megadott összegre
            cur_w_in, cur_h_in = fig.get_size_inches()
            target_w_in = total_cm / 2.54

            # magasság: YAML-ből (table.height_cm vagy overrides.size.cm_h), különben hagyjuk
            height_cm = tbl.get("height_cm")
            if not height_cm:
                height_cm = (overrides or {}).get("size", {}).get("cm_h") if isinstance(overrides, dict) else None
            target_h_in = (height_cm / 2.54) if height_cm else cur_h_in

            fig.set_size_inches(target_w_in, target_h_in, forward=True)

    # oszloponkénti formátum a YAML-ból (ha van), különben None
    fmt_per_col = None
    if cols_cfg and isinstance(cols_cfg, list):
        fmt_per_col = []
        for c in cols_cfg:
            fmt_per_col.append(c.get("fmt"))  # pl. "{val:.1f}" vagy "{val:.1f}%"

    cell_text = []
    for r in rows:
        # r lehet [label, v] vagy [label, v, c]
        out_row = []
        for j, val in enumerate(r):
            if j == 0:
                out_row.append(str(val))  # label oszlop: sima string (wrap-et már assign megcsinálhatja)
            else:
                if fmt_per_col and j < len(fmt_per_col) and fmt_per_col[j]:
                    try:
                        out_row.append(fmt_per_col[j].format(val=float(val)) if val is not None else "")
                    except Exception:
                        out_row.append("" if val is None else str(val))
                else:
                    # fallback: egyszerű str
                    out_row.append("" if val is None else str(val))
        cell_text.append(out_row)

    col_labels = [str(c) for c in columns]

    pal = s.palette
    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        colLoc="left",
        cellLoc="left",
        loc="upper left",
        bbox=[0, 0, 1, 1],
        colWidths=col_widths,  # normalizált arányok listája, vagy None
    )
    table.auto_set_font_size(False)
    table.set_fontsize(s.labels.y_fontsize)

    # --- Igazítás oszloponként (YAML: overrides.table.align) ---
    ncols = len(col_labels)
    nrows = len(rows)
    for j in range(ncols):
        # kívánt igazítás a YAML-ből, különben: label=left, többi=right
        desired = None
        if align_cfg and j < len(align_cfg):
            desired = str(align_cfg[j]).lower()
        if desired not in ("left", "center", "right"):
            desired = "left" if j == 0 else "right"

        # >>> FEJLÉC IGAZÍTÁS – JAVÍTÁS <<<
        hdr_ha = None
        if align_cfg and j < len(align_cfg):
            hdr_ha = str(align_cfg[j]).lower()
        if hdr_ha not in ("left", "center", "right"):
            hdr_ha = "left" if j == 0 else "center"
        table[0, j].get_text().set_ha(hdr_ha)

        # adatsorok igazítása
        for i in range(1, nrows + 1):
            table[i, j].get_text().set_ha(desired)

    # fejléc
    ncols = len(columns)
    for j in range(ncols):
        cell = table[0, j]
        cell.set_facecolor(pal.text)
        cell.get_text().set_color(pal.secondary)
        cell.get_text().set_weight("bold")

    # törzs
    nrows = len(rows)
    for i in range(1, nrows + 1):
        for j in range(ncols):
            cell = table[i, j]
            cell.set_facecolor("#FFFFFF" if (i % 2 == 1) else pal.background)
            cell.get_text().set_color(pal.text)

    if title:
        ax.set_title(wrap_title(title, s), pad=s.title.pad)

    fig.tight_layout()
    out = OUT_TABLES / filename
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out