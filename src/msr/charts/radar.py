# msr/charts/radar.py
from typing import Sequence, Optional, Tuple
import math
import numpy as np
import matplotlib.pyplot as plt
from .theme import apply_minimal_theme, cm_to_in, DEFAULT_PALETTE, ensure_rubik_font
from .utils import save_figure, slugify

# Egyetlen helyen szabályozható a default
DEFAULT_RADAR_SIZE_CM: Tuple[float, float] = (10.0, 10.0)

def set_default_radar_size(size_cm: Tuple[float, float]) -> None:
    global DEFAULT_RADAR_SIZE_CM
    DEFAULT_RADAR_SIZE_CM = size_cm

def save_radar(labels: Sequence[str],
               series_main: Sequence[float],
               series_comp: Optional[Sequence[float]] = None,
               title: Optional[str] = None,
               r_range: Optional[Tuple[float, float]] = None,
               size_cm: Optional[Tuple[float, float]] = None,
               filename: Optional[str] = None,
               palette: Optional[dict[str, str]] = None):
    apply_minimal_theme()

    # Use brand palette (can be overridden via `palette` arg)
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    main_c = pal.get("secondary", "#ffd500")  # main series
    comp_c = pal.get("muted", "#f0aa00")      # comparison series

    # ← NEW: modul default, ha nincs megadva
    if size_cm is None:
        size_cm = DEFAULT_RADAR_SIZE_CM

    n = len(labels)
    angles = np.linspace(0, 2*math.pi, n, endpoint=False)
    labels = list(labels)

    angles = np.concatenate([angles, [angles[0]]])
    s1 = list(series_main) + [series_main[0]]
    s2 = list(series_comp) + [series_comp[0]] if series_comp is not None else None

    fig, ax = plt.subplots(
        subplot_kw=dict(polar=True),
        figsize=(cm_to_in(size_cm[0]), cm_to_in(size_cm[1])),
        dpi=300
    )

    ax.plot(angles, s1, linewidth=2.0, color=main_c)
    ax.fill(angles, s1, alpha=0.12, color=main_c)

    if s2 is not None:
        ax.plot(angles, s2, linewidth=1.6, linestyle="--", color=comp_c)
        ax.fill(angles, s2, alpha=0.09, color=comp_c)

    ax.set_xticks(angles[:-1], labels)
    if r_range:
        ax.set_rmin(r_range[0]); ax.set_rmax(r_range[1])

    if title:
        ax.set_title(title, pad=20)

    fname = filename or f"{slugify(title or 'radar')}.png"
    out = save_figure(fig, fname)
    plt.close(fig)
    return out