#

from pathlib import Path
import textwrap
import matplotlib.pyplot as plt
from ..config import Style
from ..theme import cm_to_in

OUT_CHARTS = Path("local/output/assets/charts")
OUT_TABLES = Path("local/output/assets/tables")

def fig_ax(style: Style):
    fig, ax = plt.subplots(
        figsize=(cm_to_in(style.size.cm_w), cm_to_in(style.size.cm_h)),
        dpi=style.size.dpi,
        constrained_layout=True,
    )
    fig.set_constrained_layout_pads(h_pad=0.06, w_pad=0.02, hspace=0.02, wspace=0.02)
    return fig, ax

def place_legend(ax, fig, style: Style):
    handles, labels = ax.get_legend_handles_labels()
    order_map = {"Az Ön értékei": 0, "Hasonló árbevételű cégek átlagos értékei": 1}
    idx = sorted(range(len(labels)), key=lambda i: order_map.get(labels[i], i + 100))
    H = [handles[i] for i in idx]
    L = [labels[i] for i in idx]

    if style.legend.below:
        leg = fig.legend(
            H, L,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.05),   # ← ÚJ: fix érték a pad helyett
            ncol=style.legend.ncol,
            frameon=getattr(style.legend, "frameon", False),
            prop={"size": getattr(style.legend, "fontsize", None)} if getattr(style.legend, "fontsize", None) else None,
        )
        return leg
    return ax.legend(H, L, loc=style.legend.loc)

def wrap_title(title: str, style: Style) -> str:
    if not title:
        return title
    if style.title.wrap is None:
        return title
    return textwrap.fill(
        title, width=int(style.title.wrap),
        break_long_words=False, break_on_hyphens=True
    )

def center_title_to_figure(ax):
    bb = ax.get_position()
    ax.title.set_position(((0.5 - bb.x0) / bb.width, ax.title.get_position()[1]))

def ensure_out_dirs():
    OUT_CHARTS.mkdir(parents=True, exist_ok=True)
    OUT_TABLES.mkdir(parents=True, exist_ok=True)