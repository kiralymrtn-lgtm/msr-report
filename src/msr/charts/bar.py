from __future__ import annotations
from pathlib import Path
from typing import Sequence
import numpy as np
import matplotlib.pyplot as plt
import textwrap

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
    # ÚJ: X-tick tördelés/ritkítás + hézag/szélesség
    show_every_nth_label: int = 1,        # 1 → mindet, 2 → minden másodikat stb.
    x_label_wrap: int | None = None,      # pl. 10 → max 10 karakter soronként (új sorok)
    bar_spacing: float = 0.0,             # 0.0 → régi viselkedés; 0.2 → nagyobb hézag kategóriák között
    bar_width: float | None = None,       # egy sorozatnál: None → 0.7 (alap)
    group_bar_width: float | None = None, # két sorozatnál: None → 0.36 (alap)
    x_margin: float = 0.02,               # extra margó bal/jobb (hogy ne vágjon le semmit)
    # Overlay horizontal lines (pl. partner érték)
    overlay_values: Sequence[float] | None = None,
    overlay_line_color: str | None = None,
    overlay_line_width: float = 2.0,
    overlay_line_pad_frac: float = 0.15,
    overlay_value_labels: bool = True,
    overlay_value_label_fmt: str = "{y:.1f}",
    overlay_value_label_offset_pts: float = 4.0,
    main_label: str = "Értékek",
    comp_label: str = "Csoport",
    overlay_label: str = "Partner",
    legend_loc: str = "lower center",
    legend_frame: bool = False,
    legend_below: bool = False,
    legend_pad: float = 0.12,
    legend_ncol: int = 2,
) -> Path:
    """
    Függőleges oszlopdiagram (column).

    ÚJ:
      - x_label_wrap: több soros (tördelt) X-feliratok
      - show_every_nth_label: csak minden n-edik kategória felirata
      - bar_spacing: nagyobb hézag az oszlopcsoportok között
      - bar_width / group_bar_width: oszlop-szélesség kézi állítása
    """
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    sec = pal["secondary"]; mut = pal["muted"]; txt = pal["text"]

    if size_cm is None:
        size_cm = DEFAULT_BAR_SIZE_CM
    fig, ax = _fig(size_cm)

    # X pozíciók – opcionális extra hézaggal
    x = np.arange(len(labels), dtype=float)
    if bar_spacing and bar_spacing > 0:
        x = x * (1.0 + float(bar_spacing))

    default_single_width = 0.7
    default_group_width = 0.36

    if compare_values is None:
        width = bar_width if bar_width is not None else default_single_width
        colors = [sec] * len(values)
        if highlight_index is not None and 0 <= highlight_index < len(colors):
            colors[highlight_index] = txt

        bars = ax.bar(x, values, width=width, color=colors, label=main_label)

        if annotate:
            for rect, val in zip(bars, values):
                # érték az oszlop KÖZEPÉN
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height()/2.0,
                        f"{val:.1f}",
                        ha="center", va="center", fontsize=8)
    else:
        width = group_bar_width if group_bar_width is not None else default_group_width
        vals = np.array(values, dtype=float)
        comp = np.array(compare_values, dtype=float)

        bars_main = ax.bar(x - width/2.0, vals, width=width, color=sec, label=main_label)
        bars_comp = ax.bar(x + width/2.0, comp, width=width, color=mut, label=comp_label)

        if highlight_index is not None and 0 <= highlight_index < len(vals):
            bars_main[highlight_index].set_color(txt)

        if annotate:
            for rect, val in zip(bars_main, vals):
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height()/2.0,
                        f"{val:.1f}",
                        ha="center", va="center", fontsize=8)
            for rect, val in zip(bars_comp, comp):
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height()/2.0,
                        f"{val:.1f}",
                        ha="center", va="center", fontsize=8)

    # Overlay vízszintes vonalak (pl. partner érték)
    if overlay_values is not None:
        line_color = overlay_line_color or txt
        target_bars = (bars_main if compare_values is not None else bars)
        for rect, y in zip(target_bars, overlay_values):
            bw = rect.get_width()
            x0 = rect.get_x() - bw * overlay_line_pad_frac
            x1 = rect.get_x() + bw * (1.0 + overlay_line_pad_frac)
            ax.hlines(y, x0, x1, color=line_color, linewidth=overlay_line_width, zorder=5)

            # ← ÚJ: data label a vonal BAL oldalán, fix (pont) eltolással
            if overlay_value_labels:
                ax.annotate(
                    overlay_value_label_fmt.format(y=y),
                    xy=(x0, y),
                    xytext=(-overlay_value_label_offset_pts, 0),
                    textcoords="offset points",
                    ha="right", va="center",
                    fontsize=8, color=line_color, zorder=6,
                )

        # Legend proxy az overlay vonalhoz
        ax.plot([], [], color=line_color, linewidth=overlay_line_width, label=overlay_label)


    # LEGEND
    if legend_below:
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -legend_pad),
            frameon=legend_frame,
            ncol=legend_ncol,
            fontsize=8.5,
        )
        fig.subplots_adjust(bottom=max(0.12, 0.06 + legend_pad))
    else:
        ax.legend(frameon=legend_frame, loc=legend_loc, fontsize=8.5)

    # X-feliratok: tördelés + ritkítás
    if show_x_labels:
        if x_label_wrap and x_label_wrap > 0:
            proc_labels = [textwrap.fill(str(lbl), width=int(x_label_wrap)) for lbl in labels]
        else:
            proc_labels = [str(lbl) for lbl in labels]

        if show_every_nth_label > 1:
            sel_idx = np.arange(0, len(x), int(show_every_nth_label), dtype=int)
            ax.set_xticks(x[sel_idx])
            ax.set_xticklabels([proc_labels[i] for i in sel_idx],
                               rotation=x_label_rotation, fontsize=x_label_fontsize)
        else:
            ax.set_xticks(x)
            ax.set_xticklabels(proc_labels, rotation=x_label_rotation, fontsize=x_label_fontsize)
    else:
        ax.set_xticks([])

    ax.set_yticks([])

    if y_range:
        ax.set_ylim(y_range)
    if title:
        ax.set_title(title, pad=6)

    if show_x_labels:
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis="y", which="both", left=False, right=False, labelleft=False)
        ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=True)
    else:
        _hide_all_axes(ax)

    # Extra vízszintes margó, hogy a feliratok/labelek elférjenek
    if x_margin and x_margin > 0:
        ax.margins(x=float(x_margin))

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
        # Legend / labels
        main_label: str = "Értékek",
        comp_label: str = "Csoport",
        overlay_label: str = "Partner",
        legend_loc: str = "lower right",
        legend_frame: bool = False,
        legend_below: bool = False,
        legend_pad: float = 0.12,
        legend_ncol: int = 2,
        # Y tengely kategória feliratok
        show_y_labels: bool = True,
        y_label_fontsize: float = 9.0,
        # Partner overlay: függőleges vonalak a rudakon
        overlay_values: Sequence[float] | None = None,
        overlay_line_color: str | None = None,
        overlay_line_width: float = 2.0,
        overlay_line_pad_frac: float = 0.15,
        # overlay-vonal feliratozás
        overlay_value_labels: bool = True,
        overlay_value_label_fmt: str = "{x:.1f}",
        overlay_label_dy_frac: float = 0.06,
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

        bars = ax.barh(y, values, height=height, color=colors, label=main_label)

        if annotate:
            for rect, val in zip(bars, values):
                ymid = rect.get_y() + rect.get_height() / 2.0
                xmid = rect.get_x() + rect.get_width() / 2.0
                ax.text(xmid, ymid, f"{val:.1f}", va="center", ha="center", fontsize=8.5)
    else:
        height = 0.36
        vals = np.array(values, dtype=float)
        comp = np.array(compare_values, dtype=float)

        bars_main = ax.barh(y - height/2.0, vals, height=height, color=sec, label=main_label)
        bars_comp = ax.barh(y + height/2.0, comp, height=height, color=mut, label=comp_label)

        if highlight_index is not None and 0 <= highlight_index < len(vals):
            bars_main[highlight_index].set_color(txt)

        if annotate:
            for rect, val in zip(bars_main, vals):
                ymid = rect.get_y() + rect.get_height() / 2.0
                xmid = rect.get_x() + rect.get_width() / 2.0
                ax.text(xmid, ymid, f"{val:.1f}", va="center", ha="center", fontsize=8.5)
            for rect, val in zip(bars_comp, comp):
                ymid = rect.get_y() + rect.get_height() / 2.0
                xmid = rect.get_x() + rect.get_width() / 2.0
                ax.text(xmid, ymid, f"{val:.1f}", va="center", ha="center", fontsize=8.5)

    # Optional overlay vertical lines (e.g., group averages)
    if overlay_values is not None:
        line_color = overlay_line_color or txt
        # pick the bar collection: main bars if compare, else the only bars
        target_bars = (bars_main if compare_values is not None else bars)
        for rect, xval in zip(target_bars, overlay_values):
            bh = rect.get_height()
            # a vonal a sávnál egy kicsit hosszabb legyen
            y0 = rect.get_y() - bh * overlay_line_pad_frac
            y1 = rect.get_y() + bh * (1.0 + overlay_line_pad_frac)
            ax.vlines(xval, y0, y1, color=line_color, linewidth=overlay_line_width, zorder=5)

            # LABEL: a vonal fölé
            if overlay_value_labels:
                ax.text(
                    xval,
                    y1 + bh * overlay_label_dy_frac,  # picit fölé
                    overlay_value_label_fmt.format(x=xval),
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    zorder=6,
                )

        # legend-proxy a vonalhoz
        ax.plot([], [], color=line_color, linewidth=overlay_line_width, label=overlay_label)

    # Legend
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
        leg = ax.legend(frameon=legend_frame, loc=legend_loc, fontsize=8.5)

    if x_range:
        ax.set_xlim(x_range)

    # Y tengely címkék kapcsolhatóan
    if show_y_labels:
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=y_label_fontsize)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
        ax.tick_params(axis="y", which="both", left=False, right=False, labelleft=True)
    else:
        _hide_all_axes(ax)

    if title:
        ax.set_title(title, pad=6)

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