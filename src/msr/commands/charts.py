import typer
from rich.console import Console
console = Console()

import pandas as pd
from ..utils.paths import local_path
from ..charts.bar import save_column
from ..charts.radar import save_radar

def charts_demo(
    xlsx: str = typer.Option(
        "data/input/MCC demo eredmények.xlsx",
        help="Excel helye (relatív a local/ gyökeréhez)",
    ),
    partner_id: str | None = typer.Option(
        None,
        help="Kiemelendő PartnerId (STRING). Ha nincs megadva vagy nem található, az első sort használjuk.",
    ),
) -> None:
    """
    Példa: csoportátlag (column) + kiválasztott partner vs. csoport (radar).
    Kimenet: local/output/assets/charts/*.png
    """
    # 1) adat betöltése
    xls_path = local_path(*xlsx.split("/"))
    if not xls_path.exists():
        console.print(f"[red]Nem találom az Excelt:[/red] {xls_path}")
        raise typer.Exit(code=1)

    df = pd.read_excel(xls_path, sheet_name=0)
    # várjuk: PartnerId + Kérdés1..KérdésN (számok)
    metric_cols = [c for c in df.columns if c.lower().startswith("kérdés")]
    if not metric_cols:
        console.print("[red]Nem találtam 'Kérdés*' oszlopokat az Excelben.[/red]")
        raise typer.Exit(code=1)

    # 2) csoportátlag (column)
    means = df[metric_cols].mean().values.tolist()
    labels = metric_cols
    col_path = (
        save_column(
            values=means, labels=labels,
            title="Csoportátlag kérdésenként",
            y_range=(1, 5),  # tipikus 1–5 Likert
            annotate = True,
            filename = "group_means.png",
        )
    )
    console.print(f"[green]OK[/green] column: {col_path}")

    # 3) kiválasztott partner vs. csoport (radar)
    pid_col = "PartnerId"
    # PartnerId-k tipikusan alfanumerikusak (pl. "P01203012"). Kezeljük STRING-ként.
    if partner_id:
        row = df.loc[df[pid_col].astype(str) == str(partner_id)]
    else:
        row = pd.DataFrame()  # üres, hogy a fallback ágat aktiváljuk

    if row.empty:
        console.print(
            f"[yellow]Figyelem:[/yellow] nincs ilyen PartnerId: {partner_id!r}, az első sort használom."
        )
        row = df.iloc[[0]]

    pid_for_title = str(row[pid_col].iloc[0])

    series_main = row[metric_cols].iloc[0].tolist()
    series_comp = df[metric_cols].mean().tolist()
    rad_path = (
        save_radar(
            labels=labels,
            series_main=series_main,
            series_comp=series_comp,
            title=f"Partner {pid_for_title} vs. csoport",
            r_range=(1, 5),
            filename="partner_vs_group_radar.png",
        )
    )
    console.print(f"[green]OK[/green] radar: {rad_path}")

    console.print("[bold green]Kész![/bold green] A képek a local/output/assets/charts alatt vannak.")
    console.print("Használd a YAML-ben: output/assets/charts/group_means.png  (röviden: írhatsz assets/charts/…-t is; ilyenkor automatikusan az output/ alá mutat).")
