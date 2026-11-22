#!/usr/bin/env python3
"""
1000 so'z — 1000 gap  ·  PDF nusxa

Xuddi shu data/*.json fayllaridan kitobning bosma (A4) variantini yasaydi:

    python3 make_pdf.py        # -> 1000-soz-1000-gap.pdf

Xususiyatlari:
  * matn izlanadigan (searchable), shriftlar ichiga joylashtirilgan;
  * telefonda ochish uchun xatcho'plar (bookmark) va mundarija sahifalari;
  * yon paneldagi havolalar PDF ichida ham ishlaydi (dars raqami -> sahifa).
"""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Preformatted, Spacer,
                                Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "1000-soz-1000-gap.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

# --------------------------------------------------------------------------
# ranglar (style.css bilan bir xil ohangda)
# --------------------------------------------------------------------------

INK = colors.HexColor("#17222c")
INK_SOFT = colors.HexColor("#41505d")
MUTED = colors.HexColor("#77858f")
LINE = colors.HexColor("#e4ded3")
LINE_STRONG = colors.HexColor("#d3c9b8")
ACCENT = colors.HexColor("#0f6b62")
ACCENT_SOFT = colors.HexColor("#e3f0ee")
WARM = colors.HexColor("#a35a11")
WARM_SOFT = colors.HexColor("#fbf0e2")
GOOD = colors.HexColor("#1d6b3a")
GOOD_SOFT = colors.HexColor("#e7f4ec")
GOOD_LINE = colors.HexColor("#cbe6d5")
BAD = colors.HexColor("#a12a2a")
BAD_SOFT = colors.HexColor("#fbedeb")
BAD_LINE = colors.HexColor("#f0d2ce")
ASK = colors.HexColor("#1f4e8c")
ASK_SOFT = colors.HexColor("#e9eff8")
ASK_LINE = colors.HexColor("#d3e0f2")
PAPER = colors.HexColor("#fbf9f5")

# --------------------------------------------------------------------------
# shriftlar
# --------------------------------------------------------------------------

pdfmetrics.registerFont(TTFont("Book", str(FONT_DIR / "DejaVuSerif.ttf")))
pdfmetrics.registerFont(TTFont("Book-Bold", str(FONT_DIR / "DejaVuSerif-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Sans", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Sans-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(FONT_DIR / "DejaVuSansMono.ttf")))
pdfmetrics.registerFont(TTFont("Mono-Bold", str(FONT_DIR / "DejaVuSansMono-Bold.ttf")))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")
pdfmetrics.registerFontFamily("Book", normal="Book", bold="Book-Bold", italic="Book", boldItalic="Book-Bold")

BODY = ParagraphStyle("body", fontName="Sans", fontSize=9.2, leading=13.4, textColor=INK,
                      spaceAfter=4.5, alignment=TA_LEFT)
BODY_SERIF = ParagraphStyle("bodyserif", parent=BODY, fontName="Book", fontSize=10.2, leading=15.2)
LEAD = ParagraphStyle("lead", parent=BODY_SERIF, fontSize=10.6, leading=16.4, textColor=INK_SOFT,
                      spaceAfter=7, keepWithNext=1)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.1, leading=11.2, textColor=INK_SOFT)
TINY = ParagraphStyle("tiny", parent=BODY, fontSize=7.1, leading=9.6, textColor=INK_SOFT)
H2 = ParagraphStyle("h2", fontName="Book-Bold", fontSize=19, leading=23, textColor=INK,
                    spaceBefore=2, spaceAfter=7, keepWithNext=1)
H3 = ParagraphStyle("h3", fontName="Book-Bold", fontSize=14.4, leading=18, textColor=INK,
                    spaceBefore=4, spaceAfter=5, keepWithNext=1)
H4 = ParagraphStyle("h4", fontName="Sans-Bold", fontSize=9.6, leading=12.6, textColor=INK,
                    spaceBefore=9, spaceAfter=4, keepWithNext=1)
H5 = ParagraphStyle("h5", fontName="Sans-Bold", fontSize=6.9, leading=9, textColor=MUTED,
                    spaceAfter=2)
KICKER = ParagraphStyle("kicker", fontName="Sans-Bold", fontSize=7.2, leading=9, textColor=WARM,
                        spaceAfter=3)
FORMULA = ParagraphStyle("formula", fontName="Mono", fontSize=8.2, leading=12.2, textColor=INK)
FORMULA_S = ParagraphStyle("formulas", parent=FORMULA, fontSize=7.6, leading=10.6)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.6, leading=11.6, spaceAfter=0)
CELL_B = ParagraphStyle("cellb", parent=CELL, fontName="Sans-Bold")
CELL_H = ParagraphStyle("cellh", parent=CELL, fontName="Sans-Bold", textColor=INK)
CELL_S = ParagraphStyle("cells", parent=CELL, fontSize=7.9, leading=10.4, textColor=INK_SOFT)
CELL_MONO = ParagraphStyle("cellmono", parent=CELL, fontName="Mono", fontSize=6.6, leading=9.4,
                           wordWrap="CJK")
COVER_TITLE = ParagraphStyle("ct", fontName="Book-Bold", fontSize=38, leading=40, textColor=INK)
COVER_SUB_TITLE = ParagraphStyle("cst", fontName="Book-Bold", fontSize=25, leading=29,
                                 textColor=INK, spaceAfter=6)
