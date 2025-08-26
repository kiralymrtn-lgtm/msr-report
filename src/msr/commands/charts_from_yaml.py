from __future__ import annotations
import typer
from rich.console import Console
import pandas as pd

from ..data.loaders import load_workbook
from ..config.assignment_yaml import load_assignment_yaml
from ..charts.assignment import render_pages_from_yaml

console = Console()

def _resolve_row_index(db: pd.DataFrame, partner_id: str, pid_col: str) -> int:
    idx = db.index[db[pid_col].astype(str) == str(partner_id)]
    if len(idx) == 0:
        raise typer.BadParameter(f"Nincs ilyen {pid_col}: {partner_id!r}")
    return int(idx[0])

def charts_from_yaml(
    xlsx_path: str = typer.Option(
        "data/input/Egyedi reportok adatbázis_2024_anonim.xlsm",
        help="Forrás .xlsm (relatív a local/ gyökeréhez).",
    ),
    config_path: str = typer.Option(
        "config/assignment.yaml",
        help="Assignment YAML (relatív a local/ gyökeréhez).",
    ),
    partner_id: str = typer.Option(..., help="Partner azonosító (pl. P01203012)."),
    pid_col: str = typer.Option("ResponseID", help="Azonosító oszlop neve az Adatbázis sheeten."),
) -> None:
    ddf, db = load_workbook(xlsx=xlsx_path)
    row_index = _resolve_row_index(db, partner_id, pid_col)
    cfg = load_assignment_yaml(config_path)
    res = render_pages_from_yaml(db=db, ddf=ddf, row_index=row_index, config=cfg, partner_id=partner_id)

    for page_id, buckets in res.items():
        for kind, paths in buckets.items():
            for p in paths:
                console.print(f"[green]OK[/green] {page_id}/{kind}: {p}")