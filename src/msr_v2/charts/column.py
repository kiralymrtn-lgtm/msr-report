import textwrap
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Sequence, Optional
from .base import fig_ax, place_legend, wrap_title, ensure_out_dirs, OUT_CHARTS
from ..config import Style
from ..theme import apply_theme

LEGEND_BELOW = 0.10  # a legenda mennyivel legyen az axes alatt (axes-frakció)

def save_column(
    values: Sequence[float],
    labels: Sequence[str],
    *,
    filename: str,
    title: str | None = None,
    style: Style,
    overrides: dict | None = None,
    overlay_values: Optional[Sequence[float]] = None,
    show_x_labels: bool = True,
    x_label_wrap: int | None = None,
):
    s = style.merge_overrides(overrides)
    apply_theme(s)
    ensure_out_dirs()

    # formázás mindig a Style-ból (YAML overrides felülírhatják)
    fmt_value = s.labels.value_fmt
    overlay_fmt = s.labels.overlay_value_fmt

    # Determine effective wrapping width for category labels (overrides.labels.wrap → Style.labels.wrap)
    _wrap = None
    if overrides and isinstance(overrides.get("labels"), dict):
        _wrap = overrides["labels"].get("wrap")
    if _wrap is None:
        _wrap = s.labels.wrap

    fig, ax = fig_ax(s)
    x = np.arange(len(labels))
    # Column thickness (bar width) – overridable from YAML via `overrides.bar_width`
    bar_width = float((overrides or {}).get("bar_width", 0.8))
    bars = ax.bar(x, values, width=bar_width, color=s.palette.secondary, label="Az Ön értékei")

    if overlay_values is not None:
        txt = s.palette.text
        for rect, y in zip(bars, overlay_values):
            w = rect.get_width()
            x0 = rect.get_x() - w * 0.05
            x1 = rect.get_x() + w * (1.05)
            ax.hlines(y, x0, x1, color=txt, linewidth=2.0, zorder=5)
            ax.annotate(
                overlay_fmt.format(val=float(y)),  # ← itt is egységes
                xy=(x0, y), xytext=(-4, 0),
                textcoords="offset points",
                ha="right", va="center",
                fontsize=s.labels.y_fontsize,
                color=s.labels.value_color or txt, zorder=6,
            )
        ax.plot([], [], color=txt, linewidth=2.0, label="Hasonló árbevételű cégek átlagos értékei")

    # értékek a rúd közepén – használd a fmt_value-t
    for rect, v in zip(bars, values):
        ax.text(
            rect.get_x() + rect.get_width() / 2.,
            rect.get_height() / 2.,
            fmt_value.format(val=float(v)),  # ← EZ volt eddig s.labels.value_fmt
            ha="center", va="center",
            fontsize=s.labels.y_fontsize,
            color=s.labels.value_color or s.palette.text
        )

    # tengelyek minimal
    if show_x_labels:
        wrap = x_label_wrap if x_label_wrap is not None else _wrap
        if wrap and int(wrap) > 0:
            tick_labels = [textwrap.fill(str(t), width=int(wrap), break_long_words=False, break_on_hyphens=True) for t in labels]
        else:
            tick_labels = [str(t) for t in labels]
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, fontsize=s.labels.x_fontsize)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis="x", pad=12)
        ax.tick_params(axis="y", which="both", left=False, labelleft=False)
    else:
        ax.set_xticks([]); ax.set_yticks([])

    ax.set_yticks([])

    # Cím: egyszer állítjuk be és a FIGURÁHOZ igazítva középre toljuk
    if title:
        t = ax.set_title(
            wrap_title(title, s),
            fontsize=s.title.size,
            fontweight=s.title.weight,
            pad=s.title.pad,
        )

        # csak középre igazítás a FIGURA szélességéhez viszonyítva
        bbox = ax.get_position()
        x_fig_center_in_axes = (0.5 - bbox.x0) / bbox.width
        t.set_position((x_fig_center_in_axes, t.get_position()[1]))

        if s.legend.show:
            place_legend(ax, fig, s)

    else:
        if s.legend.show:
            place_legend(ax, fig, s)

    out = OUT_CHARTS / filename
    fig.savefig(out); plt.close(fig)
    return out