COVER_SUB = ParagraphStyle("cs", fontName="Sans", fontSize=10.4, leading=15.4, textColor=INK_SOFT)
TOC_H = ParagraphStyle("toch", fontName="Sans-Bold", fontSize=8.4, leading=11, textColor=INK)
TOC_L = ParagraphStyle("tocl", fontName="Sans", fontSize=9, leading=12.4, textColor=INK)
TOC_L2 = ParagraphStyle("tocl2", parent=TOC_L, fontSize=8.3, leading=11.2, textColor=INK_SOFT,
                        leftIndent=12)
FOOT = ParagraphStyle("foot", parent=TINY, fontSize=7.4, leading=10.4, spaceAfter=3)
FAM_TITLE = ParagraphStyle("famtitle", fontName="Sans-Bold", fontSize=9.4, leading=12, textColor=WARM,
                           spaceBefore=8, spaceAfter=2, keepWithNext=1)


# --------------------------------------------------------------------------
# kichik HTML -> flowable aylantirgich (faqat kerakli teglar)
# --------------------------------------------------------------------------

class Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag: str, attrs: dict | None = None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children: list = []


VOID = {"br", "img", "hr", "input", "meta", "link"}


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, dict(attrs)))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_fragment(source: str) -> Node:
    builder = TreeBuilder()
    builder.feed(source)
    builder.close()
    return builder.root


def plain(node) -> str:
    if isinstance(node, str):
        return node
    inner = "".join(plain(c) for c in node.children)
    if node.tag == "br":
        return "\n"
    if node.tag in ("p", "h4", "li", "tr", "div", "table"):
        return inner + "\n"
    return inner


def inline(node) -> str:
    """inline HTML -> Paragraph markup (reportlab). <em> -> rang bilan ajratish."""
    if isinstance(node, str):
        return html.escape(re.sub(r"\s+", " ", node))
    if node.tag == "br":
        return "<br/>"
    inner = "".join(inline(c) for c in node.children)
    if node.tag in ("b", "strong"):
        return f"<b>{inner}</b>"
    if node.tag in ("em", "i"):
        return f'<font color="#0f6b62">{inner}</font>'
    if node.tag == "small":
        return f'<font size="7.4">{inner}</font>'
    return inner


def fragments(node) -> list:
    """faqat matn bo'laklari (p, li, ...) — boshqa teglar inline qo'shiladi."""
    out = []
    for child in node.children:
        if isinstance(child, str):
            text = child
            if text.strip():
                out.append(text)
        elif child.tag in ("p", "li"):
            out.append(inline(child))
        elif child.tag in ("div", "td", "th", "h4", "b", "em", "span"):
            out.extend(fragments(child))
        elif child.tag == "br":
            continue
        else:
            out.extend(fragments(child))
    cleaned: list = []
    for item in out:
        item = re.sub(r"[ \t\r\n]+", " ", item)
        if cleaned and not re.search(r"[ (>\-—:]$", cleaned[-1]) and not item.startswith(" "):
            item = " " + item if not re.match(r"^[,.;:!?)»”]", item) else item
        cleaned.append(item)
    return [c for c in cleaned if c.strip()]


def stylish(text: str, style=CELL) -> Paragraph:
    return Paragraph(text or "&nbsp;", style)


def grid_table(rows: list[list[str]], widths: list[float], header: bool = True,
               font_small: bool = False, mono_col: list[int] | None = None) -> Table:
    mono_col = mono_col or []
    body = []
    for r, row in enumerate(rows):
        line = []
        for c, cell in enumerate(row):
            if isinstance(cell, Paragraph):
                line.append(cell)
            elif header and r == 0:
                line.append(Paragraph(cell, CELL_H))
            elif c in mono_col:
                line.append(Paragraph(cell, CELL_MONO))
            else:
                line.append(Paragraph(cell, CELL_S if font_small and c > 0 else CELL))
        body.append(line)
    table = Table(body, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), WARM_SOFT),
                  ("LINEBELOW", (0, 0), (-1, 0), 0.7, LINE_STRONG)]
    table.setStyle(TableStyle(style))
    return table


def html_block_flowables(source: str) -> list:
    """front.json / lessons dagi cheklangan HTML ni flowable ro'yxatiga aylantiradi."""
    root = parse_fragment(source)
    flow: list = []
    for node in root.children:
        if isinstance(node, str):
            text = node.strip()
            if text:
                flow.append(Paragraph(inline(text), BODY_SERIF))
            continue
        tag = node.tag
        if tag == "p":
            cls = node.attrs.get("class", "")
            style = LEAD if "lead" in cls else BODY_SERIF
            flow.append(Paragraph(inline(node), style))
        elif tag == "h4":
            flow.append(Paragraph(inline(node), H4))
        elif tag == "formula":
            flow.append(formula_box(plain(node)))
        elif tag == "table":
            flow.append(html_table(node))
        elif tag == "div":
            cls = node.attrs.get("class", "")
            if "tip" in cls:
                inner = "".join(f"<p>{t}</p>" for t in fragments(node) if t.strip())
                flow.append(callout(inner, WARM_SOFT, WARM))
            else:
                flow.extend(html_block_flowables(plain(node)))
        elif tag in ("ul", "ol"):
            flow.extend(list_flowables(node))
        else:
            text = inline(node).strip()
            if text:
                flow.append(Paragraph(text, BODY_SERIF))
    return flow


