# msr-report

Automatizált, **HTML → PDF** alapú riportgenerálás Jinja2 + Playwright segítségével.

## Gyors indulás
```bash
# telepítés fejlesztői módban
pip install -e .
```

# alap mappák létrehozása (git-ignored local/)
```bash
msr doctor
```

# parancsok listája
```bash
msr --help
```

## fontos szabály
**minden érzékeny vagy nagy fájl a `local/` mappába kerüljön**, mert ez git-ignored.  
példák: excel inputok, képek, logók, hátterek, pdf-ek, pptx-ek, fontok, ideiglenes képgenerált chartok stb.

## mappa-struktúra
├─ .gitignore
├─ pyproject.toml
├─ src/
│  ├─ msr/
│  │  ├─ cli.py                 # Typer CLI (a 'msr' parancs)
│  │  ├─ brand.py               # brand asset segédek
│  │  ├─ html/                  # HTML render segédek
│  │  ├─ pdf/                   # HTML→PDF (Playwright)
│  │  ├─ data/
│  │  │  └─ manifest.py         # YAML betöltés/ellenőrzés
│  │  └─ commands/
│  │     ├─ rendering.py        # render parancsok (cover/content/thanks/structure)
│  │     ├─ charts.py           # chart generálás (bar/column/radar)
│  │     └─ utils.py            # közös segédek (pl. brand.css feloldása)
│  └─ templates/
│     ├─ base.html.j2           # fő HTML sablon (Jinja2)
│     └─ assets/
│        ├─ css/
│        │  └─ brand.css        # KANONIKUS brand CSS (publikus, verziózott)
│        └─ fonts/
│           └─ Rubik/           # Rubik fontfájlok (woff2/ttf)
└─ local/                        # git-ignored privát munkaterület
   ├─ assets/
   │  ├─ logos/
   │  │  ├─ logo.png            # fő logó (content jobb-felső sarok, cover logósáv)
   │  │  └─ logo_general.png    # záró (closing) slide logója (ha van)
   │  └─ backgrounds/
   │     ├─ cover_bg.png        # cover/closing háttér (felső réteg)
   │     └─ cover_bg_bottom.png # cover alsó réteg (opcionális)
   ├─ config/
   │  └─ report_structure.yaml  # a teljes riport szerkezete (YAML)
   ├─ data/
   │  ├─ input/                 # nyers inputok (pl. Excel)
   │  └─ content/
   │     └─ thanks.html         # köszönetnyilvánítás tartalma (HTML)
   └─ output/
      ├─ html/                  # generált HTML-ek
      ├─ pdf/                   # generált PDF-ek
      └─ assets/
         └─ charts/             # generált chart képek

## Brand / CSS
- A kanonikus CSS a repo-ban van: src/templates/assets/css/brand.css.
- A logók/hátterek továbbra is a local/assets/… alatt vannak, hogy ügyfél-specifikusak maradjanak

## Oldaltípusok és sorszámozás
Három típus támogatott:
- cover – címdia (két rétegű háttér támogatás, nem jelenít oldalszámot, de beleszámít).
- content – normál tartalmi dia (bal-felső sáv, jobb-felső logó, megjeleníti az oldalszámot).
- closing – záró dia (cover felső háttérrel, külön logóval; nem jelenít oldalszámot).

Oldalszám: a render-structure parancs a YAML-ből dolgozik.
Csak a content oldalakon látszik a szám, de minden slide beleszámít (cover/closing is).

## page_config példa
```bash
page_config:
  enabled: true   # mutassuk a számot a content oldalakon
  start: 1        # kezdő sorszám (pl. cover = 1, utána az első content = 2)
```

## YAML (local/config/report_structure.yaml) – példa
```bash
page_config:
  enabled: true
  start: 1

pages:
  - kind: cover
    cover:
      title:
        line1: "VÁLLALKOZÓI"
        line2: "egyedi riport"
        year:  "2025"

  - kind: content
    content:
      layout: split
      header: { height: 20mm, width: "66%" }
      title_main: "VÁLLALATI"
      title_sub:  "teljesítmény az elmúlt 12 hónapban"
      image_path: assets/charts/group_means.png   # ha 'assets/'-sel kezdődik → local/output/assets/... alatt keresi
      explain_title: "Összefoglaló"
      explain_paragraph: "Rövid magyarázat…"

  - kind: content
    content:
      layout: text
      title_main: "KÖSZÖNETNYILVÁNÍTÁS"
      text:
        file: data/content/thanks.html
        max_width: 90%
        font_size: 10pt
        line_height: 1.6
        align: justify

  - kind: closing
    closing:
      text_html: |
        <p>Köszönjük a figyelmet és a közreműködést!</p>
        <p>Kapcsolat: …</p>
```

## Köszönet (thanks.html) – hasznos osztályok
A local/data/content/thanks.html tetszőleges HTML lehet.
Stílusok a brand.css-ben:
- tnr-italic → Times New Roman dőlt
- rubik-bold → Rubik félkövér
- linkek: normál <a href="…">szöveg</a> (aláhúzott, brand secondary szín)

## Parancsok (CLI)
```bash
msr doctor                         # local/ struktúra létrehozása/ellenőrzése
msr pages-validate                 # YAML listázása (sorszám, típus, címek)
msr render-structure               # TELJES riport render (YAML alapján)
msr pdf-from-html report_structure.html   # legenerált HTML → PDF

# demók
msr render-cover-demo              # csak cover
msr render-content-demo            # csak content(ek)
msr render-cover-and-content-demo  # cover + 2 content
msr render-thanks                  # külön a köszönet-oldal

# chart demó (Excel → chart PNG-k a local/output/assets/charts/ alá)
msr charts-demo --xlsx "data/input/demo eredmények.xlsx" --partner-id "P01203012"
```

## Tippek
- A content oldalak törzse két layoutot tud:
- text: egy nagy szövegdoboz (állítható sorhossz/igazítás/betűméret)
- split: bal hasáb (kép/chart/tábla), jobb hasáb (címes magyarázat)
- A chartok a local/output/assets/charts/ mappába generálódnak, és a YAML-ban kényelmesen hivatkozhatók assets/charts/... előtaggal.
- A brand színek/tipó a src/templates/assets/css/brand.css-ben szabhatók testre (publikus, verziózott).