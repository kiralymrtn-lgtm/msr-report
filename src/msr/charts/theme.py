from matplotlib import rcParams

DEFAULT_DPI = 300

def apply_minimal_theme():
    """Minimális, nyomtatásbarát beállítások – színt nem állítunk."""
    rcParams.update({
        "figure.dpi": DEFAULT_DPI,
        "savefig.dpi": DEFAULT_DPI,
        "axes.grid": True,
        "grid.linestyle": "-",
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    })

def cm_to_in(cm: float) -> float:
    return cm / 2.54