def html_table(node: Node) -> Table:
    rows: list[list[str]] = []
    header = False
    for tr in [c for c in node.children if not isinstance(c, str) and c.tag in ("tr", "thead", "tbody")]:
        trs = [tr] if tr.tag == "tr" else [c for c in tr.children if not isinstance(c, str) and c.tag == "tr"]
        for row in trs:
            cells = []
            is_head = tr.tag == "thead"
            for td in [c for c in row.children if not isinstance(c, str) and c.tag in ("td", "th")]:
                text = "".join(inline(c) for c in td.children)
                cells.append(text)
                if td.tag == "th":
                    is_head = True
            if cells:
                rows.append(cells)
                header = header or is_head
    if not rows:
        return Spacer(1, 1)
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    width = CONTENT_W
    widths = [width / ncols] * ncols
    if ncols == 2:
        widths = [width * 0.38, width * 0.62]
    return grid_table(rows, widths, header=header, font_small=True)


def list_flowables(node: Node) -> list:
    items = [c for c in node.children if not isinstance(c, str) and c.tag == "li"]
    if not items:
        return []
    rows = []
    for i, li in enumerate(items, 1):
        prefix = f"{i}." if node.tag == "ol" else "•"
        rows.append([Paragraph(prefix, CELL), Paragraph("".join(inline(c) for c in li.children), CELL)])
    table = Table(rows, colWidths=[13, CONTENT_W - 13], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
    ]))
    return [table, Spacer(1, 3)]


def formula_box(text: str, small: bool = False) -> Table:
    body = Paragraph(html.escape(text.strip("\n")).replace("\n", "<br/>").replace(" ", "&nbsp;"),
                     FORMULA_S if small else FORMULA)
    table = Table([[body]], colWidths=[CONTENT_W], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f4ef")),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE_STRONG),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def callout(inner_markup: str, bg, border, style=BODY) -> Table:
    table = Table([[Paragraph(inner_markup, style)]], colWidths=[CONTENT_W], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.6, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def card_split(flowables: list, padding: float = 8) -> Table:
    """Bir ustunli, satr bo'yicha bo'linadigan kartochka (uzun mashq bloklari uchun)."""
    rows = [[f] for f in flowables]
    table = Table(rows, colWidths=[CONTENT_W], hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def card(flowables: list, padding: float = 8) -> Table:
    table = Table([[flowables]], colWidths=[CONTENT_W], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding - 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding - 2),
    ]))
    return table


# --------------------------------------------------------------------------
# ma'lumot
# --------------------------------------------------------------------------

def load_json(name: str) -> dict:
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def load_lessons() -> list[dict]:
    lessons: list[dict] = []
    for path in sorted(DATA.glob("lessons_*.json")):
        lessons.extend(json.loads(path.read_text(encoding="utf-8"))["lessons"])
    lessons.sort(key=lambda l: l["n"])
    return lessons


def e(text: str) -> str:
    return html.escape(str(text), quote=False)


# --------------------------------------------------------------------------
# sahifa o'lchami va kontent
# --------------------------------------------------------------------------

PAGE_W, PAGE_H = A4
MARGIN = 15 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


