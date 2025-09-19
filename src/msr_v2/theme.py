from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from .config import Style

def cm_to_in(cm: float) -> float:
    return cm / 2.54

def ensure_rubik_font() -> None:
    fam = plt.rcParams.get("font.family")
    if fam == "Rubik" or fam == ["Rubik"]:
        return
    here = Path(__file__).resolve()
    project_root = here.parents[2]  # .../src/msr_v2 -> repo gyökér
    candidates = [
        project_root / "local" / "assets" / "fonts" / "Rubik" / "Rubik-Bold.ttf",
        project_root / "local" / "assets" / "fonts" / "Rubik" / "Rubik-Regular.ttf",
        project_root / "local" / "assets" / "fonts" / "Rubik" / "Rubik-VariableFont_wght.ttf",
        project_root / "templates" / "assets" / "fonts" / "Rubik" / "Rubik-Bold.ttf",
        project_root / "templates" / "assets" / "fonts" / "Rubik" / "Rubik-Regular.ttf",
        project_root / "templates" / "assets" / "fonts" / "Rubik" / "Rubik-VariableFont_wght.ttf",
    ]
    found = False
    for p in candidates:
        try:
            if p.exists():
                fm.fontManager.addfont(str(p))
                found = True
        except Exception:
            pass
    if found:
        plt.rcParams["font.family"] = "Rubik"

def apply_theme(style: Style) -> None:
    ensure_rubik_font()
    pal = style.palette
    plt.rcParams.update({
        "text.color": pal.text,
        "axes.labelcolor": pal.text,
        "axes.titlesize": style.title.size,
        "axes.titleweight": style.title.weight,
        "legend.frameon": style.legend.frameon,
        "legend.fontsize": style.legend.fontsize,
        "figure.dpi": style.size.dpi,
        "savefig.dpi": style.size.dpi,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False,
        "xtick.bottom": False, "ytick.left": False,
        "font.family": "Rubik",
    })