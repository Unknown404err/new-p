#!/usr/bin/env python3
"""
1000 so'z — 1000 gap
Darslik generatori: data/*.json -> index.html (bitta mustaqil fayl)

Ishlatish:
    python3 build.py            # index.html yaratadi
    python3 build.py --check    # faqat tekshiruv
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "index.html"


# --------------------------------------------------------------------------
# yuklash
# --------------------------------------------------------------------------

def load_json(name: str) -> dict:
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def load_lessons() -> list[dict]:
    lessons: list[dict] = []
    for path in sorted(DATA.glob("lessons_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for lesson in data["lessons"]:
            lessons.append(lesson)
    lessons.sort(key=lambda l: l["n"])
    return lessons


def esc(text: str) -> str:
    return html.escape(str(text), quote=False)


# --------------------------------------------------------------------------
# tekshiruv
# --------------------------------------------------------------------------

def validate(lessons: list[dict], blocks: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, int] = {}
    total = 0

    if len(lessons) != 40:
        errors.append(f"Darslar soni 40 emas: {len(lessons)}")

    nums = [l["n"] for l in lessons]
    if nums != list(range(1, len(lessons) + 1)):
        errors.append(f"Dars raqamlari uzluksiz emas: {nums[:5]}...")

    for lesson in lessons:
        n = lesson["n"]
        words = lesson.get("words", [])
        total += len(words)
        if len(words) != 25:
            errors.append(f"#{n:02d}: {len(words)} so'z (25 bo'lishi kerak)")
        for row in words:
            if len(row) != 3:
                errors.append(f"#{n:02d}: so'z qatorida 3 ustun yo'q: {row}")
                continue
            key = row[0].strip().lower()
            if not key:
                errors.append(f"#{n:02d}: bo'sh so'z")
            if key in seen:
                errors.append(f"#{n:02d}: takror so'z '{row[0]}' (avval #{seen[key]:02d})")
            else:
                seen[key] = n
        for field in ("frame", "triad", "examples", "exercises"):
            if field not in lesson:
                errors.append(f"#{n:02d}: '{field}' maydoni yo'q")

    if total != 1000:
        errors.append(f"Jami so'z 1000 emas: {total}")

    covered = set()
    for block in blocks:
        covered.update(range(block["from"], block["to"] + 1))
    if covered != set(nums):
        errors.append("Bloklar darslarni to'liq qamramagan")

    print(f"  darslar: {len(lessons)}   so'zlar: {total}   noyob so'z: {len(seen)}")
    if total and len(seen) != total:
        print(f"  ! {total - len(seen)} ta takroriy so'z")
    return errors


# --------------------------------------------------------------------------
# HTML bo'laklari
# --------------------------------------------------------------------------

def render_triad(triad: dict) -> str:
    parts = ['<div class="triad">']
    for key, title in (("aff", "Tasdiq"), ("neg", "Inkor"), ("q", "Savol")):
        items = triad.get(key, [])
        lis = "".join(f"<li>{esc(x)}</li>" for x in items)
        parts.append(f'<div class="{key}"><h5>{title}</h5><ul>{lis}</ul></div>')
    parts.append("</div>")
    short = triad.get("short") or []
    if short:
        parts.append('<div class="triad"><div class="short" style="grid-column:1/-1"><h5>Qisqa javoblar</h5><p>'
                     + " &nbsp;·&nbsp; ".join(esc(x) for x in short) + "</p></div></div>")
    return "".join(parts)


def render_words(words: list[list[str]]) -> str:
    rows = []
    for en, uz, col in words:
        rows.append(
            "<tr>"
            f'<td class="en">{esc(en)}</td>'
            f'<td class="uz">{esc(uz)}</td>'
            f'<td class="col">{esc(col)}</td>'
            "</tr>"
        )
    return (
        '<table class="words"><thead><tr><th>So\'z</th><th>Tarjima</th><th>Tayyor birikma</th></tr></thead>'
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def highlight(text: str, words: list[list[str]]) -> str:
    """Namuna gap ichidagi dars so'zlarini yengil ajratib ko'rsatadi."""
    out = esc(text)
    for row in words:
        word = row[0]
        base = word.split(" (")[0].strip()
        if len(base) < 3 or " " in base and base.lower() not in text.lower():
            continue
        pattern = re.compile(r"(?<![\w-])(" + re.escape(base) + r"(?:s|es|ed|d|ing|'s)?)(?![\w-])", re.IGNORECASE)
        out = pattern.sub(r"<em>\1</em>", out, count=2)
    return out


def render_examples(examples: list[dict], words: list[list[str]]) -> str:
    items = []
    for ex in examples:
        items.append(
            "<li>"
            f'<span class="en">{highlight(ex["en"], words)}</span>'
            f'<span class="uz">{esc(ex["uz"])}</span>'
            "</li>"
        )
    return '<ol class="ex">' + "".join(items) + "</ol>"


def render_dialog(dialog: dict) -> str:
    if not dialog:
        return ""
    lines = []
    for i, line in enumerate(dialog["lines"]):
        who = line.get("who", "A")
        cls = "line b" if who.upper() == "B" else "line"
        lines.append(
            f'<div class="{cls}"><div class="who">{esc(who)}</div>'
            f'<div class="txt">{esc(line["en"])}<small>{esc(line["uz"])}</small></div></div>'
        )
    return (
        f'<h4>{esc(dialog.get("title", "Mini dialog"))}</h4>'
        '<div class="card tight"><div class="dlg">' + "".join(lines) + "</div></div>"
    )


def render_street(street: dict) -> str:
    if not street:
        return ""
    lis = []
    for item in street["items"]:
        lis.append(f'<li>{esc(item["en"])}<small>{esc(item["uz"])}</small></li>')
    note = f'<p>{esc(street["note"])}</p>' if street.get("note") else ""
    title = esc(street.get("title") or "Ko'cha varianti")
    return (
        '<div class="street">'
        f"<h5>{title}</h5>"
        "<ul>" + "".join(lis) + "</ul>" + note + "</div>"
    )


def render_exercises(ex: dict) -> str:
    blocks = []

    sub = ex.get("substitution") or []
    if sub:
        items = "".join(
            f'<li>{esc(x["prompt"])}</li>' for x in sub
        )
        ans = "".join(f'<li>{esc(x["answer"])}</li>' for x in sub)
        blocks.append(
            '<div class="ex-block"><h6>1. Almashtirish <span>— bo\'sh joyni ko\'rsatilgan so\'z bilan to\'ldiring</span></h6>'
            f"<ol>{items}</ol>"
            f'<details class="ans"><summary>Javoblar</summary><ol>{ans}</ol></details></div>'
        )

    tr = ex.get("translate") or []
    if tr:
        items = "".join(f'<li>{esc(x["uz"])}</li>' for x in tr)
        ans = "".join(f'<li>{esc(x["en"])}</li>' for x in tr)
        blocks.append(
            '<div class="ex-block"><h6>2. Tarjima <span>— o\'zbekchadan inglizchaga</span></h6>'
            f"<ol>{items}</ol>"
            f'<details class="ans"><summary>Javoblar</summary><ol>{ans}</ol></details></div>'
        )

    fix = ex.get("fix") or []
    if fix:
        items = "".join(f'<li class="wrong">{esc(x["wrong"])}</li>' for x in fix)
        ans = "".join(
            f'<li>{esc(x["right"])} <span class="why">— {esc(x["why"])}</span></li>' for x in fix
        )
        blocks.append(
            '<div class="ex-block"><h6>3. Xato topish <span>— gapda xato bor, tuzating</span></h6>'
            f"<ol>{items}</ol>"
            f'<details class="ans"><summary>Javoblar</summary><ol>{ans}</ol></details></div>'
        )

    return '<div class="card"><h4>Mashqlar</h4>' + "".join(blocks) + "</div>"


def render_lesson(lesson: dict) -> str:
    n = lesson["n"]
    frame = lesson["frame"]
    words = lesson["words"]

    table_rows = ""
    if frame.get("table"):
        table_rows = (
            '<table class="grid"><thead><tr><th>Shakl</th><th>Ma\'nosi</th></tr></thead><tbody>'
            + "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td></tr>" for a, b in frame["table"])
            + "</tbody></table>"
        )

    return f"""
