from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class LegendCfg:
    show: bool = True
    below: bool = True
    pad: float = 0.10
    ncol: int = 2
    loc: str = "lower center"
    frameon: bool = False
    fontsize: float = 8.0

@dataclass
class TitleCfg:
    size: float = 12.0
    weight: str = "bold"
    pad: float = 8.0
    wrap: Optional[int] = None  # None → nem tördel; pl. 26 → wrap szélesség

@dataclass
class LabelCfg:
    x_fontsize: float = 8.0
    y_fontsize: float = 8.0
    value_fmt: str = "{val:.1f}"          # fő értékek (bar/column belsejében)
    overlay_value_fmt: str = "{val:.1f}"  # overlay vonal felirata
    value_color: Optional[str] = None     # None → pal.text
    wrap: int | None = None

@dataclass
class Palette:
    primary: str = "#243746"
    secondary: str = "#ffd500"
    muted: str = "#f0aa00"
    accent: str = "#438f98"
    text: str = "#243746"
    background: str = "#EEEEEE"

@dataclass
class SizeCfg:
    cm_w: float = 10.0
    cm_h: float = 10.0
    dpi: int = 300

@dataclass
class Style:
    palette: Palette = field(default_factory=Palette)
    title: TitleCfg = field(default_factory=TitleCfg)
    legend: LegendCfg = field(default_factory=LegendCfg)
    labels: LabelCfg = field(default_factory=LabelCfg)
    size: SizeCfg = field(default_factory=SizeCfg)

    def merge_overrides(self, overrides: Optional[Dict[str, Any]] = None) -> "Style":
        if not overrides:
            return self
        import copy
        s = copy.deepcopy(self)
        for section, vals in overrides.items():
            if hasattr(s, section) and isinstance(vals, dict):
                obj = getattr(s, section)
                for k, v in vals.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
        return s