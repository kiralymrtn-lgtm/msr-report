import typer
from rich.console import Console
console = Console()

import pandas as pd
from ..utils.paths import local_path
from ..charts.bar import save_column, save_bar
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
    metric_cols = [c for c in df.columns if c.lower().startswith("kérdés")]
    if not metric_cols:
        console.print("[red]Nem találtam 'Kérdés*' oszlopokat az Excelben.[/red]")
        raise typer.Exit(code=1)

    # Partner kiválasztás
    pid_col = "PartnerId"
    row = df.loc[df[pid_col].astype(str) == str(partner_id)] if partner_id else pd.DataFrame()
    if row.empty:
        console.print(f"[yellow]Figyelem:[/yellow] nincs ilyen PartnerId: {partner_id!r}, az első sort használom.")
        row = df.iloc[[0]]
    pid_for_title = str(row[pid_col].iloc[0])


    # Sorozatok
    means = df[metric_cols].mean().values.tolist()  # csoportátlag
    series_main = row[metric_cols].iloc[0].tolist()  # partner
    series_comp = df[metric_cols].mean().tolist()  # csoport (radarhoz)


    # 1) COLUMN: csoportátlag + partner vízszintes vonalak, legend alul
    col_path = save_column(
        values=means,
        labels=metric_cols,
        title="Csoportátlag kérdésenként",
        y_range=(1, 5.5),
        annotate=True,
        filename="group_means.png",
        show_x_labels=True, x_label_rotation=0, x_label_fontsize=8.5,
        overlay_values=series_main, overlay_line_width=2.4,
        main_label="Csoportátlag", overlay_label=f"Partner {pid_for_title}",
        legend_below=True, legend_pad=0.14, legend_ncol=2,
    )
    console.print(f"[green]OK[/green] column: {col_path}")


    # 2) BAR: csoportátlag + partner függőleges vonalak, legend alul
    bar_path = save_bar(
        values=series_comp,                 # Csoport → rudak
        labels=metric_cols,
        title=f"Partner {pid_for_title} vs. csoport (bar)",
        x_range=(1, 5),
        annotate=True,                      # rudak + overlay értékcímkék
        filename="partner_vs_group_bar.png",
        show_y_labels=True, y_label_fontsize=8.5,
        overlay_values=series_main,         # Partner → függőleges vonal
        overlay_line_width=2.4,
        main_label="Csoport",
        overlay_label=f"Partner {pid_for_title}",
        legend_below=True, legend_pad=0.14, legend_ncol=2,
    )
    console.print(f"[green]OK[/green] bar: {bar_path}")


    # 3) RADAR: partner vs csoport, legend alul
    rad_path = save_radar(
        labels=metric_cols,
        series_main=series_main,  # Partner
        series_comp=series_comp,  # Csoport
        title=f"Partner {pid_for_title} vs. csoport",
        r_range=(1, 5),
        filename="partner_vs_group_radar.png",
        legend_below=True, legend_pad=0.14, legend_ncol=2,
    )
    console.print(f"[green]OK[/green] radar: {rad_path}")

    console.print("[bold green]Kész![/bold green] A képek a local/output/assets/charts alatt vannak.")
    console.print("Használd a YAML-ben: output/assets/charts/group_means.png  …")