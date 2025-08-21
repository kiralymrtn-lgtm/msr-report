from pathlib import Path

def resolve_brand_css_paths() -> list[str]:
    """
    Csak a publikus repo-beli brand.css-t keressük (src/templates/assets/css/brand.css).
    Lokális override-ot nem használunk.
    """
    repo_css = Path(__file__).resolve().parents[2] / "templates" / "assets" / "css" / "brand.css"
    return [str(repo_css.resolve())] if repo_css.exists() else []
