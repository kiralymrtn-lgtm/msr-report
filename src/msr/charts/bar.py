"""
egyszerű oszlopdiagram generátor PNG-be, „nyomdai” minőségben.

célok:
- a lap hasznos szélességéhez illeszkedjen (cm → inch konverzió)
- 300 dpi mentés (pdf-ben is éles marad)
- brand színek: „normál” oszlopok és egy kiemelt oszlop (pl. saját/csoport)
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional

import math
import matplotlib.pyplot as plt

from ..utils.paths import local_path, ensure_dir

# segédfüggvény: cm → inch (matplotlib a figurát inchben méretezi)
def _cm_to_inch(cm: float) -> float:
    return cm / 2.54

def save_simple_bar(
    values: List[float],
    labels: List[str],
    highlight_index: Optional[int] = None,
    *,
    usable_width_cm: float = 30.0,   # a Te lapod: 32cm - 2×1cm margó = ~30cm
    height_cm: float = 10.0,        # tetszőleges; 10cm jól néz ki ezeken a layoutokon
    dpi: int = 300,
    filename: str = "bar_demo.png",
    color_normal: str = "#0047AB",   # brand-primary
    color_highlight: str = "#FF6A00" # accent (kiemelés)
) -> Path:
    """
    :param values: oszlopok magasságai
    :param labels: oszlopok feliratai (x tengely)
    :param highlight_index: melyik oszlop legyen kiemelve (None = nincs kiemelés)
    :param usable_width_cm: a tényleges, tartalomra használható szélesség cm-ben
    :param height_cm: a grafikon magassága cm-ben
    :param dpi: mentési felbontás (nyomtatáshoz 300 dpi ajánlott)
    :param filename: kimeneti fájlnév (a local/output/assets/charts/ alá kerül)
    :param color_normal: alap oszlop szín
    :param color_highlight: kiemelt oszlop szín
    :return: a létrejött PNG absz. útvonala
    """

    if len(values) != len(labels):
        raise ValueError("values és labels hossza nem egyezik")

    # átalakítjuk a cm méreteket inch-re a figurához
    width_in = _cm_to_inch(usable_width_cm)
    height_in = _cm_to_inch(height_cm)

    # kimeneti mappa: local/output/assets/charts
    out_dir = local_path("output", "assets", "charts")
    ensure_dir(out_dir)
    out_path = out_dir / filename

    # ~~~ FIGURA LÉTREHOZÁSA ~~~
    # figsize: (szélesség_inch, magasság_inch), dpi: mentéskor is ezt használjuk
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)

    # oszlopszínek: alapból mind normal, de a highlight_index-et átírjuk
    colors = [color_normal] * len(values)
    if highlight_index is not None and 0 <= highlight_index < len(values):
        colors[highlight_index] = color_highlight

    # az oszlopok kirajzolása
    x = list(range(len(values)))
    bars = ax.bar(x, values, color=colors)

    # értékfeliratok az oszlopok tetején (kicsi paddinggel)
    for rect, val in zip(bars, values):
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            height,
            f"{val:.1f}",
            ha="center",
            va="bottom",
            fontsize=9
        )

    # x tengely címkék (dőlés, ha hosszú), y rács halványan
    ax.set_xticks(x, labels, rotation=0, fontsize=9)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.5)

    # „tiszta” stílus: felesleges keretek le
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    # szélélek beállítása, hogy ne vágja le a feliratokat
    plt.tight_layout()

    # mentés fehér háttérrel (PDF-ben szebb, mint az átlátszó)
    fig.savefig(out_path, dpi=dpi, facecolor="white")
    plt.close(fig)

    return out_path
