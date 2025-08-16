# msr-report

automatizált, html→pdf alapú riportgenerálás.

## fontos szabály
**minden érzékeny vagy nagy fájl a `local/` mappába kerüljön**, mert ez git-ignored.  
példák: excel inputok, képek, logók, hátterek, pdf-ek, pptx-ek, fontok, ideiglenes képgenerált chartok stb.

## mappa-struktúra (kezdeti)
├─ .gitignore # gondoskodik róla, hogy a local/ és a binárisok/office fájlok ne kerüljenek gitbe
├─ README.md
├─ src/ # ide kerül majd a kód
└─ local/ # git-ignored privát munkaterület
├─ assets/
│ ├─ css/
│ ├─ logos/
│ ├─ backgrounds/
│ └─ fonts/
├─ data/
│ └─ input/
└─ output/
├─ html/
├─ pdf/
└─ assets/