<section class="doc lesson" id="d{n:02d}" data-n="{n}">
  <div class="lesson-head">
    <div class="lesson-num">{n:02d}</div>
    <div class="h">
      <div class="meta-row">
        <span class="chip accent">Struktura {n}</span>
        <span class="chip">{esc(lesson.get("theme", ""))}</span>
        <label class="donewrap"><input type="checkbox" data-done="{n}"> bajarildi</label>
      </div>
      <h3>{esc(lesson["title"])}</h3>
      <p class="goal">{esc(lesson.get("goal", ""))}</p>
    </div>
  </div>

  <div class="card">
    <h4>Bugungi struktura · {esc(frame["name"])}</h4>
    <formula>{esc(frame["formula"])}</formula>
    <p>{frame["explain"]}</p>
    {table_rows}
  </div>

  <h4>Bitta struktura — uch shakl</h4>
  {render_triad(lesson["triad"])}

  <h4>Bugungi 25 so'z</h4>
  <div class="card tight">{render_words(words)}</div>

  <h4>Namuna gaplar</h4>
  {render_examples(lesson["examples"], words)}

  {render_street(lesson.get("street"))}
  {render_dialog(lesson.get("dialog"))}
  {render_exercises(lesson["exercises"])}

  <div class="tip"><div>{lesson.get("tip", "")}</div></div>
