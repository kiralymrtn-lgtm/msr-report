from __future__ import annotations
import pandas as pd
from ..utils.paths import local_path


def load_workbook(xlsx: str = "data/input/Egyedi reportok adatbázis_2024_anonim.xlsm"):
    # védjük le: legyen biztosan string
    if not isinstance(xlsx, str):
        raise TypeError(f"xlsx must be str path, got {type(xlsx).__name__}")

    xls_path = local_path(*xlsx.split("/"))

    # .xlsm-hez jó az openpyxl engine
    ddf = pd.read_excel(xls_path, sheet_name="Változó info", engine="openpyxl")
    db  = pd.read_excel(xls_path, sheet_name="Adatbázis", engine="openpyxl")
    return ddf, db

def label_map_from_dict(ddf: pd.DataFrame) -> dict[str, str]:
    """
    'Változó' → 'Változó neve' leképezés a dictionary sheetből.
    Ha nincs oszlop, üres map-et ad vissza.
    """
    cols = set(ddf.columns.astype(str))
    if {"Változó", "Változó neve"} <= cols:
        return dict(zip(ddf["Változó"].astype(str), ddf["Változó neve"].astype(str)))
    return {}

def find_pairs(df: pd.DataFrame, suffix: str = "_átlag") -> dict[str, str]:
    """
    Visszaad egy {bázis_oszlop: bazis_atlag_oszlop} dictet, pl.
    {'minőség_index': 'minőség_index_átlag', ...}
    Csak azokat teszi be, amelyek mindkét oszloppal léteznek.
    """
    pairs: dict[str, str] = {}
    cols = set(df.columns.astype(str))
    for c in cols:
        if c.endswith(suffix):
            base = c[: -len(suffix)]
            if base in cols:
                pairs[base] = c
    return pairs