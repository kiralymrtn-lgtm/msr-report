"""
Egyetlen forráshely az útvonal-logikának. Ha később kell valami extra (pl. platformfüggő mentés), ide kerül.
Útvonal segédek:
- repo_root(): a repó gyökere
- local_root(): a ./local mappa a repó gyökerében (vagy MSR_LOCAL_ROOT környezeti változóval felülírható)
- ensure_dir(), local_path(): kényelmi függvények
"""
from __future__ import annotations
from pathlib import Path
import os

def repo_root() -> Path:
    # a repo gyökerét számolja ki relatív módon. előnye hogy bárhonnan futtatod, mindig a valódi gyökeret kapod
    # ez a fájl: src/msr/utils/paths.py → gyökér 3 szinttel feljebb
    return Path(__file__).resolve().parents[3]

def local_root() -> Path:
    """
    alapértelmezett: <repo>/local
    ha van MSR_LOCAL_ROOT env változó, azt használjuk (pl. ha valaki máshova szeretné).
    """
    env = os.getenv("MSR_LOCAL_ROOT")
    return (Path(env).expanduser().resolve() if env else repo_root() / "local")

def ensure_dir(path: Path) -> Path:
    #„Létezik? — akkor oké. Nem? — hozd létre rekurzívan.” Visszaadja a Path-ot, így kényelmes láncolni/logolni.
    path.mkdir(parents=True, exist_ok=True)
    return path

def local_path(*segments: str) -> Path:
    #Rövidítő: local_path("output","pdf") → <repo>/local/output/pdf (vagy az override-olt útvonal).
    return local_root().joinpath(*segments)