</section>"""


# --------------------------------------------------------------------------
# sahifa
# --------------------------------------------------------------------------

def render_sidebar(front: dict, lessons: list[dict], blocks: list[dict]) -> str:
    nav = ['<div class="grp"><h4>1-qism · Asoslar</h4>']
    for ch in front["chapters"]:
        nav.append(f'<a href="#{ch["id"]}"><span class="num">·</span>{esc(ch["title"])}</a>')
    nav.append("</div>")

    for block in blocks:
        label = block.get("title", "")
        nav.append(f'<div class="grp"><h4>{block["from"]}–{block["to"]} · {esc(label)}</h4>')
        for lesson in lessons:
            if block["from"] <= lesson["n"] <= block["to"]:
                nav.append(
                    f'<a href="#d{lesson["n"]:02d}"><span class="num">{lesson["n"]:02d}</span>'
                    f'{esc(lesson["title"].split(":")[0])}</a>'
                )
        nav.append("</div>")

    nav.append('<div class="grp"><h4>3-qism · Ko\'cha iboralari</h4>'
               '<a href="#bank"><span class="num">·</span>15 ibora oilasi</a></div>')
    nav.append('<div class="grp"><h4>4-qism · Ilova</h4>'
               '<a href="#frames"><span class="num">·</span>40 struktura xulosasi</a>'
               '<a href="#index"><span class="num">·</span>1000 so\'z indeksi</a></div>')

    return f"""
<button class="menu-btn" id="menuBtn" aria-label="Menyu">☰</button>
<aside class="sidebar" id="sidebar">
  <a class="brand" href="#top">
    <b>1000 so'z — 1000 gap</b>
    <span>Ingliz tili darsligi</span>
  </a>
  <div class="pbar"><i id="pbarFill"></i></div>
  <div class="pmeta"><span id="pbarText">0 / {len(lessons)} dars</span><span>40 kun</span></div>
  <input class="search" id="search" type="search" placeholder="So'z yoki dars qidirish…">
  <nav class="nav" id="nav">{''.join(nav)}</nav>
</aside>"""


def render_cover(front: dict, lessons: list[dict], total_words: int) -> str:
    return f"""
<header class="cover" id="top">
  <div class="kicker">O'zbek tilida so'zlashuvchilar uchun</div>
  <h1>1000 so'z —<br>1000 gap</h1>
  <p class="lede">{esc(front["subtitle"])}. Har kuni 25 so'z va bitta struktura: 40 kunda
  so'z boyligi ham, gap qurish ko'nikmasi ham birga o'sadi.</p>
  <div class="facts">
    <div class="fact"><b>{total_words}</b>asosiy so'z</div>
    <div class="fact"><b>{len(lessons)}</b>dars · struktura</div>
    <div class="fact"><b>{len(front["bank"])}</b>ibora oilasi</div>
    <div class="fact"><b>3</b>xil mashq har darsda</div>
  </div>
  <div class="toc-grid">
    <a href="#q1"><b>1-qism · Asoslar</b><span>Gap qurish mexanikasi, olmoshlar, so'zlashuv qatlami</span></a>
    <a href="#d01"><b>2-qism · 40 dars</b><span>25 so'z + 1 struktura + namuna gaplar + mashqlar</span></a>
    <a href="#bank"><b>3-qism · Ko'cha iboralari</b><span>15 oila: ruxsat, tushunish, kelishuv, baholash</span></a>
    <a href="#index"><b>4-qism · Ilova</b><span>Strukturalar xulosasi va 1000 so'z indeksi</span></a>
  </div>
