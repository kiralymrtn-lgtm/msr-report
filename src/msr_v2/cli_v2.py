from pathlib import Path
import pandas as pd
from msr_v2.assign import render_from_yaml

# Projekt gyökér: .../msr-report
ROOT = Path(__file__).resolve().parents[2]

XLSM = ROOT / "local" / "data" / "input" / "Egyedi reportok adatbázis_2024_anonim.xlsm"
YAML = ROOT / "local" / "config" / "assignment_v2.yaml"  # ← 'confic' helyett 'config'

# db = az "Adatbázis" sheet DataFrame-je
db = pd.read_excel(XLSM, sheet_name="Adatbázis", engine="openpyxl")
row_index = db.index[0]  # vagy keresd meg a ResponseId alapján

out_paths = render_from_yaml(
    YAML,
    db=db,
    row_index=row_index,
    partner_id="19272919",
)
print("\n".join(map(str, out_paths)))