class Book(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, pagesize=A4,
                         leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=17 * mm, bottomMargin=16 * mm,
                         title="1000 so'z — 1000 gap · ingliz tili darsligi",
                         author="1000 so'z — 1000 gap",
                         subject="O'zbek tilida so'zlashuvchilar uchun ingliz tili darsligi",
                         creator="build: make_pdf.py", **kwargs)
        frame = Frame(MARGIN, 16 * mm, CONTENT_W, PAGE_H - 33 * mm, id="body",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[Frame(MARGIN, 16 * mm, CONTENT_W,
                                                   PAGE_H - 36 * mm, leftPadding=0,
                                                   rightPadding=0, topPadding=0,
                                                   bottomPadding=0)], onPage=self.draw_cover),
            PageTemplate(id="main", frames=[frame], onPage=self.draw_furniture),
        ])
        self._bm = 0

    # --- chizish ---
    def draw_cover(self, canv, doc):
        canv.saveState()
        canv.setFillColor(PAPER)
        canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        canv.setFillColor(ACCENT)
        canv.rect(0, PAGE_H - 26 * mm, PAGE_W, 26 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont("Sans-Bold", 7.6)
        canv.drawString(MARGIN, PAGE_H - 15 * mm, "O'ZBEK TILIDA SO'ZLASHUVCHILAR UCHUN · 40 KUNLIK KURS")
        canv.restoreState()

    def draw_furniture(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.5)
        y = PAGE_H - 12 * mm
        canv.line(MARGIN, y, PAGE_W - MARGIN, y)
        canv.setFont("Sans", 7)
        canv.setFillColor(MUTED)
        canv.drawString(MARGIN, y + 2.2 * mm, "1000 so'z — 1000 gap")
        canv.drawRightString(PAGE_W - MARGIN, y + 2.2 * mm, "Ingliz tili darsligi · 40 dars")
        canv.line(MARGIN, 12 * mm, PAGE_W - MARGIN, 12 * mm)
        canv.setFont("Sans-Bold", 8)
        canv.setFillColor(INK_SOFT)
        canv.drawCentredString(PAGE_W / 2, 8 * mm, str(canv.getPageNumber()))
        canv.restoreState()

    # --- xatcho'p + mundarija ---
    def afterFlowable(self, flowable):
        level = getattr(flowable, "_toc_level", None)
        if level is None:
            return
        text = flowable._toc_text
        self._bm += 1
        key = f"bm{self._bm}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=level > 0)
        self.notify("TOCEntry", (level, text, self.page))


def bookmark(flowable, text: str, level: int):
    flowable._toc_level = level
    flowable._toc_text = text
    return flowable


# --------------------------------------------------------------------------
# bloklar
# --------------------------------------------------------------------------

def cover(front: dict, lessons: list[dict]) -> list:
    flow = [Spacer(1, 52 * mm)]
    flow.append(Paragraph("1000 so'z —", COVER_TITLE))
    flow.append(Paragraph("1000 gap", COVER_TITLE))
    flow.append(Spacer(1, 7 * mm))
    flow.append(Paragraph(e(front["subtitle"]), COVER_SUB))
    flow.append(Spacer(1, 5 * mm))
    flow.append(Paragraph("Har kuni 25 so'z va bitta struktura: 40 kunda so'z boyligi ham, "
                          "gap qurish ko'nikmasi ham birga o'sadi.", COVER_SUB))
    flow.append(Spacer(1, 12 * mm))

    facts = [
        ["1000", "asosiy so'z"],
        ["40", "dars · struktura"],
        ["15", "ibora oilasi"],
        ["3", "xil mashq har darsda"],
    ]
    cells = [[Paragraph(f"<font name='Book-Bold' size='19'>{a}</font><br/>"
                        f"<font size='7.6' color='#41505d'>{b}</font>", CELL) for a, b in facts]]
    table = Table(cells, colWidths=[CONTENT_W / 4] * 4, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 12 * mm))

    parts = [
        ("1-qism · Asoslar", "Gap qurish mexanikasi, olmoshlar, so'zlashuv qatlami, yodlash tizimi"),
        ("2-qism · 40 dars", "Har darsda: struktura, 25 so'z, 8 namuna gap, ko'cha varianti, mashqlar"),
        ("3-qism · Ko'cha iboralari", "15 oila: ruxsat, tushunish, kelishuv, baholash"),
        ("4-qism · Ilova", "40 struktura xulosasi va 1000 so'z indeksi"),
    ]
    rows = [[Paragraph(f"<b>{e(a)}</b>", CELL), Paragraph(e(b), CELL_S)] for a, b in parts]
    ptable = Table(rows, colWidths=[46 * mm, CONTENT_W - 46 * mm], hAlign="LEFT")
    ptable.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    flow.append(ptable)

    flow.append(Spacer(1, 10 * mm))
    flow.append(Paragraph("Bu nusxa telefonda o'qish va chop etish uchun. PDF ichida xatcho'plar bor: "
                          "o'quvchi dasturida (Preview, Adobe, Google Drive, Telegram) mundarijadan "
                          "kerakli darsga o'tish mumkin.", SMALL))
    flow.append(NextPageTemplate("main"))
    flow.append(PageBreak())
    return flow


def toc_page(pages: dict) -> list:
    front = load_json("front.json")
    blocks = load_json("blocks.json")["blocks"]
    lessons = load_lessons()

    rows: list[tuple[int, str, str]] = []  # (daraja, sarlavha, kalit)
    for ch in front["chapters"]:
        rows.append((1, ch["title"], ch["title"]))
    rows.append((0, "2-qism · 40 dars", "2-qism: 40 dars"))
    for block in blocks:
        rows.append((1, f"Blok {blocks.index(block) + 1} · {block['from']}–{block['to']}-darslar "
                        f"— {block['title']}", ""))
        for lesson in lessons:
            if block["from"] <= lesson["n"] <= block["to"]:
                rows.append((2, f"{lesson['n']:02d}. {lesson['title']}", f"{lesson['n']:02d}. {lesson['title']}"))
    rows.insert(0, (0, "1-qism: Asoslar: gap qanday quriladi", "1-qism: Asoslar: gap qanday quriladi"))
    rows.append((0, "3-qism: Ko'cha iboralari", "3-qism: Ko'cha iboralari"))
    rows.append((0, "4-qism: Ilova", "4-qism: Ilova"))

    st_l1 = ParagraphStyle("tl1", fontName="Sans-Bold", fontSize=9.2, leading=13, textColor=INK)
    st_l2 = ParagraphStyle("tl2", fontName="Sans", fontSize=8.7, leading=12.4, textColor=INK_SOFT)
    st_num = ParagraphStyle("tn", fontName="Sans-Bold", fontSize=8.3, leading=12.4, textColor=ACCENT,
                            alignment=2)

    def build_table(chunk: list) -> Table:
        body = []
        for level, title, key in chunk:
            page = pages.get(key) if key else None
            num = f"{page}" if page else ""
            style = st_l1 if level <= 1 else st_l2
            pad = 0 if level else 0
            body.append([Paragraph(("&nbsp;" * (level * 3)) + e(title), style),
                         Paragraph(num, st_num)])
        table = Table(body, colWidths=[CONTENT_W - 26, 26], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.HexColor("#efece5")),
            ("TOPPADDING", (0, 0), (-1, -1), 2.6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ]))
        return table

    chars = sum(len(t) for _, t, _ in rows)
    split = 0
    acc = 0
    for i, (_, t, _) in enumerate(rows):
        acc += len(t)
        if acc > chars * 0.52:
            split = i + 1
            break
    return [
        Paragraph("Mundarija", H2),
        Paragraph("Kitobning to'liq tuzilishi. PDF o'quvchisida chap paneldagi xatcho'plar "
                  "ham shu bo'limlarga olib boradi.", SMALL),
        Spacer(1, 4),
        build_table(rows[:split]),
        PageBreak(),
        build_table(rows[split:]),
        PageBreak(),
    ]