</header>"""


def render_bank(bank: list[dict]) -> str:
    fams = []
    for i, fam in enumerate(bank, 1):
        rows = "".join(
            f"<li><b>{esc(en)}</b><span>{esc(uz)}</span></li>" for en, uz in fam["rows"]
        )
        note = f'<p class="note">{esc(fam["note"])}</p>' if fam.get("note") else ""
        fams.append(
            f'<div class="fam"><h4>Oila {i:02d} · {esc(fam["title"])}</h4>'
            f'<p class="use">{esc(fam["use"])}</p>'
            f'<ul class="rows">{rows}</ul>{note}</div>'
        )
    return (
        '<section class="doc" id="bank">'
        "<h3>Ko'cha iboralari banki</h3>"
        "<p class='lead'>Quyidagi 15 oila — ikki varaqadagi iboralarning <b>tuzilish uslubi</b> asosida qayta "
        "guruhlangan to'plam. Har bir oilada bitta vazifa (ruxsat so'rash, tushunishni tekshirish, kelishuv) "
        "va uning turli darajadagi shakllari beriladi: norasmiydan xushmuomalagacha.</p>"
        + "".join(fams)
        + "</section>"
    )


def render_frames(lessons: list[dict]) -> str:
    rows = "".join(
        f'<tr><td>{l["n"]:02d}</td><td><a href="#d{l["n"]:02d}">{esc(l["frame"]["name"])}</a></td>'
        f'<td><code>{esc(l["frame"]["formula"].splitlines()[0])}</code></td>'
        f'<td>{esc(l["theme"])}</td></tr>'
        for l in lessons
    )
    return (
        '<section class="doc" id="frames">'
        "<h3>40 struktura — bir varaqli xulosa</h3>"
        "<p class='lead'>Butun kitobning o'zagi: 40 ta formula. Takrorlashdan oldin shu jadvalga qarab chiqing — "
        "qaysi strukturada qiynalsangiz, o'sha darsga qayting.</p>"
        '<table class="grid"><thead><tr><th>#</th><th>Struktura</th><th>Formula</th><th>Mavzu</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></section>"
    )


def render_index(lessons: list[dict]) -> str:
    entries = []
    for lesson in lessons:
        for en, uz, _ in lesson["words"]:
            entries.append((en, uz, lesson["n"]))
    entries.sort(key=lambda e: (e[0].lower().replace("the ", ""), e[0]))

    rows = []
    current_letter = ""
    for en, uz, n in entries:
        letter = en[0].upper()
        if letter != current_letter:
            current_letter = letter
            rows.append(f'<div class="row" style="margin-top:10px"><b style="color:var(--warm)">{esc(letter)}</b></div>')
        rows.append(
            f'<div class="row" data-w="{esc(en.lower())} {esc(uz.lower())}">'
            f'<span class="w">{esc(en)}</span><span class="t">{esc(uz)}</span>'
            f'<a class="l" href="#d{n:02d}">{n:02d}</a></div>'
        )
    return (
        '<section class="doc" id="index">'
        f"<h3>1000 so'z indeksi</h3>"
        "<p class='lead'>Har bir so'zning tarjimasi va u o'rganiladigan dars raqami. Qidiruv maydoniga "
        "so'zni yozsangiz, ro'yxat filtrlanadi.</p>"
        '<div class="idx" id="idx">' + "".join(rows) + "</div></section>"
    )


def build() -> str:
    front = load_json("front.json")
    blocks = load_json("blocks.json")["blocks"]
    lessons = load_lessons()

    print("Tekshiruv:")
    errors = validate(lessons, blocks)
    if errors:
        print("\n".join("  X " + e for e in errors))
        if "--force" not in sys.argv:
            raise SystemExit(1)
        print("  (--force: xatolarga qaramay yasaladi)")

    total_words = sum(len(l["words"]) for l in lessons)

    parts = [render_cover(front, lessons, total_words)]

    parts.append('<div class="part"><div class="kicker">1-qism</div><h2>Asoslar: gap qanday quriladi</h2>'
                 "<p>Olti bob: kitobning uslubi, uch blokli mexanika, tasdiq–inkor–savol mashinasi, "
                 "olmoshlar jadvali, so'zlashuv qatlami va yodlash tizimi. Darslarga o'tishdan oldin "
                 "shu qismni o'qib chiqing.</p></div>")
    for ch in front["chapters"]:
        parts.append(
            f'<section class="doc" id="{ch["id"]}"><div class="kicker" style="font-size:11px;letter-spacing:.18em;'
            f'text-transform:uppercase;color:var(--warm);font-weight:700">{esc(ch["kicker"])}</div>'
            f'<h3 style="margin-top:8px">{esc(ch["title"])}</h3>' + "".join(ch["body"]) + "</section>"
        )

    parts.append('<div class="part"><div class="kicker">2-qism</div><h2>40 dars</h2>'
                 "<p>Har bir dars — bitta struktura va 25 so'z. Tartibni buzmang: har bir struktura "
                 "keyingisiga tayanadi, so'zlar esa mavzu bo'yicha to'planib boradi.</p></div>")

    for block in blocks:
        parts.append(
            f'<div class="blockhead" style="margin:34px 0 6px;padding:10px 14px;background:var(--warm-soft);'
            f'border:1px solid #eeddc4;border-radius:11px;font-size:13px;color:var(--warm)">'
            f'<b>Blok {blocks.index(block) + 1} · {block["from"]}–{block["to"]}-darslar</b> — {esc(block["title"])}'
            f'<br><span style="color:var(--ink-soft)">{esc(block.get("desc", ""))}</span></div>'
        )
        for lesson in lessons:
            if block["from"] <= lesson["n"] <= block["to"]:
                parts.append(render_lesson(lesson))

    parts.append('<div class="part"><div class="kicker">3-qism</div><h2>Ko\'cha iboralari</h2>'
                 "<p>Kitobiy ingliz tili bilan ko'cha tili orasidagi ko'prik. Har bir oila — bitta vazifa "
                 "va uning uch darajadagi shakli.</p></div>")
    parts.append(render_bank(front["bank"]))

    parts.append('<div class="part"><div class="kicker">4-qism</div><h2>Ilova</h2>'
                 "<p>Strukturalar xulosasi, lug'at indeksi va kitob haqida texnik ma'lumot.</p></div>")
    parts.append(render_frames(lessons))
    parts.append(render_index(lessons))

    parts.append("""
