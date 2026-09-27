# -*- coding: utf-8 -*-
"""Tezi Word (.docx) dosyasina donusturur.

Kullanim:
    python thesis_output/build_docx.py [cikti_yolu.docx]

Kaynak: content_a.py, content_b.py, content_c.py, content_d.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))

import content_a as A  # noqa: E402
import content_b as B  # noqa: E402
import content_c as C  # noqa: E402
import content_d as D  # noqa: E402
import verified_dois  # noqa: E402

# ------------------------------------------------------------- SABI SABIT
FONT_BODY = "Times New Roman"
FONT_HEAD = "Arial"
SIZE_BODY = Pt(12)
SIZE_SMALL = Pt(10)
LINE_SPACING = 1.5


def _add_page_field(paragraph) -> None:
    """Sayfa numarasi alanini (PAGE) paragrafa ekler."""
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)


def _field(paragraph, instr_text: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instr_text
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, sep, end):
        run._r.append(el)


def _shade(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def kur_ayarlar(doc: Document) -> None:
    """Sayfa duzeni, taban ve baslik stillerini ayarlar."""
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)

    normal = doc.styles["Normal"]
    normal.font.name = FONT_BODY
    normal.font.size = SIZE_BODY
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_BODY)
    pf = normal.paragraph_format
    pf.line_spacing = LINE_SPACING
    pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    h1 = doc.styles["Heading 1"]
    h1.font.name = FONT_HEAD
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1.paragraph_format.space_before = Pt(18)
    h1.paragraph_format.space_after = Pt(12)
    h1.paragraph_format.keep_with_next = True

    h2 = doc.styles["Heading 2"]
    h2.font.name = FONT_HEAD
    h2.font.size = Pt(13)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    h2.paragraph_format.space_before = Pt(12)
    h2.paragraph_format.space_after = Pt(6)
    h2.paragraph_format.keep_with_next = True

    h3 = doc.styles["Heading 3"]
    h3.font.name = FONT_HEAD
    h3.font.size = Pt(12)
    h3.font.bold = True
    h3.font.italic = False
    h3.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    h3.paragraph_format.space_before = Pt(10)
    h3.paragraph_format.space_after = Pt(4)
    h3.paragraph_format.keep_with_next = True


def _paragraf(doc: Document, metin: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.add_run(metin)


def _madde(doc: Document, metin: str) -> None:
    p = doc.add_paragraph(metin, style="List Bullet")
    p.paragraph_format.line_spacing = LINE_SPACING
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def _tablo(doc: Document, satirlar: list[list[str]]) -> None:
    if not satirlar:
        return
    genislik = max(len(r) for r in satirlar)
    tablo = doc.add_table(rows=len(satirlar), cols=genislik)
    tablo.style = "Table Grid"
    tablo.alignment = WD_TABLE_ALIGNMENT.CENTER
    tablo.autofit = True
    for i, satir in enumerate(satirlar):
        for j, hucre_metni in enumerate(satir[:genislik]):
            hucre = tablo.cell(i, j)
            hucre.text = ""
            p = hucre.paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            )
            run = p.add_run(hucre_metni)
            run.font.size = SIZE_SMALL
            run.font.name = FONT_BODY
            if i == 0:
                run.font.bold = True
                _shade(hucre, "D9D9D9")
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def _baslik_ekle(doc: Document, metin: str, seviye: int) -> None:
    if seviye == 1:
        if metin.isupper() and len(metin) < 4:
            # Kisa ust baslik ("ÖZET", "SONUÇ") ortalanir, buyuk harf korunur.
            p = doc.add_paragraph()
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(12)
            run = p.add_run(metin.upper())
            run.font.name = FONT_HEAD
            run.font.size = Pt(16)
            run.font.bold = True
            return
        doc.add_heading(metin, level=1)
    else:
        doc.add_heading(metin, level=min(seviye, 3))


def _ogeleri_isle(doc: Document, ogeler: list) -> None:
    for ogeler_i in ogeler:
        tur = ogeler_i[0]
        if tur == "p":
            _paragraf(doc, ogeler_i[1])
        elif tur == "bullet":
            _madde(doc, ogeler_i[1])
        elif tur == "h1":
            _baslik_ekle(doc, ogeler_i[1], 1)
        elif tur == "h2":
            _baslik_ekle(doc, ogeler_i[1], 2)
        elif tur == "h3":
            _baslik_ekle(doc, ogeler_i[1], 3)
        elif tur in ("baslik", "altbaslik", "tur"):
            p = doc.add_paragraph()
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(ogeler_i[1])
            run.font.name = FONT_HEAD if tur == "baslik" else FONT_BODY
            run.font.size = Pt(18) if tur == "baslik" else Pt(13)
            run.font.bold = tur in ("baslik", "altbaslik")
        elif tur == "table":
            _tablo(doc, ogeler_i[1])
        elif tur == "caption":
            p = doc.add_paragraph()
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(10)
            run = p.add_run(ogeler_i[1])
            run.font.name = FONT_BODY
            run.font.size = SIZE_SMALL
            run.font.italic = True
        elif tur == "ref":
            metin = ogeler_i[1]
            # Yalnizca arac dogrulamasindan gecen kaynaklara DOI eklenir.
            # Dogrulanmayan kaynaklarint DOI'si bilincli olarak yazilmaz.
            doi = verified_dois.doi_al(metin)
            if doi and "doi.org" not in metin:
                metin = f"{metin.rstrip()} https://doi.org/{doi}"
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.25)
            p.paragraph_format.first_line_indent = Cm(-1.25)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(8)
            run = p.add_run(metin)
            run.font.size = Pt(11)
        elif tur == "toc":
            for baslik, sayfa in ogeler_i[1]:
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.tab_stops.add_tab_stop(Cm(16.0))
                run = p.add_run(f"{baslik}\t{sayfa}")
                run.font.size = SIZE_SMALL
                run.font.bold = baslik.isupper()
        else:
            raise ValueError(f"Bilinmeyen ogge turu: {tur!r}")


def _sayfa_basi(doc: Document) -> None:
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def _dipnot_ekle(doc: Document) -> None:
    """Alt bilgiye sayfa numarasi alanini ekler."""
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.text = ""
        _add_page_field(p)


def _bosluk_sayfasi(doc: Document) -> None:
    """Yeni bolum baslatan bos sayfa (on bilgiler icin)."""
    doc.add_section(WD_SECTION.NEW_PAGE)


def derle(cikti: Path) -> None:
    doc = Document()
    kur_ayarlar(doc)

    # --- kapak -------------------------------------------------------
    for i, ogeler_i in enumerate(A.FRONT):
        if i > 0:
            doc.add_paragraph().paragraph_format.space_after = Pt(0)
        tur = ogeler_i[0]
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(ogeler_i[1])
        run.font.name = FONT_HEAD if tur == "baslik" else FONT_BODY
        run.font.size = Pt(20) if tur == "baslik" else Pt(12)
        run.font.bold = tur in ("baslik", "altbaslik")

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run("2026")
    run.font.name = FONT_HEAD
    run.font.size = Pt(14)
    run.font.bold = True

    # --- on bilgiler -------------------------------------------------
    for blok in (D.OZET_TR, D.ABSTRACT_EN, D.TESEKKUR, D.ICINDEKILER):
        _sayfa_basi(doc)
        _ogeleri_isle(doc, blok)

    # --- ana metin ---------------------------------------------------
    for blok in (A.B1, A.B2, B.B3, B.B4, C.B5, C.B6, C.SONUC, C.KAYNAKCA, C.EKLER):
        _sayfa_basi(doc)
        _ogeleri_isle(doc, blok)

    _dipnot_ekle(doc)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(cikti))


def main() -> int:
    cikti = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parent / "tez_basin_cikti.docx"
    )
    derle(cikti)
    boyut_kb = cikti.stat().st_size / 1024
    print(f"OK: {cikti} ({boyut_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