def part_divider(num: str, title: str, text: str) -> list:
    kick = Paragraph(f"<font size='7.6' color='#a35a11'>{e(num)}</font>", KICKER)
    bookmark(kick, f"{num}: {title}", 0)
    band = Table([[""]], colWidths=[CONTENT_W], rowHeights=[2.4 * mm], hAlign="LEFT")
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)]))
    return [PageBreak(), Spacer(1, 55 * mm), band, Spacer(1, 7 * mm), kick,
            Paragraph(e(title), COVER_SUB_TITLE), Paragraph(e(text), LEAD),
            PageBreak()]


def chapter_block(ch: dict) -> list:
    flow = []
    head = Paragraph(e(ch["title"]), H3)
    bookmark(head, ch["title"], 1)
    flow.append(Paragraph(e(ch["kicker"]), KICKER))
    flow.append(head)
    for body in ch["body"]:
        flow.extend(html_block_flowables(body))
    flow.append(Spacer(1, 8))
    return flow


def triad_flowable(triad: dict) -> Table:
    def cell(title: str, items: list[str], bg, fg) -> list:
        inner = [Paragraph(title.upper(), ParagraphStyle("th", parent=H5, textColor=fg))]
        for item in items:
            inner.append(Paragraph(f"· {e(item)}", ParagraphStyle("ti", parent=BODY, fontSize=8.3,
                                                                  leading=11.2, spaceAfter=1.6)))
        return [inner]

    cells = [[cell("Tasdiq", triad["aff"], GOOD_SOFT, GOOD),
              cell("Inkor", triad["neg"], BAD_SOFT, BAD),
              cell("Savol", triad["q"], ASK_SOFT, ASK)]]
    table = Table(cells, colWidths=[CONTENT_W / 3] * 3, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), GOOD_SOFT),
        ("BACKGROUND", (1, 0), (1, 0), BAD_SOFT),
        ("BACKGROUND", (2, 0), (2, 0), ASK_SOFT),
        ("BOX", (0, 0), (0, 0), 0.6, GOOD_LINE),
        ("BOX", (1, 0), (1, 0), 0.6, BAD_LINE),
        ("BOX", (2, 0), (2, 0), 0.6, ASK_LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow = [table]
    if triad.get("short"):
        flow.append(Spacer(1, 3))
        flow.append(callout("<font size='6.9' color='#77858f'><b>QISQA JAVOBLAR</b></font><br/>"
                            + " &nbsp;·&nbsp; ".join(e(x) for x in triad["short"]), colors.white, LINE))
    return KeepTogether(flow) if False else _Stack(flow)


class _Stack(Table):
    """bir nechta flowable ni ustma-ust joylaydigan ko'rinmas jadval."""

    def __init__(self, flowables: list):
        super().__init__([[f] for f in flowables], colWidths=[CONTENT_W], hAlign="LEFT")
        self.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))


def words_flowable(words: list[list[str]]) -> Table:
    rows = [["So'z", "Tarjima", "Tayyor birikma"]]
    for en, uz, col in words:
        rows.append([f"<b>{e(en)}</b>", e(uz), f"<font color='#41505d'>{e(col)}</font>"])
    width = CONTENT_W
    return grid_table(rows, [width * 0.33, width * 0.29, width * 0.38], header=True, font_small=True)


def highlight_inline(text: str, words: list[list[str]]) -> str:
    out = e(text)
    for row in words:
        word = row[0]
        base = word.split(" (")[0].strip()
        if len(base) < 3:
            continue
        pattern = re.compile(r"(?<![\w-])(" + re.escape(base) + r"(?:s|es|ed|d|ing|'s)?)(?![\w-])",
                             re.IGNORECASE)
        out = pattern.sub(r'<font color="#0f6b62">\1</font>', out, count=2)
    return out


def examples_flowable(examples: list[dict], words: list[list[str]]) -> list:
    ex_style = ParagraphStyle("exen", parent=BODY, fontSize=8.9, leading=12.4, spaceAfter=0)
    rows = []
    for i, ex in enumerate(examples, 1):
        body = (highlight_inline(ex["en"], words)
                + "<br/><font color='#41505d' size='7.9'>" + e(ex["uz"]) + "</font>")
        rows.append([Paragraph(f"{i}.", TINY), Paragraph(body, ex_style)])
    table = Table(rows, colWidths=[13, CONTENT_W - 13], hAlign="LEFT")
    lines = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 0),
             ("RIGHTPADDING", (0, 0), (0, -1), 1),
             ("RIGHTPADDING", (1, 0), (1, -1), 3),
             ("TOPPADDING", (0, 0), (-1, -1), 2.6),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
             ("LINEBELOW", (1, 0), (1, -1), 0.4, LINE)]
    table.setStyle(TableStyle(lines))
    return [table]


