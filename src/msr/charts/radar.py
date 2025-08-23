from logging import fatal
from typing import Sequence, Optional, Tuple
import math
import numpy as np
import matplotlib.pyplot as plt

from ..utils.paths import local_path, ensure_dir
from .theme import apply_minimal_theme, cm_to_in, DEFAULT_PALETTE

# ─────────────────────────────────────────────────────────
# Global default size (cm) for radar charts
# ─────────────────────────────────────────────────────────
DEFAULT_RADAR_SIZE_CM: tuple[float, float] = (10.0, 10.0)

def set_default_radar_size(size_cm: tuple[float, float]) -> None:
    """Override the default size used by radar charts when size_cm is not provided."""
    global DEFAULT_RADAR_SIZE_CM
    DEFAULT_RADAR_SIZE_CM = size_cm

def save_radar(
    labels: Sequence[str],
    series_main: Sequence[float],
    series_comp: Optional[Sequence[float]] = None,
    title: Optional[str] = None,
    r_range: Optional[Tuple[float, float]] = None,
    size_cm: Optional[Tuple[float, float]] = None,
    filename: Optional[str] = None,
    palette: Optional[dict[str, str]] = None,
    main_label: str = "Saját",
    comp_label: Optional[str] = "Csoport",
    legend_loc: str = "lower center",
    legend_frame: bool = False,
    legend_below: bool = False,
    legend_pad: float = 0.12,
    legend_ncol: int = 2,
):
    """
    Radar chart egy (vagy két) sorozattal, brand-palettával (secondary / muted).
    Diszkrét háttérráccsal, címkékkel és kapcsolható legenddel.
    """
    apply_minimal_theme()

    # Merge brand palette with any caller overrides
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    color_main = pal["secondary"]
    color_comp = pal["muted"]

    # Méret – ha nincs megadva, modul-szintű default
    if size_cm is None:
        size_cm = DEFAULT_RADAR_SIZE_CM

    n = len(labels)
    labels = list(labels)

    # Szögek előállítása és zárás
    angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
    angles = np.concatenate([angles, [angles[0]]])
    s1 = list(series_main) + [series_main[0]]
    s2 = list(series_comp) + [series_comp[0]] if series_comp is not None else None

    fig, ax = plt.subplots(
        subplot_kw=dict(polar=True),
        figsize=(cm_to_in(size_cm[0]), cm_to_in(size_cm[1])),
        dpi=300,
    )

    # Fő sorozat
    ax.plot(angles, s1, linewidth=2.0, color=color_main, label=main_label)
    ax.fill(angles, s1, alpha=0.10, color=color_main)

    # Összehasonlító sorozat (opcionális)
    if s2 is not None:
        ax.plot(angles, s2, linewidth=1.6, linestyle="--", color=color_comp, label=(comp_label or ""))
        ax.fill(angles, s2, alpha=0.08, color=color_comp)

    # Címkék / tengelyek
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.grid(True)            # háttérrács
    grid_color = pal["text"]  # visszafogott rácsszín a brand alapján
    for gl in ax.yaxis.get_gridlines():
        gl.set_linestyle("-")
        gl.set_linewidth(0.4)
        gl.set_alpha(0.22)
        gl.set_color(grid_color)
    for gl in ax.xaxis.get_gridlines():
        gl.set_linestyle("-")
        gl.set_linewidth(0.3)
        gl.set_alpha(0.18)
        gl.set_color(grid_color)
    #ax.set_yticks([])        # nincsenek radiális tickek
    #ax.set_yticklabels([])

    if r_range:
        ax.set_rmin(r_range[0])
        ax.set_rmax(r_range[1])

    if title:
        ax.set_title(title, pad=16)

    if legend_below:
        leg = ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -legend_pad),
            frameon=legend_frame,
            ncol=legend_ncol,
            fontsize=8.5,
        )
        fig.subplots_adjust(bottom=max(0.12, 0.06 + legend_pad))
    else:
        leg = ax.legend(loc=legend_loc, frameon=legend_frame, fontsize=8.5)

    leg.set_zorder(10)

    # Mentés (közös kimeneti mappa)
    out_dir = local_path("output", "assets", "charts")
    ensure_dir(out_dir)
    out_path = out_dir / (filename or "radar.png")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", bbox_extra_artists=[leg])
    plt.close(fig)
    return out_path