<footer class="foot">
  <p><b>1000 so'z — 1000 gap.</b> Manbalar: «1000 ta asosiy inglizcha so'zlar» ro'yxati (jahongir prank),
  «street phrases» va «gotta» varaqalari. Ikkinchi va uchinchi manbadan gaplar emas, guruhlash va
  tasdiq–inkor–savol uslubi olindi; barcha namuna gaplar shu darslik uchun yangidan tuzilgan.</p>
  <p>Fayl yagona HTML hujjat: internetga ulanmasdan ham ishlaydi. Chop etish uchun brauzerda
  <b>Ctrl/Cmd + P</b> bosing — sahifa A4 formatiga moslangan.</p>
</footer>
<a class="top-link" href="#top">↑ Yuqoriga</a>""")

    css = (DATA / "style.css").read_text(encoding="utf-8")
    js = (DATA / "app.js").read_text(encoding="utf-8")

    doc = f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>1000 so'z — 1000 gap · ingliz tili darsligi</title>
<meta name="description" content="1000 asosiy inglizcha so'z va 40 struktura asosida gap tuzishni o'rgatadigan o'zbek tilidagi darslik.">
<style>
{css}
</style>
</head>
<body>
<div class="layout">
{render_sidebar(front, lessons, blocks)}
<main class="main">
{''.join(parts)}
</main>
</div>
<script>
{js}
</script>
</body>
</html>
"""
    OUT.write_text(doc, encoding="utf-8")
    size = OUT.stat().st_size / 1024
    print(f"  -> {OUT.name} ({size:.0f} KB)")
    return doc


if __name__ == "__main__":
    build()