def street_flowable(street: dict) -> Table:
    street_title = (street.get("title") or "Ko'cha varianti").upper()
    inner = [Paragraph("<font color='#a35a11'><b>" + e(street_title) + "</b></font>", H5)]
    for item in street["items"]:
        inner.append(Paragraph(f"<b>{e(item['en'])}</b><br/>"
                               f"<font size='7.6' color='#41505d'>{e(item['uz'])}</font>",
                               ParagraphStyle("st", parent=BODY, fontSize=8.4, leading=11.4,
                                              spaceAfter=2.6)))
    if street.get("note"):
        inner.append(Spacer(1, 2))
        inner.append(Paragraph(f"<font size='7.4'>{e(street['note'])}</font>", SMALL))
    table = Table([[inner]], colWidths=[CONTENT_W], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARM_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#eeddc4")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def dialog_flowable(dialog: dict) -> Table:
    rows = []
    for line in dialog["lines"]:
        who = line.get("who", "A")
        rows.append([
            Paragraph(f"<b>{e(who)}</b>", ParagraphStyle("who", parent=CELL, fontSize=8.2,
                                                         textColor=ACCENT)),
            Paragraph(f"{e(line['en'])}<br/><font size='7.5' color='#41505d'>{e(line['uz'])}</font>",
                      ParagraphStyle("dl", parent=BODY, fontSize=8.7, leading=12, spaceAfter=0)),
        ])
    table = Table(rows, colWidths=[13, CONTENT_W - 13], hAlign="LEFT")
    lines = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 0),
             ("RIGHTPADDING", (0, 0), (-1, -1), 4),
             ("TOPPADDING", (0, 0), (-1, -1), 2.4),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4)]
    for i in range(1, len(rows)):
        lines.append(("LINEABOVE", (1, i), (1, i), 0.35, LINE))
    table.setStyle(TableStyle(lines))
    return table


def exercises_flowable(ex: dict) -> list:
    inner: list = []
    specs = [
        ("substitution", "1. Almashtirish", "bo'sh joyni ko'rsatilgan so'z bilan to'ldiring",
         lambda x: x["prompt"], lambda x: x["answer"]),
        ("translate", "2. Tarjima", "o'zbekchadan inglizchaga",
         lambda x: x["uz"], lambda x: x["en"]),
        ("fix", "3. Xato topish", "gapda xato bor, tuzating",
         lambda x: f"<font color='#a12a2a'>{e(x['wrong'])}</font>",
         lambda x: f"{e(x['right'])} <font color='#77858f'>— {e(x['why'])}</font>"),
    ]
    for key, title, hint, q, a in specs:
        items = ex.get(key) or []
        if not items:
            continue
        inner.append(Paragraph(f"<b>{title}</b> <font size='7.4' color='#77858f'>— {hint}</font>", H4))
        qrows = [[Paragraph(f"{i}.", TINY), Paragraph(q(item), CELL)] for i, item in enumerate(items, 1)]
        qtable = Table(qrows, colWidths=[13, CONTENT_W - 44], hAlign="LEFT")
        qtable.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (0, -1), 1),
                                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6)]))
        inner.append(qtable)
        arows = [[Paragraph(f"{i}.", TINY), Paragraph(a(item), CELL_S)] for i, item in enumerate(items, 1)]
        atable = Table(arows, colWidths=[13, CONTENT_W - 44], hAlign="LEFT")
        atable.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (0, -1), 1),
                                    ("TOPPADDING", (0, 0), (-1, -1), 0.8),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2)]))
        inner.append(Spacer(1, 2))
        inner.append(Paragraph("JAVOBLAR", H5))
        inner.append(atable)
        inner.append(Spacer(1, 4))
    return [card_split(inner)]


def lesson_block(lesson: dict, break_before: bool = True) -> list:
    n = lesson["n"]
    frame = lesson["frame"]
    flow: list = [PageBreak()] if break_before else []

    head = Paragraph(f"<font size='9' color='#a35a11'><b>{n:02d}</b></font> · "
                     f"{e(lesson['title'])}", H3)
    bookmark(head, f"{n:02d}. {lesson['title']}", 1)

    meta = Paragraph(f"<font color='#0f6b62'><b>Struktura {n}</b></font> · "
                     f"<font color='#41505d'>{e(lesson.get('theme', ''))}</font>", SMALL)

    intro = [meta, head, Paragraph(e(lesson.get("goal", "")), LEAD)]

    inner = [Paragraph(f"Bugungi struktura · {e(frame['name'])}", H4),
             formula_box(frame["formula"]),
             Spacer(1, 4),
             Paragraph(frame["explain"], BODY)]
    if frame.get("table"):
        rows = [["Shakl", "Ma'nosi"]] + [[f"<b>{e(a)}</b>", e(b)] for a, b in frame["table"]]
        inner.append(Spacer(1, 4))
        inner.append(grid_table(rows, [CONTENT_W * 0.36 - 16, CONTENT_W * 0.64 - 16],
                                font_small=True))
    flow.append(KeepTogether(intro + [Spacer(1, 2), card(inner)]))

    flow.append(Paragraph("Bitta struktura — uch shakl", H4))
    flow.append(triad_flowable(lesson["triad"]))

    flow.append(Paragraph("Bugungi 25 so'z", H4))
    flow.append(words_flowable(lesson["words"]))

    flow.append(Paragraph("Namuna gaplar", H4))
    flow.extend(examples_flowable(lesson["examples"], lesson["words"]))

    if lesson.get("street"):
        flow.append(Spacer(1, 6))
        flow.append(street_flowable(lesson["street"]))
    if lesson.get("dialog"):
        flow.append(Paragraph(e(lesson["dialog"].get("title", "Mini dialog")), H4))
        flow.append(dialog_flowable(lesson["dialog"]))

    flow.append(Spacer(1, 3))
    flow.extend(exercises_flowable(lesson["exercises"]))

    tip = callout(lesson.get("tip", ""), WARM_SOFT, colors.HexColor("#eeddc4"), BODY)
    flow.append(Spacer(1, 6))
    flow.append(tip)
    flow.append(Spacer(1, 12))
    return flow


