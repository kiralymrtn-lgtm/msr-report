#

from __future__ import annotations
from typing import Sequence, Optional, Tuple
from pathlib import Path
import yaml
import pandas as pd

from .config import Style
from .theme import apply_theme
from .charts.bar import save_bar
from .charts.column import save_column
from .charts.radar import save_radar
from .charts.table import save_table

# Egyszerű párosító: "X" -> "X{suffix}" ha létezik
def _find_pairs(db: pd.DataFrame, suffix: str) -> dict[str, str]:
    cols = set(db.columns)
    pairs = {}
    for c in db.columns:
        cand = f"{c}{suffix}"
        if cand in cols:
            pairs[c] = cand
    return pairs

def _series_for_metrics(
    db: pd.DataFrame,
    row_index: int,
    metrics: Sequence[str],
    *,
    mode: str,                # "single" | "pair"
    compare_suffix: str = "_átlag",
) -> tuple[list[str], list[float], Optional[list[float]]]:
    labels = [str(m) for m in metrics]
    if mode == "single":
        vals = [float(db.loc[row_index, m]) for m in metrics if m in db.columns]
        return labels, vals, None
    # pair
    pairs = _find_pairs(db, compare_suffix)
    vals_main: list[float] = []
    vals_comp: list[float] = []
    labs: list[str] = []
    for m in metrics:
        if m in db.columns and m in pairs and pairs[m] in db.columns:
            labs.append(m)
            vals_main.append(float(db.loc[row_index, m]))
            vals_comp.append(float(db.loc[row_index, pairs[m]]))
    return labs, vals_main, vals_comp

def _fmt_filename(name: str, partner_id: str | None) -> str:
    if not name:
        return "chart.png"
    if partner_id is None:
        return name
    try:
        return name.format(partner=str(partner_id), partner_id=str(partner_id))
    except KeyError:
        return name

def render_from_yaml(
    yaml_path: Path | str,
    *,
    db: pd.DataFrame,
    row_index: int,
    partner_id: str | None = None,
):
    cfg = yaml.safe_load(Path(yaml_path).read_text())

    # 1) Globális stílus
    base_style = Style()
    settings = cfg.get("settings") or {}
    base_style = base_style.merge_overrides(settings)

    results: list[Path] = []

    # 2) Chartok
    for ch in cfg.get("charts", []):
        typ = (ch.get("type") or "").strip().lower()
        filename = _fmt_filename(ch.get("filename") or f"{typ}.png", partner_id)
        title = ch.get("title")
        overrides = ch.get("overrides")
        source_type = (ch.get("source_type") or "single").lower()
        compare_suffix = ch.get("compare_suffix") or "_átlag"

        metrics = ch.get("metrics") or []
        labels_override = ch.get("labels")

        labels, vals, comps = _series_for_metrics(
            db, row_index, metrics, mode=("pair" if source_type == "pair" else "single"),
            compare_suffix=compare_suffix
        )
        # ha van labels_override és stimmel a hossz:
        if labels_override and len(labels_override) == len(labels):
            labels = labels_override

        if typ in ("column", "col", "columns"):
            p = save_column(
                values=vals,
                labels=labels,
                filename=filename,
                title=title,
                style=base_style,
                overrides=overrides,
                overlay_values=comps if comps is not None else None,
                show_x_labels=True,
                x_label_wrap=overrides.get("x_label_wrap") if isinstance(overrides, dict) else None,
            )
            results.append(p)
        elif typ in ("bar", "barh", "bars"):
            p = save_bar(
                values=vals,
                labels=labels,
                filename=filename,
                title=title,
                style=base_style,
                overrides=overrides,
                overlay_values=comps if comps is not None else None,
                show_y_labels=True,
            )
            results.append(p)
        elif typ in ("radar", "spider", "spiderweb"):
            p = save_radar(
                labels=labels,
                series_main=vals,
                series_comp=comps if comps is not None else None,
                filename=filename,
                title=title,
                style=base_style,
                overrides=overrides,
                r_range=tuple(ch.get("r_range")) if ch.get("r_range") else None,
            )
            results.append(p)
        elif typ in ("table", "tbl"):
            # 1) YAML overrides.table.columns → innen jönnek a fejléc címek
            tbl_cfg = (overrides or {}).get("table", {}) if isinstance(overrides, dict) else {}
            cols_cfg = tbl_cfg.get("columns")  # lehet None

            # 2×3 oszlopos split: Erősségek | Ön | Átlag  •  Gyengeségek | Ön | Átlag
            # YAML kapcsoló: overrides.table.pair_split: true
            pair_split = bool(tbl_cfg.get("pair_split", False))

            if pair_split and (comps is not None) and (len(comps) == len(vals)):
                strengths, weaknesses = [], []
                for lab, v, c in zip(labels, vals, comps):
                    # szabály: ha Ön >= Átlag → Erősségek, különben Gyengeségek
                    (strengths if (v is not None and c is not None and float(v) >= float(c)) else weaknesses).append(
                        [lab, v, c])

                # kiegyenlítjük a két oldalt ugyanannyi sorra (üres töltelék, hogy szépen egymás mellé kerüljenek)
                maxlen = max(len(strengths), len(weaknesses)) or 0

                def _pad(rows_list):
                    pad = maxlen - len(rows_list)
                    if pad > 0:
                        rows_list.extend([["", None, None]] * pad)
                    return rows_list

                strengths = _pad(strengths)
                weaknesses = _pad(weaknesses)

                # 6 oszlopos (Erősségek | Ön | Átlag | Gyengeségek | Ön | Átlag) sorok
                rows6 = []
                for i in range(maxlen):
                    s_lab, s_v, s_c = strengths[i]
                    w_lab, w_v, w_c = weaknesses[i]
                    rows6.append([s_lab, s_v, s_c, w_lab, w_v, w_c])

                # fejléc: YAML-ból, ha megadtad; különben default
                if cols_cfg and isinstance(cols_cfg, list) and len(cols_cfg) == 6:
                    columns6 = [c.get("title", "") for c in cols_cfg]
                else:
                    columns6 = [
                        "Erősségek", "Az Ön értékei", "Átlagos érték",
                        "Gyengeségek", "Az Ön értékei", "Átlagos érték",
                    ]

                p = save_table(
                    columns=columns6,
                    rows=rows6,
                    filename=filename,
                    title=title,
                    style=base_style,
                    overrides=overrides,  # a table.py innen kapja a per-oszlop fmt/align/width_cm stb.
                )
                results.append(Path(p))
                continue  # fontos: ne fusson le az alapeseti 2/3 oszlopos ág


            # 2) Sorok: 2 vagy 3 oszlop attól függően, van-e compare (comps)
            if comps is not None and len(comps) == len(vals):
                rows = [[lab, v, c] for lab, v, c in zip(labels, vals, comps)]
                # default fejléc, ha a YAML nem adott:
                if not cols_cfg:
                    columns = ["Kérdés", "Az Ön értéke", "Átlag"]
                else:
                    columns = [c.get("title", "") for c in cols_cfg]
            else:
                rows = [[lab, v] for lab, v in zip(labels, vals)]
                if not cols_cfg:
                    columns = ["Kérdés", "Érték"]
                else:
                    columns = [c.get("title", "") for c in cols_cfg]

            p = save_table(
                columns=columns,
                rows=rows,
                filename=filename,
                title=title,
                style=base_style,
                overrides=overrides,  # a table.py innen tudja elérni a columns fmt/align beállításokat
            )
            results.append(Path(p))
        else:
            # ismeretlen típus — átugorjuk csendben
            pass

    return results