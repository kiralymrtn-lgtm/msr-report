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
    ax.yaxis.grid(False)

    # --- Legacy MSR: két szintű y-tengely (group labels) támogatás ---
    ov = overrides or {}
    group_labels = ov.get("group_labels")
    group_colors = ov.get("group_colors", {})
    group_sep = bool(ov.get("group_sep", False))
    # régi assignmentben: -1.80 tipikus
    group_title_offset_axes = float(ov.get("group_title_offset_axes", -1.00))
    # opcionális: előre foglalt bal margó (axes bal oldalán kívüli címekhez)
    group_title_reserve_left = float(ov.get("group_title_reserve_left", 0.30))
    # y-címkék látszódjanak-e
    show_y_labels_ov = ov.get("show_y_labels")
    if show_y_labels_ov is not None:
        show_y_labels = bool(show_y_labels_ov)
    # per-chart legend override (régi séma):
    if ov.get("show_legend") is not None:
        s.legend.show = bool(ov.get("show_legend"))

    # Csoportonként szín (ha megadva), különben secondary
    if group_labels and isinstance(group_labels, list) and len(group_labels) == len(labels):
        bar_colors = [group_colors.get(gl, s.palette.secondary) for gl in group_labels]
    else:
        bar_colors = s.palette.secondary

    # Van-e tényleges (nem üres) cím?
    has_title = bool(title and str(title).strip())

    # Egysávos ábrán a függőleges tartományt a cím függvényében állítjuk:
    # - ha van cím: szimmetrikus (-1..1), hagyunk neki helyet
    # - ha nincs cím: feljebb toljuk a sávot (-1..0.8), így kevesebb üres hely marad felül
    if len(labels) == 1:
        if has_title:
            ax.set_ylim(-1.0, 1.0)
        else:
            ax.set_ylim(-1.0, 0.7)

    # Bar thickness (bar height) – overridable from YAML via `overrides.bar_height`
    bar_height = float((overrides or {}).get("bar_height", 0.8))
    bars = ax.barh(y, values, height=bar_height, color=bar_colors, label="Az Ön értékei")

    # Csoport elválasztók és csoportcímek kirajzolása
    if group_labels and isinstance(group_labels, list) and len(group_labels) == len(labels):
        # group → y indexek (megtartva a megjelenési sorrendet)
        idx_by_group = {}
        order = []
        for i, gname in enumerate(group_labels):
            if gname not in idx_by_group:
                idx_by_group[gname] = []
                order.append(gname)
            idx_by_group[gname].append(y[i])

        # opcionális elválasztó vonalak csoportok között
        if group_sep and len(order) > 1:
            for k in range(len(order) - 1):
                last_y = max(idx_by_group[order[k]])
                y_sep = float(last_y) + 0.5
                # A vonal a LABEL-ek között fusson, balra egészen a csoportcímek bal széléig.
                # Ehhez x-ben axes-frakciót használunk (y adatkoordinátában marad).
                x0_axes = group_title_offset_axes  # bal vég: csoportcímek bal széle
                x1_axes = -0.02  # jobb vég: a tengely (0.0 → csak a label-oszlopban fusson)
                ax.plot([x0_axes, x1_axes], [y_sep, y_sep],
                        transform=ax.get_yaxis_transform(),
                        color="#D0D5DD", linewidth=0.8, solid_capstyle="butt",
                        clip_on=False)

        # csoportcímek a bal oldalon (axes transzformációban, így az offset axes-frakció)
        # opcionális tördelés támogatása: overrides.group_title_wrap
        wrap_w = ov.get("group_title_wrap")

        def _wrap_group_title(txt: str) -> str:
            if wrap_w is None:
                return str(txt)
            try:
                w = int(wrap_w)
            except Exception:
                w = None
            if not w:
                return str(txt)
            return tw.fill(str(txt), width=w, break_long_words=False, break_on_hyphens=True)

        for gname in order:
            yy = idx_by_group[gname]
            y_center = float(sum(yy) / len(yy))
            ha = "right" if group_title_offset_axes < 0 else "left"
            ax.text(group_title_offset_axes, y_center, _wrap_group_title(gname),
                    transform=ax.get_yaxis_transform(), va="center", ha=ha,
                    fontsize=getattr(s.labels, "y_fontsize", 8), color=s.palette.text,
                    clip_on=False, zorder=4)

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

    # Értékek a sáv közepén – támogatja a régi annotate/value_label_fmt/value_label_color override-okat
    use_annotate = bool(ov.get("annotate", True))
    fmt_str = ov.get("value_label_fmt", fmt_value)
    val_color = ov.get("value_label_color", (s.labels.value_color or s.palette.text))

    if use_annotate:
        for rect, v in zip(bars, values):
            ymid = rect.get_y() + rect.get_height() / 2.0
            xmid = rect.get_x() + rect.get_width() / 2.0
            ax.text(
                xmid, ymid,
                fmt_str.format(val=float(v)),
                va="center", ha="center", fontsize=s.labels.y_fontsize,
                color=val_color
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

    if has_title:
        # Cím középre igazítása a VIZUÁLIS tartomány felett (group + labels + bars együtt).
        # Nem hívunk draw()-t, így nem omlik össze a CL.
        pos = ax.get_position()  # axes bbox in figure fraction
        if group_labels and isinstance(group_labels, list) and len(group_labels) == len(labels):
            # bal szél: axes bal + (negatív) group offset * axes szélesség (axes-frakció → figure-frakció)
            left = pos.x0 + group_title_offset_axes * pos.width
            left = max(0.0, left)  # ne menjen a figura bal széle mögé
            right = pos.x1  # jobb szél: axes jobb
            x_center = (left + right) / 2.0
        else:
            # nincs grouping → a teljes figura közepe
            x_center = 0.5

        fig.suptitle(
            wrap_title(title, s),
            fontsize=s.title.size,
            fontweight=s.title.weight,
            x=x_center,
            y=1.05,
        )

    if s.legend.show:
        s.chart_type = "bar"
        place_legend(ax, fig, s)

    out = OUT_CHARTS / filename

    fig.savefig(out, bbox_inches="tight", pad_inches=0.1);
    plt.close(fig)  # ← pad_inches hozzáadása
    return out