def block_head(block: dict, index: int) -> list:
    inner = (f"<b>Blok {index} · {block['from']}–{block['to']}-darslar</b> — {e(block['title'])}<br/>"
             f"<font size='7.6' color='#41505d'>{e(block.get('desc', ''))}</font>")
    table = Table([[Paragraph(inner, BODY)]], colWidths=[CONTENT_W], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARM_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#eeddc4")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [Spacer(1, 4), table, Spacer(1, 8)]


def bank_flowables(bank: list[dict]) -> list:
    flow = []
    for i, fam in enumerate(bank, 1):
        flow.append(Paragraph(f"Oila {i:02d} · {e(fam['title'])}", FAM_TITLE))
        flow.append(Paragraph(e(fam["use"]), SMALL))
        rows = [[Paragraph(f"<b>{e(en)}</b>", CELL), Paragraph(e(uz), CELL_S)] for en, uz in fam["rows"]]
        table = Table(rows, colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2.4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ]))
        flow.append(table)
        if fam.get("note"):
            flow.append(Spacer(1, 2))
            flow.append(Paragraph(f"<font size='7.4' color='#41505d'>{e(fam['note'])}</font>", SMALL))
        flow.append(Spacer(1, 4))
    return flow


def frames_flowables(lessons: list[dict]) -> list:
    rows = [["#", "Struktura", "Formula", "Mavzu"]]
    for l in lessons:
        first_line = re.sub(r"\s{2,}", " ", l["frame"]["formula"].splitlines()[0].strip())
        first_line = e(first_line).replace(" ", "&nbsp;")
        rows.append([f"{l['n']:02d}", e(l["frame"]["name"]),
                     Paragraph(f"<font name='Mono' size='6.6'>{first_line}</font>", CELL_MONO),
                     e(l["theme"])])
    return [grid_table(rows, [9 * mm, 37 * mm, CONTENT_W - 9 * mm - 37 * mm - 32 * mm, 32 * mm],
                       font_small=True)]


def index_flowables(lessons: list[dict]) -> list:
    entries = []
    for lesson in lessons:
        for en, uz, _ in lesson["words"]:
            entries.append((en, uz, lesson["n"]))
    entries.sort(key=lambda x: (x[0].lower().replace("the ", ""), x[0]))

    glyph = ParagraphStyle("gl", parent=H4, textColor=WARM, spaceBefore=6, spaceAfter=2)
    flow: list = []
    groups = 3
    chunk_rows: list[list[str]] = []
    letter = ""
    pending: list[tuple] = []

    def flush():
        nonlocal pending
        if not pending:
            return
        rows = []
        for i in range(0, len(pending), groups):
            row = []
            for en, uz, n in pending[i:i + groups]:
                row += [Paragraph(f"<b>{e(en)}</b>", TINY),
                        Paragraph(e(uz), TINY),
                        Paragraph(f"{n:02d}", ParagraphStyle("ix", parent=TINY, textColor=MUTED))]
            while len(row) < groups * 3:
                row.append(Paragraph("", TINY))
            rows.append(row)
        widths = [CONTENT_W * 0.15, CONTENT_W * 0.13, CONTENT_W * 0.05] * groups
        table = Table(rows, colWidths=widths, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1.6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1.6),
            ("TOPPADDING", (0, 0), (-1, -1), 0.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0.7),
        ]))
        flow.append(table)
        pending = []

    for en, uz, n in entries:
        first = en[0].upper()
        if first != letter:
            flush()
            letter = first
            flow.append(Paragraph(f"{e(letter)}", glyph))
        pending.append((en, uz, n))
    flush()
    return flow


# --------------------------------------------------------------------------
# yig'ish
# --------------------------------------------------------------------------

