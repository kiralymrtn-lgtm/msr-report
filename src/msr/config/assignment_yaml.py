from __future__ import annotations
from pathlib import Path
import yaml
from ..utils.paths import local_path

def load_assignment_yaml(path: str = "config/assignment.yaml") -> dict:
    """Beolvas egy YAML assignment fájlt a local/ alól."""
    cfg_path = local_path(*path.split("/"))
    if not cfg_path.exists():
        raise FileNotFoundError(f"Assignment YAML nem található: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}