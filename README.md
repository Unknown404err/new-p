# 1000 so'z — 1000 gap

O'zbek tilida so'zlashuvchilar uchun ingliz tili darsligi: **40 dars**, har darsda **1 struktura + 25 so'z**, jami **1000 so'z**.

## Fayllar

| Fayl | Nima |
|---|---|
| `darslik/index.html` | Interaktiv darslik — bitta mustaqil fayl, internetsiz ishlaydi (mundarija, qidiruv, progress). |
| `darslik/1000-soz-1000-gap.pdf` | Telefonda o'qish / chop etish / yuborish uchun PDF nusxa (A4, 189 sahifa, xatcho'plar bilan). |

## Qayta yasash

```bash
cd darslik
python3 build.py        # data/*.json -> index.html
python3 make_pdf.py     # data/*.json -> 1000-soz-1000-gap.pdf
```

Manba ma'lumotlar `darslik/data/` ichida: `front.json` (kirish boblar va ibora banki), `blocks.json` (8 blok),
`lessons_01.json … lessons_08.json` (40 dars), `style.css`, `app.js`.

`build.py` tekshiradi: 40 dars, har birida 25 so'z, jami 1000 ta noyob so'z, bloklar darslarni to'liq qamrashi.
PDF yasash uchun `reportlab` kerak (`pip install --break-system-packages reportlab`).
