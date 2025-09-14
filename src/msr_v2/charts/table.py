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

    cell_text = [[_fmt(x) for x in row] for row in rows]
    col_labels = [str(c) for c in columns]

    pal = s.palette
    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        colLoc="left",
        cellLoc="left",
        loc="upper left",
        bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(s.labels.y_fontsize)

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