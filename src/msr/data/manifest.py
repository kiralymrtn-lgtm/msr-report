
# YAML alapú oldalstruktúra betöltése + nagyon enyhe validáció.

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml  # PyYAML
from ..utils.paths import local_path


def _default_manifest_path() -> Path:
    """Alapértelmezett hely: local/config/report_structure.yaml"""
    return local_path("config", "report_structure.yaml")


def load_structure(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Beolvassa a szerkezetet YAML-ból és visszaad egy dict-et:
      {"pages": [ { "kind": "...", ... }, ... ] }

    - path: ha None, akkor local/config/report_structure.yaml
    - nagyon enyhe validáció: van-e 'pages' lista, és minden elemnek van-e 'kind' (cover/content).
    """
    manifest_path = path or _default_manifest_path()
    if not manifest_path.exists():
        raise FileNotFoundError(f"Nem találom a manifesztet: {manifest_path}")

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    pages = data.get("pages")
    if not isinstance(pages, list):
        raise ValueError("A YAML 'pages' kulcsa kötelező és listának kell lennie.")

    # nagyon alap ellenőrzés és normalizálás:
    normalized: List[Dict[str, Any]] = []
    for i, p in enumerate(pages, start=1):
        if not isinstance(p, dict):
            raise ValueError(f"{i}. oldal: nem dict típus.")
        kind = p.get("kind")
        if kind not in {"cover", "content", "closing"}:
            raise ValueError(f"{i}. oldal: 'kind' kötelező ('cover' vagy 'content' vagy 'closing').")
        # Üres részeket biztosan tegyünk be:
        if kind == "cover":
            p.setdefault("cover", {})
            p["cover"].setdefault("title", {})
        else:
            p.setdefault("content", {})
        normalized.append(p)

    return {"pages": normalized, "path": str(manifest_path)}


def summarize(struct: Dict[str, Any]) -> Tuple[int, int, int]:
    """Visszaadja: (összes, cover, content) darabszám."""
    pages = struct.get("pages", [])
    total = len(pages)
    covers = sum(1 for p in pages if p.get("kind") == "cover")
    contents = total - covers
    return total, covers, contents
