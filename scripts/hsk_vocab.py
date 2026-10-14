#!/usr/bin/env python3
"""Look up HSK 2.0 (2012) levels from the official workbook.

A word's level is the lowest sheet that lists it. The sheets are cumulative,
so 爱 is level 1 even though it also appears on the level 6 sheet.

Default workbook:
  /Users/yinshijin/Desktop/HSK2.0词汇-三级至六级/HSK-2012官方原表.xlsx

Usage:
  python3 hsk_vocab.py 爱 空调 放弃
  python3 hsk_vocab.py --segment "甲背了满满的一筐石头"
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from xml.etree import ElementTree as ET

DEFAULT_WORKBOOK = (
    "/Users/yinshijin/Desktop/HSK2.0词汇-三级至六级/HSK-2012官方原表.xlsx"
)

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}

# workbook sheet name -> level. Matched by the level digit in the name.
LEVEL_MARKS = (
    ("一级", 1),
    ("二级", 2),
    ("三级", 3),
    ("四级", 4),
    ("五级", 5),
    ("六级", 6),
)


def _inline(cell) -> str:
    texts = cell.findall(".//m:t", NS)
    return "".join((t.text or "") for t in texts).strip()


def _sheet_words(xml: bytes) -> list[str]:
    root = ET.fromstring(xml)
    words = []
    started = False
    for row in root.findall("m:sheetData/m:row", NS):
        cell = row.find("m:c", NS)
        if cell is None:
            continue
        text = _inline(cell)
        if not text:
            continue
        if not started:
            if "汉字" in text:
                started = True
            continue
        if any(mark in text for mark in ("HSK", "原表", "汉字", "说明")):
            continue
        if not any("\u4e00" <= ch <= "\u9fff" for ch in text):
            continue
        words.append(text)
    return words


def load_levels(path: str = DEFAULT_WORKBOOK) -> dict[str, int]:
    """Return word -> lowest level (1–6)."""
    with zipfile.ZipFile(path) as zf:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("r:Relationship", REL_NS)
        }
        by_level: dict[int, list[str]] = {}
        for sheet in wb.findall("m:sheets/m:sheet", NS):
            name = sheet.attrib.get("name", "")
            level = next((n for mark, n in LEVEL_MARKS if mark in name), None)
            if level is None:
                continue
            rid = sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]
            target = targets[rid].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            by_level[level] = _sheet_words(zf.read(target))
    levels: dict[str, int] = {}
    for level in range(1, 7):
        for word in by_level.get(level, []):
            levels.setdefault(word, level)
    if len(levels) < 4000:
        raise SystemExit(f"workbook looks incomplete: only {len(levels)} words in {path}")
    return levels


class Trie:
    def __init__(self) -> None:
        self.nodes: dict[str, Trie] = {}
        self.level: int | None = None

    def add(self, word: str, level: int) -> None:
        node = self
        for ch in word:
            node = node.nodes.setdefault(ch, Trie())
        node.level = level

    def longest(self, text: str, start: int) -> tuple[int | None, int]:
        node = self
        best_level = None
        best_end = start
        i = start
        while i < len(text) and text[i] in node.nodes:
            node = node.nodes[text[i]]
            i += 1
            if node.level is not None:
                best_level = node.level
                best_end = i
        return best_level, best_end


def segment(text: str, levels: dict[str, int]) -> list[dict]:
    """Longest-match the 2012 list. Unlisted characters are level null."""
    trie = Trie()
    for word, level in levels.items():
        trie.add(word, level)
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if not ("\u4e00" <= ch <= "\u9fff"):
            i += 1
            continue
        level, end = trie.longest(text, i)
        if level is None:
            out.append({"word": ch, "level": None})
            i += 1
        else:
            out.append({"word": text[i:end], "level": level})
            i = end
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up 2012 HSK levels")
    parser.add_argument("words", nargs="*", help="Exact words to look up")
    parser.add_argument("--segment", help="Segment a Chinese string by longest list match")
    parser.add_argument("--list", default=DEFAULT_WORKBOOK, help="Path to HSK-2012官方原表.xlsx")
    args = parser.parse_args()
    if not args.words and not args.segment:
        parser.error("give words or --segment")
    levels = load_levels(args.list)
    if args.segment:
        json.dump(segment(args.segment, levels), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    rows = []
    for word in args.words:
        level = levels.get(word)
        rows.append({"word": word, "level": level, "label": f"HSK {level}" if level else "off-list"})
    json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
