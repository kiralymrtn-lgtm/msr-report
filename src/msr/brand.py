"""
brand.py – központi brand beállítások és asset-útvonalak.

MIT TUD:
- egységes helyen tartja a palettát (HEX színek), betűcsalád neveket, lapméretet (ha kell),
- szabványos, "várt" fájlneveket ad a logóra és háttérképre,
- megadja, hová várjuk a brand.css-t (local/assets/css/brand.css),
- barátságosan jelzi, ha egy asset hiányzik (hol keresd / hova másold).

MIÉRT KELL:
- a chartok, html sablonok és egyéb modulok ne külön-külön találgassák a logó/cover útját,
  hanem egy helyről kérjék le (kevesebb hiba, könnyebb refactor).
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .utils.paths import local_path

# ————————————————————————————————————————————————————————————
# 1) paletta + tipó
#    EZEKET KÉSŐBB A CHARTOK IS HASZNÁLHATJÁK
# ————————————————————————————————————————————————————————————

@dataclass(frozen=True)
class BrandPalette:
    primary: str = "#243746"    # fő szín
    secondary: str = "#f0aa00"  # másodlagos
    accent: str = "#438f98"     # kiemelés
    text: str = "#243746"
    muted: str = "#ffd500"
    background: str = "#EEEEEE"

@dataclass(frozen=True)
class BrandTypography:
    heading: str = 'system-ui, -apple-system, "Segoe UI", Arial, sans-serif'
    body: str = 'system-ui, -apple-system, "Segoe UI", Arial, sans-serif'

# ————————————————————————————————————————————————————————————
# 2) assetok helye a local/ alatt
#    (ezek NEM verziózottak, a .gitignore kizárja)
# ————————————————————————————————————————————————————————————

@dataclass(frozen=True)
class BrandAssets:
    css_path: Path          # local/assets/css/brand.css
    logo_path: Optional[Path] = None          # local/assets/logos/logo.png
    cover_background_path: Optional[Path] = None  # local/assets/backgrounds/cover_bg.jpg

    def ensure_css(self) -> None:
        if not self.css_path.exists():
            raise FileNotFoundError(
                f"Hiányzik a brand CSS: {self.css_path}\n"
                f"→ Hozd létre: local/assets/css/brand.css (brand színek, tipó, @page méret)."
            )

    def missing_assets(self) -> Tuple[str, ...]:
        missing = []
        if self.logo_path and not self.logo_path.exists():
            missing.append(f"Logó nem található: {self.logo_path}")
        if self.cover_background_path and not self.cover_background_path.exists():
            missing.append(f"Háttér nem található: {self.cover_background_path}")
        return tuple(missing)

# ————————————————————————————————————————————————————————————
# 3) fő "brand" objektum, amit a CLI és a sablonok használnak
# ————————————————————————————————————————————————————————————

@dataclass(frozen=True)
class BrandTheme:
    palette: BrandPalette
    typography: BrandTypography
    assets: BrandAssets

def get_brand(
    logo_filename: str = "logo.png",
    cover_bg_filename: str = "cover_bg.png",
    css_filename: str = "brand.css",
) -> BrandTheme:
    """
    STANDARD HELYEK:
    - CSS:   local/assets/css/brand.css
    - LOGÓ:  local/assets/logos/logo.png
    - BG:    local/assets/backgrounds/cover_bg.png

    Kényelmes, mert elég a fájlnevet megadni → a local_path összeállítja.
    """
    css = local_path("assets", "css", css_filename)
    logo = local_path("assets", "logos", logo_filename)
    bg   = local_path("assets", "backgrounds", cover_bg_filename)

    assets = BrandAssets(css_path=css, logo_path=logo, cover_background_path=bg)
    palette = BrandPalette()
    typo = BrandTypography()
    return BrandTheme(palette=palette, typography=typo, assets=assets)
