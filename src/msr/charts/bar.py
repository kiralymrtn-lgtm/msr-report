from __future__ import annotations
from pathlib import Path
from typing import Sequence
import numpy as np
import matplotlib.pyplot as plt

from ..utils.paths import local_path, ensure_dir
from .theme import DEFAULT_PALETTE, ensure_rubik_font, cm_to_in, DEFAULT_DPI


# Legyen Rubik a default a bar/column chartoknál is
ensure_rubik_font()

# ─────────────────────────────────────────────────────────
# Global default size (cm) for bar/column charts
# ─────────────────────────────────────────────────────────
DEFAULT_BAR_SIZE_CM: tuple[float, float] = (10.0, 10.0)

def set_default_bar_size(size_cm: tuple[float, float]) -> None:
    """Override the default size used by bar/column charts when size_cm is not provided."""
    global DEFAULT_BAR_SIZE_CM
    DEFAULT_BAR_SIZE_CM = size_cm

def _fig(size_cm: tuple[float, float]):
    fig, ax = plt.subplots(
        figsize=(cm_to_in(size_cm[0]), cm_to_in(size_cm[1])),
        dpi=DEFAULT_DPI,
    )
    return fig, ax

def _hide_all_axes(ax: plt.Axes) -> None:
    """No grid, no spines, no ticks, no tick-labels – completely frameless."""
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
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
    show_x_labels: bool = False,
    x_label_rotation: float = 0.0,
    x_label_fontsize: float = 9.0,
    # Overlay horizontal lines (e.g., partner values)
    overlay_values: Sequence[float] | None = None,
    overlay_line_color: str | None = None,
    overlay_line_width: float = 2.0,
    overlay_line_pad_frac: float = 0.15,
) -> Path:
    """
    Függőleges oszlopdiagram (column).
      - Alapszín: secondary
      - Összehasonlító sorozat: muted (side-by-side)
      - Kiemelés: highlight_index → text szín
      - Nincs grid; tengelyek és tickek rejtve
    """
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    sec = pal["secondary"]; mut = pal["muted"]; txt = pal["text"]

    if size_cm is None:
        size_cm = DEFAULT_BAR_SIZE_CM
    fig, ax = _fig(size_cm)
    x = np.arange(len(labels))

    if compare_values is None:
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

    # Optional overlay horizontal lines (e.g., partner values)
    if overlay_values is not None:
        line_color = overlay_line_color or txt
        # pick the bar collection to overlay: main bars for compare, otherwise the only bars
        target_bars = (bars_main if compare_values is not None else bars)
        for rect, y in zip(target_bars, overlay_values):
            bw = rect.get_width()
            # extend slightly beyond the bar width on both sides
            x0 = rect.get_x() - bw * overlay_line_pad_frac
            x1 = rect.get_x() + bw * (1.0 + overlay_line_pad_frac)
            ax.hlines(y, x0, x1, color=line_color, linewidth=overlay_line_width, zorder=5)


    # Frames

    # X-labels kapcsolhatóan
    if show_x_labels:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=x_label_rotation, fontsize=x_label_fontsize)
    else:
        ax.set_xticks([])

    ax.set_yticks([])

    if y_range:
        ax.set_ylim(y_range)
    if title:
        ax.set_title(title, pad=6)

    if show_x_labels:
        # spinek off, X-felirat marad
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis="y", which="both", left=False, right=False, labelleft=False)
        ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=True)
    else:
        _hide_all_axes(ax)

    out_dir = local_path("output", "assets", "charts")
    ensure_dir(out_dir)
    out_path = out_dir / filename

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path

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
    Vízszintes 'bar' diagram (barh).
      - Alapszín: secondary
      - Összehasonlítás: muted
      - Kiemelés: highlight_index → text szín
      - Tengelyek/tickek/spine-ok: nincsenek
    """
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    sec = pal["secondary"]; mut = pal["muted"]; txt = pal["text"]

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