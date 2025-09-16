from pathlib import Path
import shutil
import argparse
import pandas as pd
from msr_v2.assign import render_from_yaml

# Projekt gyökér: .../msr-report
ROOT = Path(__file__).resolve().parents[2]

XLSM = ROOT / "local" / "data" / "input" / "Egyedi reportok adatbázis_2024_anonim.xlsm"
YAML = ROOT / "local" / "config" / "assignment_v2.yaml"

# db = az "Adatbázis" sheet DataFrame-je
parser = argparse.ArgumentParser(description="MSR v2 riport generálás")
parser.add_argument("--limit", type=int, default=1, help="Az első N ResponseId feldolgozása (alapértelmezés: 1)")
args = parser.parse_args()

db = pd.read_excel(XLSM, sheet_name="Adatbázis", engine="openpyxl")

# ResponseId oszlopból vegyük az első N értéket
if "ResponseID" not in db.columns:
    raise KeyError("Az Excelben nem található 'ResponseId' oszlop.")

response_ids = (
    db["ResponseID"].dropna().astype(str).head(args.limit).tolist()
)

all_moved = []
for rid in response_ids:
    # Keressük meg a hozzá tartozó sor indexét
    matches = db.index[db["ResponseID"].astype(str) == rid].tolist()
    if not matches:
        # Ha valamiért nincs találat, lépjünk tovább
        continue
    row_index = matches[0]

    out_paths = render_from_yaml(
        YAML,
        db=db,
        row_index=row_index,
        partner_id=rid,
    )

    # Képi elemek áthelyezése partner-specifikus mappába: local/output/assets/<partner_id>/
    partner_assets_dir = ROOT / "local" / "output" / "assets" / rid
    partner_assets_dir.mkdir(parents=True, exist_ok=True)

    moved_paths = []
    for p in out_paths:
        p = Path(p)
        dest = partner_assets_dir / p.name
        # Ha a célfájl már létezik, felülírjuk
        if dest.exists():
            dest.unlink()
        shutil.move(str(p), str(dest))
        moved_paths.append(dest)

    all_moved.extend(moved_paths)

# Írjuk ki az összes áthelyezett fájlt
print("\n".join(map(str, all_moved)))