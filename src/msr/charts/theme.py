from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

DEFAULT_DPI = 300

# ─────────────────────────────────────────────────────────
# Brand palette (tükör a brand.css-hez)
# ─────────────────────────────────────────────────────────
DEFAULT_PALETTE: dict[str, str] = {
    "primary":    "#243746",  # brand primary / text
    "secondary":  "#ffd500",  # fő chart szín (bar/radar main)
    "muted":      "#f0aa00",  # összehasonlító sorozat
    "accent":     "#438f98",  # opcionális
    "text":       "#243746",  # szövegszín
    "background": "#EEEEEE",
}

def ensure_rubik_font() -> None:
    """Regisztrálja a Rubik TTF(eke)t Matplotlibhez, ha megtalálja (idempotens)."""
    # Ha már Rubik az aktív család, kilépünk
    fam = plt.rcParams.get("font.family")
    if fam == "Rubik" or fam == ["Rubik"]:
        return

    # Lehetséges helyek (Regular/Variable + BOLD!)
    here = Path(__file__).resolve()
    project_root = here.parents[3]  # .../src/msr/charts -> projekt gyökér
    candidates = [
        # local/ alatt
        project_root / "local" / "assets" / "fonts" / "Rubik" / "Rubik-Bold.ttf",
        project_root / "local" / "assets" / "fonts" / "Rubik" / "Rubik-Regular.ttf",
        project_root / "local" / "assets" / "fonts" / "Rubik" / "Rubik-VariableFont_wght.ttf",
        # templates/ alatt (repo része)
        project_root / "templates" / "assets" / "fonts" / "Rubik" / "Rubik-Bold.ttf",
        project_root / "templates" / "assets" / "fonts" / "Rubik" / "Rubik-Regular.ttf",
        project_root / "templates" / "assets" / "fonts" / "Rubik" / "Rubik-VariableFont_wght.ttf",
    ]

    found_any = False
    for p in candidates:
        try:
            if p.exists():
                fm.fontManager.addfont(str(p))
                found_any = True
        except Exception:
            pass

    # Ha találtunk legalább egy Rubik fájlt, állítsuk be alapértelmezettnek
    if found_any:
        plt.rcParams["font.family"] = "Rubik"
        # opcionálisan: a sans-serif lista elejére is betesszük
        try:
            ss = plt.rcParams.get("font.sans-serif", [])
            if isinstance(ss, str):
                ss = [ss]
            plt.rcParams["font.sans-serif"] = ["Rubik", *[x for x in ss if x != "Rubik"]]
        except Exception:
            pass
    else:
        # Nem találtuk – marad a fallback (DejaVu)
        # (Ha szeretnél, ide tehetsz console logot is.)
        pass

def apply_minimal_theme(*args, **kwargs) -> None:
    """Visszafogott (grid és fölös spines nélkül) + brand színezés és Rubik font."""
    ensure_rubik_font()
    pal = DEFAULT_PALETTE
    plt.rcParams.update({
        "text.color": pal["text"],
        "axes.labelcolor": pal["text"],
        "axes.titleweight": "bold",
        "axes.titlesize": 12,  # ← globális title fontsize
        "xtick.color": pal["text"],
        "ytick.color": pal["text"],
        # keret minimalizálása
        "axes.spines.top": False,
        "axes.spines.right": False,
        # keret minimalizálása
        "axes.grid": False,
        # DPI
        "xtick.bottom": False,
        "ytick.left": False,
        # DPI
        "figure.dpi": DEFAULT_DPI,
        "savefig.dpi": DEFAULT_DPI,
        # legenda keret nélkül
        "legend.frameon": False,
        "legend.fontsize": 8,
    })

def cm_to_in(cm: float) -> float:
    return cm / 2.54