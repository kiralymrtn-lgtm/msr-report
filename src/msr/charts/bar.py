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
    title_fontsize: float | None = None,
    compare_values: Sequence[float] | None = None,
    highlight_index: int | None = None,
    show_x_labels: bool = False,
    x_label_rotation: float = 0.0,
    x_label_fontsize: float = 8.0,
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
    overlay_line_pad_frac: float = 0.00,
    overlay_value_labels: bool = True,
    overlay_value_label_fmt: str = "{y:.1f}",
    overlay_value_label_offset_pts: float = 4.0,
    value_label_fmt: str | None = None,
    value_label_color: str | None = None,
    main_label: str = "Értékek",
    comp_label: str = "Csoport",
    overlay_label: str = "Partner",
    show_legend: bool = True,
    legend_loc: str = "lower center",
    legend_frame: bool = False,
    legend_below: bool = False,
    legend_pad: float = 0.14,
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

    # Fallback formats if the caller passed None via YAML
    if not value_label_fmt:
        value_label_fmt = "{val:.1f}"
    if not overlay_value_label_fmt:
        overlay_value_label_fmt = "{y:.1f}"

    # Prepare explicit legend handles (to control legend order)
    legend_handles: list = []
    legend_labels: list[str] = []

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
        # Legend proxy for main series (bar patch) – enforced order
        main_handle = plt.Rectangle((0, 0), 1, 1, facecolor=sec, edgecolor="none")
        legend_handles.append(main_handle); legend_labels.append(main_label)

        if annotate:
            for rect, val in zip(bars, values):
                # érték az oszlop KÖZEPÉN
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height()/2.0,
                        value_label_fmt.format(val=val),
                        ha="center", va="center", fontsize=8,
                        color=(value_label_color or txt)
                        )
    else:
        width = group_bar_width if group_bar_width is not None else default_group_width
        vals = np.array(values, dtype=float)
        comp = np.array(compare_values, dtype=float)

        bars_main = ax.bar(x - width/2.0, vals, width=width, color=sec, label=main_label)
        bars_comp = ax.bar(x + width/2.0, comp, width=width, color=mut, label=comp_label)
        # Legend proxies for side-by-side bars — order: main then comp
        main_handle = plt.Rectangle((0, 0), 1, 1, facecolor=sec, edgecolor="none")
        comp_handle = plt.Rectangle((0, 0), 1, 1, facecolor=mut, edgecolor="none")
        legend_handles.extend([main_handle, comp_handle]); legend_labels.extend([main_label, comp_label])

        if highlight_index is not None and 0 <= highlight_index < len(vals):
            bars_main[highlight_index].set_color(txt)

        if annotate:
            for rect, val in zip(bars_main, vals):
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height()/2.0,
                        value_label_fmt.format(val=val),
                        ha="center", va="center", fontsize=8,
                        color=(value_label_color or txt)
                        )
            for rect, val in zip(bars_comp, comp):
                ax.text(rect.get_x() + rect.get_width()/2.0,
                        rect.get_height()/2.0,
                        value_label_fmt.format(val=val),
                        ha="center", va="center", fontsize=8,
                        color=(value_label_color or txt)
                        )

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
                    fontsize=8, color=(value_label_color or line_color), zorder=6,
                )

        # Legend proxy for overlay line — appended after main, so order stays consistent
        overlay_handle = plt.Line2D([0], [0], color=line_color, linewidth=overlay_line_width)
        legend_handles.append(overlay_handle); legend_labels.append(overlay_label)

    # LEGEND (explicit order using proxies)
    leg = None
    if show_legend and legend_handles:
        if legend_below:
            leg = ax.legend(
                legend_handles, legend_labels,
                loc="upper center",
                bbox_to_anchor=(0.5, -legend_pad),
                frameon=legend_frame,
                ncol=legend_ncol,
                fontsize=8,
            )
            fig.subplots_adjust(bottom=max(0.12, 0.06 + legend_pad))
        else:
            leg = ax.legend(legend_handles, legend_labels, frameon=legend_frame, loc=legend_loc, fontsize=8)

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
        _kw = {"pad": 6, "fontweight": "bold"}
        if title_fontsize is not None:
            _kw["fontsize"] = title_fontsize
        ax.set_title(title, **_kw)
    #if title:
    #    fig.suptitle(title, ha="center", y=0.99)  # a teljes képre középre
    #    fig.tight_layout(rect=[0, 0, 1, 0.96])  # hagyjunk helyet felül

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
    extra_artists = [leg] if (show_legend and leg is not None) else []
    fig.savefig(out_path, bbox_inches="tight", bbox_extra_artists=extra_artists)
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
        title_fontsize: float | None = None,
        # Legend / labels
        main_label: str = "Értékek",
        comp_label: str = "Csoport",
        overlay_label: str = "Partner",
        show_legend: bool = True,
        legend_loc: str = "lower right",
        legend_frame: bool = False,
        legend_below: bool = False,
        legend_pad: float = 0.14,
        legend_ncol: int = 2,
        # Y tengely kategória feliratok
        show_y_labels: bool = True,
        y_label_fontsize: float = 8.0,
        # Partner overlay: függőleges vonalak a rudakon
        overlay_values: Sequence[float] | None = None,
        overlay_line_color: str | None = None,
        overlay_line_width: float = 2.0,
        overlay_line_pad_frac: float = 0.00,
        # overlay-vonal feliratozás
        overlay_value_labels: bool = True,
        overlay_value_label_fmt: str = "{x:.1f}",
        overlay_label_dy_frac: float = 0.06,
        value_label_fmt: str | None = None,
        value_label_color: str | None = None,
        # group labels
        group_labels: Sequence[str] | None = None,  # elemszám = len(labels); minden elemhez egy csoportnév
        group_sep: bool = True,  # tegyünk vékony vízszintes szeparátort a csoportok közé
        group_sep_color: str | None = None,  # ha None → pal["text"] halványítva
        group_title_rotation: float = 90.0,  # csoportcímek forgatása (90° → függőleges)
        group_title_offset_axes: float = -0.22,  # balra tolás (axes-frakcióban, pl. -0.10)
        group_title_reserve_left: float = 0.22,  # bal oldali margó lefoglalása a csoportcímeknek (axes-frakció)
        group_title_fontsize: float = 8.0,  # csoportcím betűméret
        group_title_wrap: int | None = None,  # opcionális: csoportcím tördelése (max karakter/sor, csak szóköznél)
        group_colors: dict[str, str] | None = None,  # opcionális: csoportonként más rúd-szín (fő sorozatra)
) -> Path:
    """
    Vízszintes 'bar' diagram (barh).
      - Alapszín: secondary
      - Összehasonlítás: muted
      - Kiemelés: highlight_index → text szín
      - Tengelyek/tickek/spine-ok: nincsenek
      - Kétszintű Y: csoportcímek opcionális tördelése (group_title_wrap, csak szóköznél)
    """
    pal = {**DEFAULT_PALETTE, **(palette or {})}
    sec = pal["secondary"]; mut = pal["muted"]; txt = pal["text"]

    # Fallback formats if the caller passed None via YAML
    if not value_label_fmt:
        value_label_fmt = "{val:.1f}"
    if not overlay_value_label_fmt:
        overlay_value_label_fmt = "{x:.1f}"

    # Prepare explicit legend handles (to control legend order)
    legend_handles: list = []
    legend_labels: list[str] = []

    if size_cm is None:
        size_cm = DEFAULT_BAR_SIZE_CM
    fig, ax = _fig(size_cm)
    extra_artists: list = []
    sep_specs: list = []  # (title_text_artist, ysep) párok – a vonalakat később, a rendererrel rajzoljuk
    reserved_left = None
    y = np.arange(len(labels))

    if compare_values is None:
        height = 0.7
        colors = [sec] * len(values)
        if highlight_index is not None and 0 <= highlight_index < len(colors):
            colors[highlight_index] = txt

        bars = ax.barh(y, values, height=height, color=colors, label=main_label)
        # Legend proxy for main series (bar patch)
        main_handle = plt.Rectangle((0, 0), 1, 1, facecolor=sec, edgecolor="none")
        legend_handles.append(main_handle); legend_labels.append(main_label)

        if annotate:
            for rect, val in zip(bars, values):
                ymid = rect.get_y() + rect.get_height() / 2.0
                xmid = rect.get_x() + rect.get_width() / 2.0
                ax.text(xmid, ymid, value_label_fmt.format(val=val), va="center", ha="center", fontsize=8,
                        color = (value_label_color or txt))
    else:
        height = 0.36
        vals = np.array(values, dtype=float)
        comp = np.array(compare_values, dtype=float)

        bars_main = ax.barh(y - height/2.0, vals, height=height, color=sec, label=main_label)
        bars_comp = ax.barh(y + height/2.0, comp, height=height, color=mut, label=comp_label)
        # Legend proxies for side-by-side bars — order: main then comp
        main_handle = plt.Rectangle((0, 0), 1, 1, facecolor=sec, edgecolor="none")
        comp_handle = plt.Rectangle((0, 0), 1, 1, facecolor=mut, edgecolor="none")
        legend_handles.extend([main_handle, comp_handle]); legend_labels.extend([main_label, comp_label])

        if highlight_index is not None and 0 <= highlight_index < len(vals):
            bars_main[highlight_index].set_color(txt)

        if annotate:
            for rect, val in zip(bars_main, vals):
                ymid = rect.get_y() + rect.get_height() / 2.0
                xmid = rect.get_x() + rect.get_width() / 2.0
                text_color = value_label_color or txt
                ax.text(xmid, ymid, value_label_fmt.format(val=val), va="center", ha="center", fontsize=8,
                        color = text_color)
            for rect, val in zip(bars_comp, comp):
                ymid = rect.get_y() + rect.get_height() / 2.0
                xmid = rect.get_x() + rect.get_width() / 2.0
                ax.text(xmid, ymid, value_label_fmt.format(val=val), va="center", ha="center", fontsize=8,
                        color = (value_label_color or txt))

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
                    fontsize=8,
                    color=(value_label_color or line_color),
                    zorder=6,
                )

        # Legend proxy for overlay line
        overlay_handle = plt.Line2D([0], [0], color=line_color, linewidth=overlay_line_width)
        legend_handles.append(overlay_handle); legend_labels.append(overlay_label)

    # --- Kétszintű Y: csoportcímek + szeparátorok ---
    if group_labels is not None and len(group_labels) == len(labels):
        # 1) csoport-spanek meghatározása (start..end indexek)
        spans: list[tuple[str,int,int]] = []
        start = 0
        for i in range(1, len(group_labels)+1):
            if i == len(group_labels) or group_labels[i] != group_labels[i-1]:
                spans.append((group_labels[start], start, i-1))
                start = i

        # 2) opcionális: fő rudak színezése csoportonként
        if group_colors:
            if compare_values is None:
                for rect, g in zip(bars, group_labels):
                    rect.set_color(group_colors.get(g, sec))
            else:
                for rect, g in zip(bars_main, group_labels):
                    rect.set_color(group_colors.get(g, sec))

        # 3) csoportcímek és szeparátorok rajzolása
        sep_col = group_sep_color or txt
        for name, a, b in spans:
            y_mid = (a + b) / 1.0 / 2.0 + 0.0  # közép
            # cím a bal margón (x: axes-frakció, y: adatkoordináta)
            wrapped_name = (
                textwrap.fill(str(name),
                              width=int(group_title_wrap),
                              break_long_words=False,
                              break_on_hyphens=True)
                if group_title_wrap else str(name)
            )
            t = ax.text(
                group_title_offset_axes, y_mid, wrapped_name,
                transform=ax.get_yaxis_transform(),  # x axes-frakció, y data
                rotation=group_title_rotation,
                ha="center", va="center",
                fontsize=group_title_fontsize, color=txt,
                clip_on=False,
            )
            extra_artists.append(t)

            # Vízszintes szeparátor: NE most rajzoljuk, hanem csak eltároljuk,
            # hogy később a csoportcím BBOX-ának BAL széléhez tudjuk kötni.
            if group_sep and b < len(labels) - 1:
                ysep = b + 0.5
                sep_specs.append((t, ysep))

        # Bal oldali margó növelése, hogy a csoportcímek kényelmesen elférjenek
        if group_title_offset_axes is not None:
            auto_left = 0.12 + max(0.0, -float(group_title_offset_axes)) * 0.6
        else:
            auto_left = 0.12
        desired_left = max(float(group_title_reserve_left), auto_left)
        # Ésszerű tartományra szorítjuk, és csak később (tight_layout után) alkalmazzuk
        desired_left = max(0.05, min(desired_left, 0.45))
        reserved_left = desired_left

    # LEGEND: don't place yet if it goes below; we'll center to full figure later
    leg = None
    legend_handles_labels = None
    if show_legend and legend_handles:
        if legend_below:
            legend_handles_labels = (legend_handles, legend_labels)
        else:
            leg = ax.legend(legend_handles, legend_labels, frameon=legend_frame, loc=legend_loc, fontsize=8)

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

    out_dir = local_path("output", "assets", "charts")
    ensure_dir(out_dir)
    out_path = out_dir / filename

    # 1) renderer előállítása (bbox számításokhoz)
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    except Exception:
        renderer = None

    # 2) bal margó a csoportcímeknek (ha kell) – még a layout előtt
    if reserved_left is not None:
        try:
            fig.subplots_adjust(left=reserved_left)
        except Exception:
            pass

    # 3) extra artistok (csoportcímek, szeparátorok, LEGEND, cím)
    extra = list(extra_artists)
    if show_legend and leg is not None:
        # ha a legend az axes-en kívülre lóg, vegyük be az exportba
        extra.append(leg)

    # Compute full-image horizontal center (accounts for left/right overhang from extra artists)
    extra_left_frac = 0.0
    extra_right_frac = 0.0
    if renderer and extra:
        fig_w = float(fig.bbox.width)
        try:
            min_x = min(a.get_window_extent(renderer=renderer).x0 for a in extra)
            max_x = max(a.get_window_extent(renderer=renderer).x1 for a in extra)
            extra_left_frac = max(0.0, -min_x / fig_w)
            extra_right_frac = max(0.0, (max_x - fig_w) / fig_w)
        except Exception:
            pass
    x_center_full = (1.0 + extra_right_frac - extra_left_frac) / 2.0

    # If the legend should be below, place it now centered to the full figure
    if show_legend and legend_handles_labels is not None:
        handles, labels_ = legend_handles_labels
        leg = fig.legend(
            handles, labels_,
            loc="upper center",
            bbox_to_anchor=(x_center_full, -legend_pad),
            frameon=legend_frame,
            ncol=legend_ncol,
            fontsize=8,
            bbox_transform=fig.transFigure,
        )
        extra.append(leg)
        fig.subplots_adjust(bottom=max(0.12, 0.06 + legend_pad))

    # --- Csoport-szeparátorok kirajzolása a csoportcím BAL széléhez igazítva ---
    if sep_specs and renderer:
        for (title_artist, ysep) in sep_specs:
            bbox = title_artist.get_window_extent(renderer=renderer)
            # a bal szélt display→axes frakcióra alakítjuk (csak X kell)
            x0_axes = ax.transAxes.inverted().transform((bbox.x0, 0))[0]
            x1_axes = -0.02  # enyhén az y-tengely bal oldalán végződjön
            sep_line = plt.Line2D([x0_axes, x1_axes], [ysep, ysep],
                                  transform=ax.get_yaxis_transform(),
                                  color=sep_col, linewidth=0.5, alpha=0.25,
                                  zorder=1, clip_on=False)
            ax.add_line(sep_line)
            extra.append(sep_line)

    # 4) opcionális: cím középre, a teljes export-szélességhez mérve
    if title:
        st = fig.text(
            x_center_full, 0.985, title,
            ha="center", va="top",
            fontweight="bold",
            fontsize=(title_fontsize if title_fontsize is not None else None),
        )
        extra.append(st)
        fig.subplots_adjust(top=0.92)

    # 5) tight_layout – a bal és felső keret tiszteletben tartásával; ne dobjon warningot szűk esetekben
    import warnings
    tl_rect_left = float(reserved_left) if reserved_left is not None else 0.06
    tl_rect_top = 0.92 if title else 0.98
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        fig.tight_layout(rect=[tl_rect_left, 0.0, 1.0, tl_rect_top])

    # 6) mentés – az összes extra artisttal (legend, csoportcímek, szeparátorok, cím)
    fig.savefig(out_path, bbox_inches="tight", bbox_extra_artists=extra)

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