def make_story(pages: dict | None = None) -> list:
    """Har bir o'tishda hikoyani yangidan quradi — mundarija raqamlari to'g'ri chiqishi uchun."""
    pages = pages or {}
    front = load_json("front.json")
    blocks = load_json("blocks.json")["blocks"]
    lessons = load_lessons()
    stories: list = []

    stories += cover(front, lessons)
    stories += toc_page(pages)
    stories.append(NextPageTemplate("main"))

    stories += part_divider("1-qism", "Asoslar: gap qanday quriladi",
                            "Olti bob: kitobning uslubi, uch blokli mexanika, tasdiq–inkor–savol "
                            "mashinasi, olmoshlar jadvali, so'zlashuv qatlami va yodlash tizimi. "
                            "Darslarga o'tishdan oldin shu qismni o'qib chiqing.")
    for ch in front["chapters"]:
        stories += chapter_block(ch)

    stories += part_divider("2-qism", "40 dars",
                            "Har bir dars — bitta struktura va 25 so'z. Tartibni buzmang: har bir "
                            "struktura keyingisiga tayanadi, so'zlar esa mavzu bo'yicha to'planib boradi.")
    for i, block in enumerate(blocks, 1):
        if i > 1:
            stories.append(PageBreak())
        stories += block_head(block, i)
        first = True
        for lesson in lessons:
            if block["from"] <= lesson["n"] <= block["to"]:
                stories += lesson_block(lesson, break_before=not first)
                first = False

    stories += part_divider("3-qism", "Ko'cha iboralari",
                            "Kitobiy ingliz tili bilan ko'cha tili orasidagi ko'prik. Har bir oila — "
                            "bitta vazifa va uning uch darajadagi shakli.")
    stories += bank_flowables(front["bank"])

    stories += part_divider("4-qism", "Ilova",
                            "40 struktura xulosasi, 1000 so'z indeksi va kitob haqida texnik ma'lumot.")
    stories.append(Paragraph("40 struktura — bir varaqli xulosa", H3))
    stories.append(Paragraph("Butun kitobning o'zagi: 40 ta formula. Takrorlashdan oldin shu jadvalga "
                             "qarab chiqing — qaysi strukturada qiynalsangiz, o'sha darsga qayting.", LEAD))
    stories += frames_flowables(lessons)
    stories.append(PageBreak())
    stories.append(Paragraph("1000 so'z indeksi", H3))
    stories.append(Paragraph("Har bir so'zning tarjimasi va u o'rganiladigan dars raqami. "
                             "Qidiruv uchun PDF o'quvchisining izlash funksiyasidan foydalaning.", LEAD))
    stories += index_flowables(lessons)

    stories.append(PageBreak())
    stories.append(Paragraph("Kitob haqida", H3))
    for para in [
        "<b>1000 so'z — 1000 gap.</b> Manbalar: «1000 ta asosiy inglizcha so'zlar» ro'yxati "
        "(jahongir prank), «street phrases» va «gotta» varaqalari. Ikkinchi va uchinchi manbadan "
        "gaplarning o'zi emas, guruhlash va tasdiq–inkor–savol uslubi olindi; barcha namuna gaplar "
        "shu darslik uchun yangidan tuzilgan.",
        "Fayl ikki ko'rinishda mavjud: <b>index.html</b> (internetga ulanmasdan ishlaydigan interaktiv "
        "darslik: mundarija, qidiruv, «bajarildi» belgilari) va shu <b>PDF nusxa</b> — telefonda "
        "o'qish, chop etish yoki boshqa kishiga yuborish uchun.",
        "Chop etish: A4, ikki tomonlama. Har bir dars o'z blokida boshlanadi, javoblar savollardan "
        "keyin beriladi.",
    ]:
        stories.append(Paragraph(para, BODY_SERIF))
        stories.append(Spacer(1, 4))

    return stories


def build() -> None:
    pages: dict[str, int] = {}
    for attempt in range(3):
        doc = Book(str(OUT))
        doc.multiBuild(make_story(pages))
        fresh = dict((t, p) for lvl, t, p in doc_outline(OUT))
        if fresh == pages:
            break
        pages = fresh
    add_toc_links(OUT)
    size = OUT.stat().st_size / 1024
    print(f"  -> {OUT.name} ({size:.0f} KB)")


def doc_outline(path: Path) -> list:
    try:
        import pymupdf
    except ImportError:
        return []

    with pymupdf.open(str(path)) as d:
        return d.get_toc()


# --------------------------------------------------------------------------
# mundarijaga bosiladigan havolalar qo'shish
# --------------------------------------------------------------------------

def add_toc_links(path: Path) -> None:
    try:
        import pymupdf
    except ImportError:  # ixtiyoriy bosqich
        return

    doc = pymupdf.open(str(path))
    toc = doc.get_toc()
    if not toc:
        return

    def norm(text: str) -> str:
        return re.sub(r"[\s.·]+", " ", text).strip().lower()

    added = 0
    for page in doc:
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"])
                if text.strip():
                    lines.append((norm(text), pymupdf.Rect(line["bbox"])))
        if not lines:
            continue
        for level, title, target in toc:
            key = norm(re.sub(r"^\d+-qism: ", "", title))
            if len(key) < 6:
                continue
            for text, rect in lines:
                if text == key or text.startswith(key[:max(12, len(key) - 3)]):
                    page.insert_link({"kind": pymupdf.LINK_GOTO, "from": rect,
                                      "page": target - 1, "to": pymupdf.Point(0, 0)})
                    added += 1
                    break
    doc.saveIncr() if added else None
    doc.close()
    print(f"     mundarija havolalari: {added}")


if __name__ == "__main__":
    build()
