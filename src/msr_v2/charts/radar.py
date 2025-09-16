import numpy as np, math
import textwrap as tw
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from typing import Sequence, Optional, Tuple
from .base import fig_ax, place_legend, wrap_title, ensure_out_dirs, OUT_CHARTS
from ..config import Style
from ..theme import apply_theme

def save_radar(
    labels: Sequence[str],
    series_main: Sequence[float],
    *,
    filename: str,
    title: str | None = None,
    style: Style,
    overrides: dict | None = None,
    series_comp: Optional[Sequence[float]] = None,
    r_range: Optional[Tuple[float, float]] = None,
):
    s = style.merge_overrides(overrides); apply_theme(s); ensure_out_dirs()

    n = len(labels)
    ang = np.linspace(0, 2*math.pi, n, endpoint=False)
    ang = np.r_[ang, ang[0]]
    s1 = list(series_main) + [series_main[0]]
    s2 = list(series_comp) + [series_comp[0]] if series_comp is not None else None

    fig, ax = plt.subplots(
        subplot_kw=dict(polar=True),
        figsize=(s.size.cm_w/2.54, s.size.cm_h/2.54),
        dpi=s.size.dpi,
    )
    ax.plot(ang, s1, lw=2.0, color=s.palette.secondary, label="Az Ön értékei")
    ax.fill(ang, s1, alpha=0.10, color=s.palette.secondary)
    if s2 is not None:
        ax.plot(ang, s2, lw=1.8, color=s.palette.text, label="Hasonló árbevételű cégek átlagos értékei")
        ax.fill(ang, s2, alpha=0.08, color=s.palette.text)

    ax.set_xticks(ang[:-1])
    wrap = None
    if overrides and isinstance(overrides.get("labels"), dict):
        wrap = overrides["labels"].get("wrap")
    if wrap is None:
        wrap = s.labels.wrap

    def _wrap_label(v):
        if not wrap:
            return str(v)
        return tw.fill(str(v), width=int(wrap), break_long_words=False, break_on_hyphens=True)

    ax.set_xticklabels([_wrap_label(x) for x in labels], fontsize=s.labels.x_fontsize)

    # --- R fixálása 0..5-re és egész osztásra ---
    ax.set_rmin(0)
    ax.set_rmax(5)

    # pontosan egész lépésköz (0,1,2,3,4,5) -> mindig ugyanannyi kör
    ax.yaxis.set_major_locator(mticker.FixedLocator([1,2,3,4,5]))

    # minor teljes tiltása, hogy ne duplázódjon semmi
    ax.minorticks_off()
    ax.yaxis.set_minor_locator(mticker.NullLocator())
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())

    # feliratok: mindig egész számként
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:.0f}'))

    # finom grid styling (halvány körök + sugarak)
    grid_color = s.palette.text
    for gl in ax.yaxis.get_gridlines():
        gl.set_linestyle("-"); gl.set_linewidth(0.2); gl.set_alpha(0.22); gl.set_color(grid_color)
    for gl in ax.xaxis.get_gridlines():
        gl.set_linestyle("-"); gl.set_linewidth(0.3); gl.set_alpha(0.18); gl.set_color(grid_color)
    ax.spines["polar"].set_color("#EEEEEE"); ax.spines["polar"].set_linewidth(0.4); ax.spines["polar"].set_alpha(0.25)

    if r_range: ax.set_rmin(r_range[0]); ax.set_rmax(r_range[1])
    if title: ax.set_title(wrap_title(title, s), pad=s.title.pad)

    if s.legend.show:
        place_legend(ax, fig, s)
    fig.tight_layout()

    # cím kiírása normálisan
    t = ax.set_title(
        wrap_title(title, style),
        fontsize=style.title.size,
        fontweight=style.title.weight,
        pad=style.title.pad,
    )

    # … legend elhelyezés, stb. …

    # fontos: előbb layout!
    fig.tight_layout()

    # majd igazítsd a címet a FIGURÁHOZ középre
    bbox = ax.get_position()  # axes helyzete a figurán belül
    x_fig_center_in_axes = (0.5 - bbox.x0) / bbox.width
    ax.title.set_position((x_fig_center_in_axes, ax.title.get_position()[1]))

    out = OUT_CHARTS / filename
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out