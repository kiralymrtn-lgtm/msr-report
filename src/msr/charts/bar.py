from __future__ import annotations
from pathlib import Path
from typing import Sequence
import numpy as np
import matplotlib.pyplot as plt

from ..utils.paths import local_path, ensure_dir
from .theme import DEFAULT_PALETTE, ensure_rubik_font

CM_TO_IN = 0.3937007874

# Legyen Rubik a default a bar/column chartoknál is
ensure_rubik_font()

# Brand-aligned default palette (tükör a brand.css-hez)
DEFAULT_PALETTE = {
    "secondary": "#ffd500",  # --brand-secondary (matches brand.css)
    "muted":     "#f0aa00",  # --muted
    "text":      "#243746",  # --text
}

# ─────────────────────────────────────────────────────────
# Global default size (cm) for bar/column charts
# ─────────────────────────────────────────────────────────
DEFAULT_BAR_SIZE_CM: tuple[float, float] = (8.0, 8.0)

def set_default_bar_size(size_cm: tuple[float, float]) -> None:
    """Override the default size used by bar/column charts when size_cm is not provided."""
    global DEFAULT_BAR_SIZE_CM
    DEFAULT_BAR_SIZE_CM = size_cm

def _fig(size_cm: tuple[float, float]):
    w_in, h_in = size_cm[0] * CM_TO_IN, size_cm[1] * CM_TO_IN
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=300)
    return fig, ax

def _hide_all_axes(ax: plt.Axes) -> None:
    """No grid, no spines, no ticks, no tick-labels – completely frameless."""
    ax.grid(False)
    # Hide every spine
    for spine in ax.spines.values():
        spine.set_visible(False)
    # Remove all ticks and tick labels on both axes
    ax.tick_params(axis="both", which="both",
                   bottom=False, top=False, left=False, right=False,
                   labelbottom=False, labelleft=False)
    ax.set_axisbelow(False)

def save_column(
    values: Sequence[float],
    labels: Sequence[str],
    *,
    title: str | None = None,
    y_range: tuple[float, float] | None = None,
    annotate: bool = False,
    size_cm: tuple[float, float] | None = None,
    filename: str = "column.png",
    palette: dict[str, str] | None = None,
    compare_values: Sequence[float] | None = None,
    highlight_index: int | None = None,
) -> Path:
    """
    Függőleges oszlopdiagram (bar/column).

    - Alapszín: secondary
    - Összehasonlító sorozat (ha van): muted (side-by-side elrendezés)
    - Kiemelés: highlight_index → text szín
    - Nincs grid; csak Y spine látszik
    """
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    sec = pal["secondary"]
    mut = pal["muted"]
    txt = pal["text"]
    if size_cm is None:
        size_cm = DEFAULT_BAR_SIZE_CM
    fig, ax = _fig(size_cm)
    x = np.arange(len(labels))

    if compare_values is None:
        # Egy sorozat
        width = 0.7
        colors = [sec] * len(values)
        if highlight_index is not None and 0 <= highlight_index < len(colors):
            colors[highlight_index] = txt

        bars = ax.bar(x, values, width=width, color=colors)

        if annotate:
            for rect, val in zip(bars, values):
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height(),
                        f"{val:.1f}",
                        ha="center", va="bottom", fontsize=8)
    else:
        # Két sorozat (összehasonlítás): side-by-side
        width = 0.36
        vals = np.array(values, dtype=float)
        comp = np.array(compare_values, dtype=float)

        bars_main = ax.bar(x - width/2.0, vals, width=width, color=sec, label="Saját")
        bars_comp = ax.bar(x + width/2.0, comp, width=width, color=mut, label="Csoport")

        if highlight_index is not None and 0 <= highlight_index < len(vals):
            bars_main[highlight_index].set_color(txt)

        if annotate:
            for rect, val in zip(bars_main, vals):
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height(),
                        f"{val:.1f}",
                        ha="center", va="bottom", fontsize=8)
            for rect, val in zip(bars_comp, comp):
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height(),
                        f"{val:.1f}",
                        ha="center", va="bottom", fontsize=8)

        ax.legend(frameon=False, loc="upper right")

    # No axes/ticks for column charts (frameless look)
    ax.set_xticks([])
    ax.set_yticks([])

    if y_range:
        ax.set_ylim(y_range)

    if title:
        ax.set_title(title, pad=6)

    _hide_all_axes(ax)

    out_dir = local_path("output", "assets", "charts")
    ensure_dir(out_dir)
    out_path = out_dir / filename

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


# Horizontal bar chart helper (frameless, brand-aligned)
def save_bar(
    values: Sequence[float],
    labels: Sequence[str],
    *,
    title: str | None = None,
    x_range: tuple[float, float] | None = None,
    annotate: bool = False,
    size_cm: tuple[float, float] | None = None,
    filename: str = "bar.png",
    palette: dict[str, str] | None = None,
    compare_values: Sequence[float] | None = None,
    highlight_index: int | None = None,
) -> Path:
    """
    Vízszintes 'bar' diagram (barh):
      - Alapszín: secondary
      - Összehasonlítás (ha van): muted (side-by-side elrendezés y-eltolással)
      - Kiemelés: highlight_index → text szín
      - Tengelyek/tickek/spine-ok NINCSENEK
    """
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    sec = pal["secondary"]
    mut = pal["muted"]
    txt = pal["text"]
    if size_cm is None:
        size_cm = DEFAULT_BAR_SIZE_CM
    fig, ax = _fig(size_cm)
    y = np.arange(len(labels))

    if compare_values is None:
        height = 0.7
        colors = [sec] * len(values)
        if highlight_index is not None and 0 <= highlight_index < len(colors):
            colors[highlight_index] = txt

        bars = ax.barh(y, values, height=height, color=colors)

        if annotate:
            for rect, val in zip(bars, values):
                ymid = rect.get_y() + rect.get_height() / 2.0
                ax.text(val, ymid, f"{val:.1f}", va="center", ha="left", fontsize=8)
    else:
        height = 0.36
        vals = np.array(values, dtype=float)
        comp = np.array(compare_values, dtype=float)

        bars_main = ax.barh(y - height/2.0, vals, height=height, color=sec, label="Saját")
        bars_comp = ax.barh(y + height/2.0, comp, height=height, color=mut, label="Csoport")

        if highlight_index is not None and 0 <= highlight_index < len(vals):
            bars_main[highlight_index].set_color(txt)

        if annotate:
            for rect, val in zip(bars_main, vals):
                ymid = rect.get_y() + rect.get_height() / 2.0
                ax.text(val, ymid, f"{val:.1f}", va="center", ha="left", fontsize=8)
            for rect, val in zip(bars_comp, comp):
                ymid = rect.get_y() + rect.get_height() / 2.0
                ax.text(val, ymid, f"{val:.1f}", va="center", ha="left", fontsize=8)

        ax.legend(frameon=False, loc="lower right")

    if x_range:
        ax.set_xlim(x_range)

    # Teljesen frameless
    _hide_all_axes(ax)

    out_dir = local_path("output", "assets", "charts")
    ensure_dir(out_dir)
    out_path = out_dir / filename

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path

# Visszafelé kompatibilitás (régi demókhoz)
def save_simple_bar(
    *,
    values: Sequence[float],
    labels: Sequence[str],
    highlight_index: int | None = None,
    usable_width_cm: float = 30.0,
    height_cm: float = 10.0,
    filename: str = "bar_demo.png",
) -> Path:
    return save_column(
        values=values,
        labels=labels,
        annotate=False,
        size_cm=(usable_width_cm, height_cm),
        filename=filename,
        highlight_index=highlight_index,
    )