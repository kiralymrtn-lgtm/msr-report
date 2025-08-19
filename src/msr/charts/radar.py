from typing import Sequence, Optional, Tuple
import math
import numpy as np
import matplotlib.pyplot as plt
from .theme import apply_minimal_theme, cm_to_in
from .utils import save_figure, slugify

def save_radar(labels: Sequence[str],
               series_main: Sequence[float],
               series_comp: Optional[Sequence[float]] = None,
               title: Optional[str] = None,
               r_range: Optional[Tuple[float, float]] = None,
               size_cm: Tuple[float, float] = (18.0, 18.0),
               filename: Optional[str] = None):
    """
    Radar chart egy (vagy két) sorozattal. Szín: matplotlib default.
    """
    apply_minimal_theme()
    n = len(labels)
    angles = np.linspace(0, 2*math.pi, n, endpoint=False)
    labels = list(labels)

    # Radar zárása
    angles = np.concatenate([angles, [angles[0]]])
    s1 = list(series_main) + [series_main[0]]
    s2 = list(series_comp) + [series_comp[0]] if series_comp is not None else None

    fig, ax = plt.subplots(subplot_kw=dict(polar=True),
                           figsize=(cm_to_in(size_cm[0]), cm_to_in(size_cm[1])))

    ax.plot(angles, s1, linewidth=2.0)
    ax.fill(angles, s1, alpha=0.1)

    if s2 is not None:
        ax.plot(angles, s2, linewidth=1.6, linestyle="--")
        ax.fill(angles, s2, alpha=0.08)

    ax.set_xticks(angles[:-1], labels)
    if r_range:
        ax.set_rmin(r_range[0]); ax.set_rmax(r_range[1])

    if title:
        ax.set_title(title, pad=20)

    fname = filename or f"{slugify(title or 'radar')}.png"
    out = save_figure(fig, fname)
    plt.close(fig)
    return out