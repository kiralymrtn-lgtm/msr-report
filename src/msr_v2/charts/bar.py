import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Sequence, Optional
from .base import fig_ax, place_legend, wrap_title, ensure_out_dirs, OUT_CHARTS
from ..config import Style
from ..theme import apply_theme
import textwrap as tw

def save_bar(
    values: Sequence[float],
    labels: Sequence[str],
    *,
    filename: str,
    title: str | None = None,
    style: Style,
    overrides: dict | None = None,
    overlay_values: Optional[Sequence[float]] = None,
    show_y_labels: bool = True,
):
    s = style.merge_overrides(overrides)
    fmt_value = s.labels.value_fmt
    overlay_fmt = s.labels.overlay_value_fmt
    apply_theme(s)
    ensure_out_dirs()

    fig, ax = fig_ax(s)
    y = np.arange(len(labels))
    # Ha csak 1 kategória van, tágítsuk ki a függőleges tartományt,
    # hogy a bar_height változás vizuálisan is erősebben látszódjon.
    if len(labels) == 1:
        # Alapból -0.5..0.5 ~ 1.0 a span. Tegyük -1.0..1.0-ra (span=2.0).
        ax.set_ylim(-1.0, 1.0)
    # Bar thickness (bar height) – overridable from YAML via `overrides.bar_height`
    bar_height = float((overrides or {}).get("bar_height", 0.8))
    bars = ax.barh(y, values, height=bar_height, color=s.palette.secondary, label="Az Ön értékei")

    # overlay FÜGGŐLEGES vonalak (átlag)
    if overlay_values is not None:
        txt = s.palette.text
        for rect, xval in zip(bars, overlay_values):
            h = rect.get_height()
            y0 = rect.get_y() - h*0.05
            y1 = rect.get_y() + h*(1.05)
            ax.vlines(xval, y0, y1, color=txt, linewidth=2.0, zorder=5)
            # label a vonal fölött
            ax.text(
                xval, y1 + h*0.06,
                overlay_fmt.format(val=float(xval)),
                ha="center", va="bottom",
                fontsize=s.labels.y_fontsize,
                color=s.labels.value_color or txt, zorder=6
            )
        ax.plot([], [], color=txt, linewidth=2.0, label="Hasonló árbevételű cégek átlagos értékei")

    # értékek a SÁV KÖZEPÉN (balról jobbra)
    for rect, v in zip(bars, values):
        ymid = rect.get_y() + rect.get_height() / 2.0
        xmid = rect.get_x() + rect.get_width() / 2.0
        ax.text(
            xmid, ymid,
            fmt_value.format(val=float(v)),
            va="center", ha="center", fontsize=s.labels.y_fontsize,
            color=(s.labels.value_color or s.palette.text)
        )

    if show_y_labels:
        ax.set_yticks(y)
        wrap = None
        if overrides and isinstance(overrides.get("labels"), dict):
            wrap = overrides["labels"].get("wrap")
        if wrap is None:
            wrap = s.labels.wrap

        def _wrap_label(v):
            if not wrap:
                return str(v)
            return tw.fill(str(v), width=int(wrap), break_long_words=False, break_on_hyphens=True)

        ax.set_yticklabels([_wrap_label(t) for t in labels], fontsize=s.labels.y_fontsize)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    else:
        ax.set_yticks([]); ax.set_xticks([])

    if title and str(title).strip():
        t = ax.set_title(
            wrap_title(title, s),
            fontsize=s.title.size,
            fontweight=s.title.weight,
            pad=s.title.pad,
        )
        # Fontos: előbb futtassuk le a constrained layoutot, majd igazítsunk középre
        fig.canvas.draw()  # ← ÚJ: ezzel véglegesedik az axes pozíciója
        bbox = ax.get_position()
        x_fig_center_in_axes = (0.5 - bbox.x0) / bbox.width
        t.set_position((x_fig_center_in_axes, t.get_position()[1]))

    if s.legend.show:
        s.chart_type = "bar"
        place_legend(ax, fig, s)

    out = OUT_CHARTS / filename
    fig.savefig(out, bbox_inches="tight", pad_inches=0.2);
    plt.close(fig)  # ← pad_inches hozzáadása
    return out