import numpy as np
import matplotlib.pyplot as plt
import re
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
    group_title_offset_axes = float(ov.get("group_title_offset_axes", -0.35))
    group_title_reserve_left = float(ov.get("group_title_reserve_left", 0.40))
    # Egyszerűsítés: nincs forgatás
    group_title_rotation = 0.0
    # Fix tördelési szélesség (karakterben) – YAML override: group_title_wrap
    group_title_wrap_chars = int(ov.get("group_title_wrap", 10))
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

    # Csoport elválasztók és csoportcímek kirajzolása – egyszerűsített (forgatás nélkül)
    if group_labels and isinstance(group_labels, list) and len(group_labels) == len(labels):
        # group → y indexek (megjelenési sorrenddel)
        idx_by_group, order = {}, []
        for i, gname in enumerate(group_labels):
            if gname not in idx_by_group:
                idx_by_group[gname] = []
                order.append(gname)
            idx_by_group[gname].append(y[i])

        # A label-oszlop bal széle (axes-frakcióban)
        x_left_axes = group_title_offset_axes if group_title_offset_axes < 0 else -0.40

        # A label-oszlop jobb széle = y-tick feliratok BAL széle – egy kis puffer
        X_PAD = 0.005  # 0.5% axes-szélesség
        try:
            renderer = fig.canvas.get_renderer()
        except Exception:
            renderer = None
        if renderer is None:
            try:
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()
            except Exception:
                renderer = None

        x_right_axes = -0.02  # tartalék érték, ha nincs renderer
        if renderer is not None:
            xs = []
            for lab in ax.get_yticklabels():
                if not lab.get_text():
                    continue
                try:
                    bb = lab.get_window_extent(renderer=renderer)
                    bb_ax = bb.transformed(ax.transAxes.inverted())
                    xs.append(bb_ax.x0)  # a tick-felirat bal széle axes-koordinátában
                except Exception:
                    pass
            if xs:
                leftmost = min(xs)
                x_right_axes = leftmost - X_PAD  # a group-label jobb széle épp a tick-bal széle előtt

        # separator hossza (axes-frakció): ~12–15% szélesség bőven elég
        sep_len = float(ov.get("group_sep_len", 0.14))
        x_sep_left = x_right_axes - sep_len

        # SEPARATOR a group címkék között – a teljes label-zónában (tick feliratok alatt is),
        # de a sávok (bar-ok) előtt érjen véget.
        if group_sep and len(order) > 1:
            # 1) a label-zóna BAL széle: a group-címkék bal offsetje és a tick-feliratok bal széle közül a BALABB
            # (hogy biztos a teljes label-teret lefedje)
            left_label_axes = x_left_axes
            if renderer is not None and xs:
                tick_left = min(xs)  # tick-feliratok bal széle (axes-frakció)
                left_label_axes = min(left_label_axes, tick_left) - 0.25  # kis extra puffer balra

            # 2) a label-zóna JOBB széle: az x=0 adatvonal (baseline) pozíciója axes-frakcióban
            #    így a vonal nem megy be a sávok közé
            x0_pix = ax.transData.transform((0.0, 0.0))[0]
            x0_axes = ax.transAxes.inverted().transform((x0_pix, 0.0))[0]
            right_label_axes = x0_axes - 0.005  # kis puffer, hogy ne érjen bele a baseline-ba

            for k in range(len(order) - 1):
                last_y = max(idx_by_group[order[k]])
                y_sep = float(last_y) + 0.5
                ax.plot([left_label_axes, right_label_axes], [y_sep, y_sep],
                        transform=ax.get_yaxis_transform(),
                        color="#D0D5DD", linewidth=1.0, alpha=0.9, solid_capstyle="butt",
                        clip_on=False)

        # Fix tördelő: mindig 'group_title_wrap_chars' szélességgel
        def _wrap_group_simple(txt: str) -> str:
            norm = str(txt).replace("–", "-").replace("—", "-")
            return tw.fill(norm,
                           width=max(1, group_title_wrap_chars),
                           break_long_words=False,
                           break_on_hyphens=True)

        # GROUP címkék kirajzolása: jobbra zártan, a tengely előtt
        for gname in order:
            yy = idx_by_group[gname]
            y_center = float(sum(yy) / len(yy))
            text = _wrap_group_simple(gname)

            # a szöveg jobb széle fixen a x_right_axes vonalon legyen
            ax.text(
                x_right_axes, y_center, text,
                transform=ax.get_yaxis_transform(),
                va="center", ha="right",  # jobbra zárt
                fontsize=getattr(s.labels, "y_fontsize", 8),
                color=s.palette.text,
                clip_on=False, zorder=4
            )

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

    # Bal margó beállítása a group címeknek
    if group_labels and isinstance(group_labels, list) and len(group_labels) == len(labels):
        fig.subplots_adjust(left=group_title_reserve_left)

    if s.legend.show:
        s.chart_type = "bar"
        place_legend(ax, fig, s)

    out = OUT_CHARTS / filename

    fig.savefig(out, bbox_inches="tight", pad_inches=0.1);
    plt.close(fig)  # ← pad_inches hozzáadása
    return out