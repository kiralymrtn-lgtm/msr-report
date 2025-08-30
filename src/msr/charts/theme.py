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
    """Regisztrálja a Rubik TTF-et Matplotlibhez, ha megtalálja (idempotens)."""
    try:
        fam = plt.rcParams.get("font.family")
        if fam == "Rubik" or fam == ["Rubik"]:
            return
    except Exception:
        pass

    candidates = [
        Path.cwd() / "local" / "assets" / "fonts" / "Rubik" / "Rubik-VariableFont_wght.ttf",
        Path.cwd() / "local" / "assets" / "fonts" / "Rubik" / "Rubik-Regular.ttf",
        Path(__file__).resolve().parents[2] / "templates" / "assets" / "fonts" / "Rubik" / "Rubik-VariableFont_wght.ttf",
    ]
    for p in candidates:
        try:
            if p.exists():
                fm.fontManager.addfont(str(p))
                plt.rcParams["font.family"] = "Rubik"
                break
        except Exception:
            pass

def apply_minimal_theme(*args, **kwargs) -> None:
    """Visszafogott (grid és fölös spines nélkül) + brand színezés és Rubik font."""
    ensure_rubik_font()
    pal = DEFAULT_PALETTE
    plt.rcParams.update({
        "text.color": pal["text"],
        "axes.labelcolor": pal["text"],
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