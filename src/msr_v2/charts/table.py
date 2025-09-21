from typing import Sequence, Any
import numpy as np
import matplotlib.pyplot as plt
import textwrap as tw
from pathlib import Path
from .base import fig_ax, wrap_title, ensure_out_dirs, OUT_TABLES
from ..config import Style
from ..theme import apply_theme

def _fmt(x: Any) -> str:
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.1f}"
    return str(x)

def save_table(
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    *,
    filename: str,
    title: str | None = None,
    style: Style,
    overrides: dict | None = None,
):
    s = style.merge_overrides(overrides); apply_theme(s); ensure_out_dirs()
    fig, ax = fig_ax(s)
    ax.set_axis_off()

    tbl = (overrides or {}).get("table", {}) if isinstance(overrides, dict) else {}
    cols_cfg = tbl.get("columns")  # lehet None
    align_cfg = tbl.get("align", None)  # pl. ["left","center","center"]

    # zebra sorkiemelés (váltakozó háttérszín) – YAML: overrides.table.zebra
    zebra = bool(tbl.get("zebra", False))
    # Egyszerű globális színbeállítás a teljes TÖRZSRE (header NEM változik)
    body_bg = tbl.get("body_bg")    # pl. "#FFFFFF" vagy "#F7F9FC"
    body_fg = tbl.get("body_fg")    # pl. "#243746"

    # --- Globális (alap) beállítások a sor/fejléc vertikális "vizuális" magasságára és cella-paddingre ---
    DEFAULT_ROW_VPAD = 0.60      # a sor "vizuális" magasságát befolyásoló tényező (betűméret köré rakott felső+alsó ráhagyás, arány)
    DEFAULT_HEADER_VPAD = 2.80   # fejlécsornál kicsit nagyobb alap ráhagyás
    DEFAULT_ROW_PAD = 0.02       # matplotlib cell.PAD (minden irány), adatsor
    DEFAULT_HEADER_PAD = 0.02    # matplotlib cell.PAD (minden irány), fejléc

    row_vpad = float(tbl.get("row_vpad", DEFAULT_ROW_VPAD))
    header_vpad = float(tbl.get("header_vpad", DEFAULT_HEADER_VPAD))
    row_cell_pad = float(tbl.get("cell_pad", DEFAULT_ROW_PAD))
    header_cell_pad = float(tbl.get("header_cell_pad", DEFAULT_HEADER_PAD))


    # --- oszlopszélességek cm-ben → figura szélesség + colWidths ---
    col_widths = None  # ezt adjuk majd a ax.table(..., colWidths=...) paraméternek

    # 1) globális lista: col_widths_cm
    widths_cm = tbl.get("col_widths_cm")

    # 2) vagy per-column: columns[].width_cm
    if not widths_cm and cols_cfg:
        per = [c.get("width_cm") for c in cols_cfg]
        if any(w is not None for w in per):
            widths_cm = per

    if widths_cm:
        # szűrés + float
        widths_cm = [float(w) for w in widths_cm if w is not None]
        if widths_cm:
            total_cm = sum(widths_cm)
            # a matplotlib colWidths arányt vár → normalizáljuk
            col_widths = [w / total_cm for w in widths_cm]

            # a figura szélességét is állítsuk a megadott összegre
            cur_w_in, cur_h_in = fig.get_size_inches()
            target_w_in = total_cm / 2.54

            # magasság először explicit YAML-ből (table.height_cm vagy overrides.size.cm_h)
            height_cm = tbl.get("height_cm")
            if not height_cm:
                height_cm = (overrides or {}).get("size", {}).get("cm_h") if isinstance(overrides, dict) else None
            if height_cm:
                target_h_in = float(height_cm) / 2.54
            else:
                # --- Automatikus magasság: sorok száma, betűméret és vpad alapján ---
                fs_pt = float(getattr(s.labels, "y_fontsize", 8))
                pt_to_in = 1.0 / 72.0
                # egy adat sor becsült vizuális magassága (inch): betűméret + felül+alul vpad
                row_h_in = fs_pt * (1.0 + 2.0 * row_vpad) * pt_to_in
                # fejléc sor
                header_h_in = fs_pt * (1.0 + 2.0 * header_vpad) * pt_to_in
                nrows = len(rows)
                # felső/alsó perem (inch) – kicsi, mert úgyis bbox_inches="tight" lesz mentéskor
                top_margin_in = 0.15
                bottom_margin_in = 0.15
                target_h_in = top_margin_in + header_h_in + nrows * row_h_in + bottom_margin_in

            fig.set_size_inches(target_w_in, target_h_in, forward=True)

    # oszloponkénti formátum a YAML-ból (ha van), különben None
    fmt_per_col = None
    if cols_cfg and isinstance(cols_cfg, list):
        fmt_per_col = []
        for c in cols_cfg:
            fmt_per_col.append(c.get("fmt"))  # pl. "{val:.1f}" vagy "{val:.1f}%"

    cell_text = []
    for r in rows:
        # r lehet [label, v] vagy [label, v, c]
        out_row = []
        for j, val in enumerate(r):
            if j == 0:
                out_row.append(str(val))  # label oszlop: sima string (wrap-et már assign megcsinálhatja)
            else:
                if fmt_per_col and j < len(fmt_per_col) and fmt_per_col[j]:
                    try:
                        out_row.append(fmt_per_col[j].format(val=float(val)) if val is not None else "")
                    except Exception:
                        out_row.append("" if val is None else str(val))
                else:
                    # fallback: egyszerű str
                    out_row.append("" if val is None else str(val))
        cell_text.append(out_row)


    # --- Header wrap per oszlop (columns[].header_wrap), fallback: overrides.table.header_wrap, majd global (s.table.header_wrap)
    # 1) globális default a Style-ból (assignment_v2.yaml global.table.header_wrap)
    global_hw = None
    if hasattr(s, "table") and isinstance(getattr(s, "table"), dict):
        global_hw = s.table.get("header_wrap")

    # 2) chart-szintű default (overrides.table.header_wrap)
    ov_tbl = (overrides or {}).get("table", {}) if isinstance(overrides, dict) else {}
    default_hw = ov_tbl.get("header_wrap", global_hw)

    # 3) per-oszlop wrap lista összeállítása
    header_wraps = []
    if cols_cfg and isinstance(cols_cfg, list) and any(("header_wrap" in (c or {})) for c in cols_cfg):
        for j in range(len(columns)):
            hw = None
            if j < len(cols_cfg) and isinstance(cols_cfg[j], dict):
                hw = cols_cfg[j].get("header_wrap")
            header_wraps.append(hw if hw is not None else default_hw)
    else:
        header_wraps = [default_hw] * len(columns)

    # 4) fejléc címkék felépítése oszloponkénti wrap-pal
    col_labels = []
    for j, c in enumerate(columns):
        text = str(c)
        hw = header_wraps[j]
        if hw:
            try:
                w = int(hw)
                text = tw.fill(text, width=w, break_long_words=False, break_on_hyphens=True)
            except Exception:
                pass
        col_labels.append(text)



    pal = s.palette
    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        colLoc="left",
        cellLoc="left",
        loc="upper left",
        bbox=[0, 0, 1, 1],
        colWidths=col_widths,  # normalizált arányok listája, vagy None
    )
    table.auto_set_font_size(False)

    for (i, j), cell in table.get_celld().items():
        # külön PAD a fejlécnek és a törzsnek
        cell.PAD = (header_cell_pad if i == 0 else row_cell_pad)
        cell.set_linewidth(0.5)  # kör- és rácsvonalak globálisan


    table.set_fontsize(s.labels.y_fontsize)



    # --- Igazítás oszloponként (YAML: overrides.table.align) ---
    ncols = len(col_labels)
    nrows = len(rows)
    for j in range(ncols):
        # kívánt igazítás a YAML-ből, különben: label=left, többi=right
        desired = None
        if align_cfg and j < len(align_cfg):
            desired = str(align_cfg[j]).lower()
        if desired not in ("left", "center", "right"):
            desired = "left" if j == 0 else "right"

        # >>> FEJLÉC IGAZÍTÁS – JAVÍTÁS <<<
        hdr_ha = None
        if align_cfg and j < len(align_cfg):
            hdr_ha = str(align_cfg[j]).lower()
        if hdr_ha not in ("left", "center", "right"):
            hdr_ha = "left" if j == 0 else "center"
        table[0, j].get_text().set_ha(hdr_ha)

        # adatsorok igazítása
        for i in range(1, nrows + 1):
            table[i, j].get_text().set_ha(desired)

    # fejléc
    ncols = len(columns)
    for j in range(ncols):
        cell = table[0, j]
        cell.set_facecolor(pal.text)
        cell.get_text().set_color(pal.secondary)
        cell.get_text().set_weight("normal")

    # törzs – egyszerű logika:
    # 1) ha meg van adva globális body_bg/body_fg → azt használjuk minden adatsorra
    # 2) különben, ha zebra: true → váltakozó háttér
    # 3) különben → minden sor fehér, alap szövegszínnel
    nrows = len(rows)
    for i in range(1, nrows + 1):
        for j in range(ncols):
            cell = table[i, j]
            if body_bg or body_fg:
                cell.set_facecolor(body_bg if body_bg else "#FFFFFF")
                cell.get_text().set_color(body_fg if body_fg else pal.text)
            elif zebra:
                bg = "#FFFFFF" if (i % 2 == 1) else pal.background
                cell.set_facecolor(bg)
                cell.get_text().set_color(pal.text)
            else:
                cell.set_facecolor("#FFFFFF")
                cell.get_text().set_color(pal.text)

    if title:
        ax.set_title(wrap_title(title, s), pad=s.title.pad)


    out = OUT_TABLES / filename
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out