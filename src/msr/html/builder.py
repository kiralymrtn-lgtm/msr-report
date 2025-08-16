"""
HTML renderelő modul Jinja2-vel.

GONDOLAT:
- "prezentációs logika" a HTML sablonban (templates/html),
- "adat" a Pythonban (context),
- "összefésülés" itt történik (tpl.render).
- a létrejött HTML a local/output/html/ alá kerül (git-ignored).
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..utils.paths import local_path, ensure_dir

def _env() -> Environment:
    """
    Jinja2 környezet felépítése.
    - FileSystemLoader: a sablonok könyvtárát adjuk meg (repo/src/templates/html).
    - autoescape: HTML/XML esetén automatikus escaping (XSS és társai ellen).
    """
    # ez a fájl: src/msr/html/builder.py → .../src/templates/html
    templates_dir = Path(__file__).resolve().parents[2] / "templates" / "html"
    loader = FileSystemLoader(str(templates_dir))
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,   # szépen formázott kimenet (levágja az üres whitespace-t blokkok előtt)
        lstrip_blocks=True,
    )
    return env

def render_to_html_file(
    template_name: str,
    context: Dict[str, Any],
    output_filename: str = "report.html",
) -> Path:
    """
    Sablon (template_name) + context (adat) → HTML szöveg → fájlba írjuk.
    - hol? local/output/html/  (nem kerül gitbe)
    - mit ad vissza? a létrehozott HTML abszolút elérési útját (Path)
    """
    env = _env()
    tpl = env.get_template(template_name)   # pl. "base.html.j2"

    out_dir = local_path("output", "html")
    ensure_dir(out_dir)
    out_path = out_dir / output_filename

    html = tpl.render(**context)            # itt történik a Jinja kifejezések és ciklusok kiértékelése
    out_path.write_text(html, encoding="utf-8")
    return out_path
