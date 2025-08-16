"""
HTML → PDF konverzió Playwright-tal (headless Chromium).

LÉNYEG:
- a böngésző megnyitja a file://<abszolút út> HTML-t,
- a PDF paramétereit (méret, margó, háttér) átadjuk,
- a CSS @page szabályok érvényesülnek (prefer_css_page_size=True).
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright
from ..utils.paths import local_path, ensure_dir

def html_to_pdf(html_file: Path, pdf_name: Optional[str] = None) -> Path:
    """
    :param html_file: a renderelt HTML abszolút elérési útja
    :param pdf_name: ha nem adod meg, a HTML fájl neve + ".pdf" lesz
    :return: létrejött PDF abszolút elérési út
    """
    if not html_file.exists():
        raise FileNotFoundError(f"Nem találom a HTML fájlt: {html_file}")

    out_dir = local_path("output", "pdf")
    ensure_dir(out_dir)
    if pdf_name is None:
        pdf_name = html_file.stem + ".pdf"
    pdf_path = out_dir / pdf_name

    with sync_playwright() as p:
        browser = p.chromium.launch()     # headless Chromium indítása
        page = browser.new_page()

        # A helyi fájl betöltése file:// URL-lel (különben a böngésző nem tudná olvasni)
        page.goto(html_file.as_uri())

        # ~~~~~ FONTOS ~~~~~
        # prefer_css_page_size=True → az @page size (brand.css) az elsődleges
        # Ha itt width/height/format/landscape paramétereket adnánk meg,
        # azok felülírnák a CSS-t (amit most szándékosan nem teszünk).
        page.pdf(
            path=str(pdf_path),
            print_background=True,      # CSS háttérgrafikák is kerüljenek a PDF-be
            prefer_css_page_size=True,  # NYOMTATÁSI MÉRET a CSS-ben definiált
        )
        browser.close()

    if not pdf_path.exists():
        raise RuntimeError(f"PDF nem jött létre: {pdf_path}")

    return pdf_path
