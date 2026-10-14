#!/usr/bin/env python3
"""Build an HSK reading-notes .docx from notes.json.

The layout matches H31008, H41009, H51553C, and H61001:
A4, Calibri for English and Songti SC for Chinese, three borderless
color blocks (navy banner, gray intro, pale-blue Summary), then the
vocabulary tables and a why-paragraph with a wrong-choice table.

Usage:
  python3 build_notes.py notes.json -o H41009-阅读解析.docx

Levels in the JSON are checked against HSK-2012官方原表.xlsx.
Question numbers must cover the whole reading section for that level.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hsk_vocab import DEFAULT_WORKBOOK, load_levels

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# Reading span for each level. Keep this in step with references/paper-map.md.
READING = {
    3: range(41, 71),
    4: range(46, 86),
    5: range(46, 91),
    6: range(51, 101),
}
MAIN_LEVELS = {3: {3}, 4: {4}, 5: {4, 5}, 6: {5, 6}}
HIGHER_LEVELS = {3: {4, 5, 6}, 4: {5, 6}, 5: {6}, 6: set()}
VOCAB_HEADING = {
    3: "Vocabulary  ·  HSK 3",
    4: "Vocabulary  ·  HSK 4",
    5: "Vocabulary  ·  HSK 4 and HSK 5",
    6: "Vocabulary  ·  HSK 5 and HSK 6",
}
BANNER_VOCAB = {
    3: "HSK 3 vocabulary, then why each answer works",
    4: "HSK 4 vocabulary, then why each answer works",
    5: "HSK 4 and HSK 5 vocabulary, then why each answer works",
    6: "HSK 5 and HSK 6 vocabulary, then why each answer works",
}
PART_LINE = {
    3: {
        1: "Part 1  ·  Choose the sentence that matches.",
        2: "Part 2  ·  Choose the word that fills each blank.",
        3: "Part 3  ·  Read the passage and choose the correct answer.",
    },
    4: {
        1: "Part 1  ·  Choose the word that fills each blank.",
        2: "Part 2  ·  Put the three sentences in the right order.",
        3: "Part 3  ·  Read the passage and choose the correct answer.",
    },
    5: {
        1: "Part 1  ·  Choose the word or sentence that fills each blank.",
        2: "Part 2  ·  Choose the statement that agrees with the passage.",
        3: "Part 3  ·  Read the article and choose the correct answer.",
    },
    6: {
        1: "Part 1  ·  Choose the sentence that has a grammar problem.",
        2: "Part 2  ·  Choose the word group that fills the blanks.",
        3: "Part 3  ·  Choose the sentence that fills each blank.",
        4: "Part 4  ·  Read the article and choose the correct answer.",
    },
}
LEVEL_COLOR = {3: "1C2833", 4: "1B4F72", 5: "148F77", 6: "6C3483"}
NAVY = "1B4F72"
TEAL = "148F77"
SLATE = "5D6D7E"
INK = "1C2833"
GOLD = "7D6608"
WHITE = "FFFFFF"
LINE = "D5D8DC"
CONTENT_W = 9866
VOCAB_COLS = (1814, 2041, 4764, 1247)
OFF_COLS = (1814, 2041, 6011)
WRONG_COLS = (2381, 2154, 5331)

INTRO = {
    3: (
        "Each unit is one task on the paper. Questions 41–45 and 46–50 each match five lines "
        "to the lettered sentences. When an example is printed, it has already used one sentence, "
        "and the five questions use the rest. Questions 51–55 and 56–60 are two word banks. "
        "Five separate sentences share six words, and the example has already used one of them. "
        "Questions 61–70 are short passages, one question each. The first table lists HSK 3 words "
        "from the 2012 list. Words from HSK 1 and HSK 2 are left out. When a unit has HSK 4, HSK 5, "
        "or HSK 6 words, a second table lists them. Those words sit above HSK 3. "
        "The reading key used here is {key}. The English says why the answer fits and why each other choice fails."
    ),
    4: (
        "Each unit is one task on the paper. Questions 46–50 and 51–55 are two word banks. "
        "Five separate sentences share six words, and the example has already used one of them. "
        "Questions 56–65 each ask for the order of three sentences. Questions 66–85 are short passages. "
        "Some passages have two questions. The first table lists HSK 4 words from the 2012 list. "
        "Words from HSK 1 to 3 are left out. When a passage has HSK 5 or HSK 6 words, a second table "
        "lists them. Those words sit above HSK 4. The reading key used here is {key}. "
        "The English says why the answer fits and why each other choice fails. "
        "Part 1 lists the other five words in the bank. Part 2 lists two orders a reader is likely to try. "
        "Part 3 lists the other printed choices."
    ),
    5: (
        "Each unit is one passage. Questions 46–60 are the gap-fill texts. Questions 61–70 are ten "
        "short texts, one each. Questions 71–90 are the longer articles. The first table in a unit "
        "lists words that are new at HSK 4 or HSK 5 on the 2012 list. Words already met at HSK 1–3 "
        "are not repeated. A second table lists HSK 6 words, which are a main reason this paper feels "
        "difficult. A few words a question depends on are not entries on that list; they are marked "
        "separately and are not given a level. The reading key used here is {key}. "
        "The English notes say why the key fits and why each other choice fails."
    ),
    6: (
        "Each unit is one item or one passage. Questions 51–60 are ten grammar items: "
        "choose the sentence that has a problem. Questions 61–70 are ten word-fill items. "
        "Questions 71–75 and 76–80 are two sentence-insertion passages. Questions 81–100 "
        "are five articles. The first table lists words that are new at HSK 5 or HSK 6 on "
        "the 2012 list. Words from HSK 1 to 4 are left out. A second table lists words in "
        "the same passage that are not on that list. The reading key used here is {key}. "
        "The English says why the answer fits and why each other choice fails. "
        "For questions 51–60, a sentence that is actually correct is labeled Looks odd."
    ),
}


def roman(n: int) -> str:
    vals = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    out = []
    for value, glyph in vals:
        while n >= value:
            out.append(glyph)
            n -= value
    return "".join(out)


def esc(text: str) -> str:
    return escape(text, {"'": "&apos;", '"': "&quot;"})


def run(text: str, size: int, color: str, bold: bool = True) -> str:
    bold_xml = "<w:b/><w:bCs/>" if bold else ""
    space = ' xml:space="preserve"' if text[:1].isspace() or text[-1:].isspace() else ""
    return (
        "<w:r><w:rPr>"
        f'<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Songti SC" w:cs="Calibri"/>'
        f"{bold_xml}<w:color w:val=\"{color}\"/>"
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        f"</w:rPr><w:t{space}>{esc(text)}</w:t></w:r>"
    )


def paragraph(inner: str, before: int = 0, after: int = 0, size_hint: int = 21) -> str:
    return (
        "<w:p><w:pPr>"
        f'<w:spacing w:before="{before}" w:after="{after}" w:line="276" w:lineRule="auto"/>'
        f'<w:rPr><w:sz w:val="{size_hint}"/><w:szCs w:val="{size_hint}"/></w:rPr>'
        f"</w:pPr>{inner}</w:p>"
    )


def para_text(text: str, size: int, color: str, before: int, after: int, bold: bool = True) -> str:
    return paragraph(run(text, size, color, bold), before, after, size)


def shade(fill: str) -> str:
    return f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'


def borders() -> str:
    edge = f'<w:{{0}} w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/>'
    names = ("top", "left", "bottom", "right", "insideH", "insideV")
    return "<w:tblBorders>" + "".join(edge.format(name) for name in names) + "</w:tblBorders>"


def cell(inner_paras: str, width: int, fill: str) -> str:
    return (
        "<w:tc><w:tcPr>"
        f'<w:tcW w:w="{width}" w:type="dxa"/>{shade(fill)}'
        '<w:tcMar><w:top w:w="60" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
        '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tcMar>'
        "<w:vAlign w:val=\"center\"/>"
        f"</w:tcPr>{inner_paras}</w:tc>"
    )


def table(rows: list[list[tuple[str, int, str]]], widths: tuple[int, ...]) -> str:
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    body = []
    for row in rows:
        cells = "".join(cell(paras, width, fill) for paras, width, fill in row)
        body.append(f"<w:tr>{cells}</w:tr>")
    return (
        "<w:tbl><w:tblPr>"
        f'<w:tblW w:w="{CONTENT_W}" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        f"{borders()}"
        "</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        + "".join(body)
        + "</w:tbl>"
    )


def nil_borders() -> str:
    edge = "<w:{0} w:val=\"nil\"/>"
    names = ("top", "left", "bottom", "right", "insideH", "insideV")
    return "<w:tblBorders>" + "".join(edge.format(name) for name in names) + "</w:tblBorders>"


def color_block(paragraphs: list[str], fill: str) -> str:
    """Borderless shaded cell. Banner, intro, and Summary use this, not table()."""
    tc_edges = "".join(f'<w:{name} w:val="nil"/>' for name in ("top", "left", "bottom", "right"))
    cell_xml = (
        "<w:tc><w:tcPr>"
        f'<w:tcW w:w="{CONTENT_W}" w:type="dxa"/>{shade(fill)}'
        f"<w:tcBorders>{tc_edges}</w:tcBorders>"
        '<w:tcMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
        '<w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tcMar>'
        f"</w:tcPr>{''.join(paragraphs)}</w:tc>"
    )
    return (
        "<w:tbl><w:tblPr>"
        f'<w:tblW w:w="{CONTENT_W}" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        f"{nil_borders()}"
        "</w:tblPr>"
        f'<w:tblGrid><w:gridCol w:w="{CONTENT_W}"/></w:tblGrid>'
        f"<w:tr>{cell_xml}</w:tr></w:tbl>"
    )


def header_row(labels: list[str], widths: tuple[int, ...], fill: str) -> list[tuple[str, int, str]]:
    return [
        (paragraph(run(label, 21, WHITE), 20, 20, 21), width, fill)
        for label, width in zip(labels, widths)
    ]


def data_row(values: list[tuple[str, str]], widths: tuple[int, ...], fill: str = WHITE) -> list[tuple[str, int, str]]:
    row = []
    for (text, color), width in zip(values, widths):
        row.append((paragraph(run(text, 21, color), 20, 20, 21), width, fill))
    return row


def vocab_table(rows: list[dict], header_fill: str) -> str:
    labels = ["Word", "Pinyin", "English", "Level"]
    built = [header_row(labels, VOCAB_COLS, header_fill)]
    for item in rows:
        level = int(str(item["level"]).replace("HSK", "").strip())
        built.append(
            data_row(
                [
                    (item["word"], INK),
                    (item["pinyin"], SLATE),
                    (item["english"], INK),
                    (f"HSK {level}", LEVEL_COLOR[level]),
                ],
                VOCAB_COLS,
            )
        )
    return table(built, VOCAB_COLS)


def off_table(rows: list[dict]) -> str:
    built = [header_row(["Word", "Pinyin", "English"], OFF_COLS, "7F8C8D")]
    for item in rows:
        built.append(
            data_row(
                [(item["word"], INK), (item["pinyin"], SLATE), (item["english"], INK)],
                OFF_COLS,
            )
        )
    return table(built, OFF_COLS)


def wrong_table(rows: list[dict]) -> str:
    built = [header_row(["Choice", "Kind of mistake", "Why it does not work"], WRONG_COLS, NAVY)]
    for item in rows:
        choice = item["choice"].strip()
        text = item.get("text", "").strip()
        shown = f"{choice}  {text}" if text else choice
        built.append(
            data_row(
                [(shown, INK), (item["mistake"], GOLD), (item["why"], INK)],
                WRONG_COLS,
            )
        )
    return table(built, WRONG_COLS)


def question_line(item: dict) -> str:
    number = item["number"]
    answer = str(item["answer"]).strip()
    text = item.get("answer_text", "").strip()
    pinyin = item.get("pinyin", "").strip()
    bits = [
        run(f"Question {number}", 24, TEAL),
        run("     ", 24, INK),
        run("Answer", 24, NAVY),
        run(f"  {answer}", 24, NAVY),
    ]
    if text or pinyin:
        tail = text
        if pinyin:
            tail = f"{tail}  {pinyin}".strip()
        bits.append(run("     ", 24, INK))
        bits.append(run(tail, 24, INK))
    return paragraph("".join(bits), 160, 40, 24)


def join_levels(levels: list[int]) -> str:
    labels = [f"HSK {n}" for n in levels]
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + ", and " + labels[-1]


def off_heading(level: int) -> tuple[str, str]:
    if level == 5:
        title = "Needed here, but not an HSK 4 or 5 entry"
        note = "Not given an HSK level, because they are not entries on the 2012 level 4 or 5 list."
    elif level == 6:
        title = "Also in this passage  ·  Above the HSK 6 list"
        note = "These are not on the 2012 list used here. They are a common reason the passage feels hard."
    else:
        title = f"Needed here, but not an HSK {level} entry"
        note = f"Not given an HSK level, because they are not entries on the 2012 level {level} list."
    return title, note


def render_unit(unit: dict, index: int, level: int) -> str:
    span = str(unit["questions"]).replace("-", "–")
    qlabel = "Question" if "–" not in span else "Questions"
    parts = [
        para_text(f"{roman(index)}. {qlabel} {span}  ·  {unit['title'].strip()}", 28, NAVY, 280, 40),
        para_text(PART_LINE[level][int(unit["part"])], 20, SLATE, 0, 120, bold=False),
        para_text("Summary", 24, TEAL, 120, 40),
        color_block([paragraph(run(unit["summary"].strip(), 21, INK, bold=False), 80, 80, 21)], "EAF2F8"),
    ]
    vocab = unit.get("vocab") or []
    if vocab:
        parts.append(para_text(VOCAB_HEADING[level], 24, TEAL, 160, 80))
        parts.append(vocab_table(vocab, NAVY))
    higher = unit.get("higher") or []
    if higher:
        present = sorted({int(str(row["level"]).replace("HSK", "").strip()) for row in higher})
        parts.append(para_text(f"Also in this passage  ·  {join_levels(present)}", 24, SLATE, 160, 40))
        parts.append(
            para_text(
                f"These sit above HSK {level}. They are a common reason the passage feels hard.",
                21, SLATE, 0, 80,
            )
        )
        parts.append(vocab_table(higher, SLATE))
    offlist = unit.get("offlist") or []
    if offlist:
        title, note = off_heading(level)
        parts.append(para_text(title, 24, TEAL, 160, 40))
        parts.append(para_text(note, 20, SLATE, 0, 80))
        parts.append(off_table(offlist))
    parts.append(para_text("Questions", 24, TEAL, 160, 40))
    for item in unit["items"]:
        parts.append(question_line(item))
        parts.append(para_text(item["why"].strip(), 21, INK, 40, 80))
        parts.append(wrong_table(item["wrongs"]))
    return "".join(parts)


def banner(code: str, level: int) -> str:
    start = READING[level].start
    end = READING[level].stop - 1
    lines = [
        paragraph(run(f"{code}  ·  Reading notes", 44, WHITE), 0, 20, 44),
        paragraph(run(f"Questions {start}–{end}  ·  {BANNER_VOCAB[level]}", 24, "D4E6F1", bold=False), 0, 20, 24),
        paragraph(
            run(f"HSK Level {level}  ·  Paper {code}  ·  Listening and writing are not included", 20, "AEB6BF", bold=False),
            0, 20, 20,
        ),
    ]
    return color_block(lines, NAVY)


def document_xml(data: dict) -> str:
    level = int(data["level"])
    code = data["code"].strip()
    key = data["key_source"].strip()
    body = [
        banner(code, level),
        paragraph("", 0, 120, 20),
        color_block(
            [paragraph(run(INTRO[level].format(key=key), 20, SLATE, bold=False), 80, 80, 20)],
            "F4F6F7",
        ),
        paragraph("", 0, 120, 20),
    ]
    for index, unit in enumerate(data["units"], start=1):
        body.append(render_unit(unit, index, level))
    sect = (
        "<w:sectPr>"
        '<w:footerReference w:type="default" r:id="rId1"/>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="964" w:right="1020" w:bottom="964" w:left="1020" '
        'w:header="720" w:footer="340" w:gutter="0"/>'
        "</w:sectPr>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>'
        + "".join(body)
        + sect
        + "</w:body></w:document>"
    )


def footer_xml(code: str) -> str:
    inner = (
        paragraph(run(f"{code}  ·  Reading notes", 18, SLATE, bold=False), 0, 0, 18)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:ftr xmlns:w="{W}">{inner}</w:ftr>'
    )


def styles_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
  <w:docDefaults>
    <w:rPrDefault><w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Songti SC" w:cs="Calibri"/>
      <w:sz w:val="21"/><w:szCs w:val="21"/>
      <w:color w:val="{INK}"/>
    </w:rPr></w:rPrDefault>
    <w:pPrDefault><w:pPr>
      <w:spacing w:line="276" w:lineRule="auto"/>
    </w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
  </w:style>
</w:styles>'''


def content_types() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>'''


def root_rels() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>'''


def doc_rels() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''


def core_xml(code: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:title>{esc(code)} reading notes</dc:title>
  <dc:creator>HSK reading notes</dc:creator>
</cp:coreProperties>'''


def require(obj: dict, key: str, where: str) -> None:
    if key not in obj or obj[key] in ("", None, []):
        raise SystemExit(f"{where} is missing {key}")


def level_num(value) -> int:
    text = str(value).replace("HSK", "").strip()
    if text not in {"3", "4", "5", "6"}:
        raise SystemExit(f"level must look like 'HSK 4' or 4, got {value!r}")
    return int(text)


def check(data: dict, levels: dict[str, int]) -> None:
    require(data, "code", "notes")
    require(data, "level", "notes")
    require(data, "key_source", "notes")
    require(data, "units", "notes")
    level = int(data["level"])
    if level not in READING:
        raise SystemExit("level must be 3, 4, 5, or 6")
    seen: list[int] = []
    for u_i, unit in enumerate(data["units"], start=1):
        where = f"unit {u_i}"
        require(unit, "title", where)
        require(unit, "questions", where)
        require(unit, "part", where)
        require(unit, "summary", where)
        require(unit, "items", where)
        part = int(unit["part"])
        if part not in PART_LINE[level]:
            raise SystemExit(f"{where} part {part} is not a part of HSK {level}")
        for row_name in ("vocab", "higher"):
            for row in unit.get(row_name) or []:
                word = row.get("word", "")
                got = level_num(row.get("level"))
                real = levels.get(word)
                if real is None:
                    raise SystemExit(f"{where} {row_name} lists {word}, which is not on the 2012 list. Put it in offlist only if a question depends on it.")
                if real != got:
                    raise SystemExit(f"{where} {word} is HSK {real}, not HSK {got}")
                allowed = MAIN_LEVELS[level] if row_name == "vocab" else HIGHER_LEVELS[level]
                if got not in allowed:
                    raise SystemExit(f"{where} {word} (HSK {got}) does not belong in the {row_name} table for an HSK {level} paper")
                for field in ("pinyin", "english"):
                    if not str(row.get(field, "")).strip():
                        raise SystemExit(f"{where} {word} needs {field}")
        for row in unit.get("offlist") or []:
            word = row.get("word", "")
            real = levels.get(word)
            if real is not None:
                raise SystemExit(f"{where} {word} is HSK {real}, so it is not off-list")
            for field in ("pinyin", "english"):
                if not str(row.get(field, "")).strip():
                    raise SystemExit(f"{where} {word} needs {field}")
        ordering = part == 2 and level == 4
        for item in unit["items"]:
            q_where = f"{where} question {item.get('number')}"
            require(item, "number", q_where)
            require(item, "answer", q_where)
            require(item, "why", q_where)
            require(item, "wrongs", q_where)
            number = int(item["number"])
            seen.append(number)
            if ordering and len(item["wrongs"]) != 2:
                raise SystemExit(f"{q_where} is an ordering item, so it needs exactly two wrong orders")
            for wrong in item["wrongs"]:
                for field in ("choice", "mistake", "why"):
                    if not str(wrong.get(field, "")).strip():
                        raise SystemExit(f"{q_where} has a wrong row missing {field}")
    expected = list(READING[level])
    if seen != expected:
        missing = [n for n in expected if n not in seen]
        extra = [n for n in seen if n not in expected]
        dupes = sorted({n for n in seen if seen.count(n) > 1})
        raise SystemExit(
            "question numbers must be the full reading section in order. "
            f"missing={missing} extra={extra} repeated={dupes}"
        )


def write_docx(data: dict, dest: Path) -> None:
    code = data["code"].strip()
    files = {
        "[Content_Types].xml": content_types(),
        "_rels/.rels": root_rels(),
        "word/document.xml": document_xml(data),
        "word/styles.xml": styles_xml(),
        "word/footer1.xml": footer_xml(code),
        "word/_rels/document.xml.rels": doc_rels(),
        "docProps/core.xml": core_xml(code),
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, xml in files.items():
            zf.writestr(name, xml.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build HSK reading notes")
    parser.add_argument("notes", help="Path to notes.json")
    parser.add_argument("-o", "--output", required=True, help="Path of the .docx to write")
    parser.add_argument("--list", default=DEFAULT_WORKBOOK, help="Path to HSK-2012官方原表.xlsx")
    args = parser.parse_args()
    data = json.loads(Path(args.notes).read_text(encoding="utf-8"))
    levels = load_levels(args.list)
    check(data, levels)
    dest = Path(args.output)
    write_docx(data, dest)
    print(f"wrote {dest} ({dest.stat().st_size} bytes, {len(data['units'])} units)")


if __name__ == "__main__":
    main()
