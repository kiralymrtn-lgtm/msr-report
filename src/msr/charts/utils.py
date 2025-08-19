import re
from pathlib import Path
from ..utils.paths import local_path, ensure_dir

def charts_dir() -> Path:
    out = local_path("output", "assets", "charts")
    ensure_dir(out)
    return out

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\-_]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")

def save_figure(fig, filename: str, transparent: bool = False) -> Path:
    out = charts_dir() / filename
    fig.savefig(out, bbox_inches="tight", transparent=transparent)
    return out