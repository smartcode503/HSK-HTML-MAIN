---
name: HSK-HTML-MAIN
description: >
  Build an HSK 2.0 level 3, 4, 5, or 6 paper into reading notes, the answer
  PDF, the listening-script PDF, and Trimulia practice HTML. A missing
  listening recording does not stop the pack. The HTML is last: after the student submits, each reading explanation
  of the right choice and the wrong choices is taken from the reading-notes
  file, the page shows the score, and 输出 downloads a score PDF. Use when
  the user supplies an HSK 真题 and asks for 阅读解析, 听力 HTML, 阅读 HTML,
  or 交卷后输出 PDF. Use when the user runs /HSK-HTML-MAIN.
user-invocable: true
---

# HSK-HTML-MAIN

One HSK 2.0 paper, level 3, 4, 5, or 6. Produce the three outputs below, in this order. The last output is the HTML: one listening page and one reading page. The HTML is last because the reading page does not write its own explanation: after 交卷, 解析 says why the keyed choice fits and why each other choice does not, and those sentences are copied from `{code}-阅读解析.docx`.

Paper deliverables go in the paper's own folder. This skill's files, including the notes builder, stay in `/Users/yinshijin/Desktop/我的 skill/HSK-HTML-MAIN`.

## Spans

The level is the digit in the paper code. Listening questions are 1–40 (level 3), 1–45 (level 4), 1–45 (level 5), and 1–50 (level 6). Reading spans and how to split them are in [references/paper-map.md](references/paper-map.md). Listening and writing stay out of the reading-notes file.

## 1. Reading notes

Write `{code}-阅读解析.docx` with this skill's builder. The notes are English. Chinese stays in the word table, the answer line, and the quotations inside a sentence. The finished file matches `H31008-阅读解析.docx`, `H41009-阅读解析.docx`, `H51553C-阅读解析.docx`, and `H61001-阅读解析.docx`. The builder writes the banner, the intro, the part line, the headings, and the table styling. Leave the docx unedited after the script writes it.

The builder's blocks have no border and no page header. English is Calibri. Chinese is Songti SC. A one-question unit is titled `Question N`. A range is `Questions N–M`.

1. Read the reading section of the paper PDF. Use `pdftotext -layout` when the PDF has a text layer. When that text is empty, read the pages as images and transcribe the reading section before writing notes. Copy every reading answer from the key. The `key_source` string names that file, for example `the printed answer page: H41009卷答案.pdf`. Stop and ask when there is no key. Done when the reading questions and the key answers are both written down.
2. Split the reading with [references/paper-map.md](references/paper-map.md). One unit is one task that shares a passage, a word bank, or a sentence bank. A single 病句 item or a single short passage is its own unit. Done when every reading question number sits in exactly one unit, in order, and the groups match the passages printed on this paper.
3. Look up 2012 levels with this skill's script. `--segment` longest-matches a unit's Chinese. Bare words look up one entry. A word's level is the number the script prints. Keep the first time a word appears. The workbook is `HSK-2012官方原表.xlsx`; the script already points at it.

```bash
python3 "/Users/yinshijin/Desktop/我的 skill/HSK-HTML-MAIN/scripts/hsk_vocab.py" --segment "这段原文"
python3 "/Users/yinshijin/Desktop/我的 skill/HSK-HTML-MAIN/scripts/hsk_vocab.py" 空调 例如 相约
```

Done when every word that will go in a table has been looked up in this run.
4. Write `notes.json` in the shape of [references/unit.md](references/unit.md). The summary, the title, the why-paragraph, and each wrong row are the part you write. Done when every unit has a summary, the vocabulary rows are in reading order and inside the band for that level, every question has a why-paragraph, and every wrong choice required by the paper map has a row. An HSK 4 ordering item has exactly two wrong orders.
5. Save the JSON under `/tmp` and build into the paper folder:

```bash
python3 "/Users/yinshijin/Desktop/我的 skill/HSK-HTML-MAIN/scripts/build_notes.py" /tmp/H41009-notes.json -o "/path/to/paper/H41009-阅读解析.docx"
```

The script checks the full question span, the level of every listed word, and the two-order rule. A non-zero exit means the JSON is wrong; fix the JSON and run it again. The output name is `{code}-阅读解析.docx` beside the PDF. When that file already exists, stop and ask before replacing it. Done when the script prints `wrote …` and the path is the paper folder.
6. Open the docx and check the first unit, one middle unit (a word bank or an ordering item when the paper has one), and the last unit. Done when those answers match the key, the question numbers run through the whole reading span with nothing missing, and the file contains no listening and no writing.

Stop after this step when the user asked only for the notes.

## 2. Answer PDF and listening script

Download the answer-key PDF and the listening-script PDF into the output folder before any HTML is written. The listening page is written from these two files. A missing recording does not matter and does not delay this step.

Look beside the paper first. When the only source is one booklet, split the printed answer pages into `{code}答案.pdf` and the printed listening-script pages into `{code}听力材料.pdf`. Leave the question pages as `{code}.pdf`. When the two files are not on disk, download them and save them under the names already used in that folder: `{code}卷答案.pdf`, `{code}卷听力材料.pdf`, `{code}答案.pdf`, or `{code}听力材料.pdf`.

Stop and ask only when the answer key or the listening script still cannot be obtained. Done when both files are in the output folder and the reading letters in the key match the docx.

Do not download the listening recording. Do not open YouTube or any other site to fetch it, and do not retry a failed audio download. If an mp3 or m4a is already on disk, next to the paper, in the output folder, or at a path the user gives, keep that file and its format. If it is not, leave the audio for later and continue.

## 3. HTML

Write the HTML only after the docx from step 1 exists and the answer key and the listening script from step 2 are in the output folder. Write the listening page from the script and the key even when no recording is available.

When a recording is already on disk, embed that file. When it is not, embed a short silent placeholder, about one second, generated locally. The login line, the section line, and the player label say `占位音频，没有考试内容`. Do not synthesize speech, and do not present the placeholder as the exam recording. Say in the final reply that the player is a placeholder.

When the user later supplies the recording, put that file into the listening HTML that already exists. Replace only the embedded audio. Keep an mp3 as mp3 and an m4a as m4a, and match the player MIME to that format. Remove the placeholder wording. Do not change the questions, the notes, or the QUIZ_ID, and do not rebuild the page.

Two Trimulia pages, in the paper folder:

- `{code}-听力-带有答案解析-可输出 PDF-三一-{YYYYMMDD}.html`
- `{code}-阅读-带有答案解析-可输出 PDF-三一-{YYYYMMDD}.html`

Shells that already include 输出:

- HSK 3 listening and reading: the H31008 pages in `H31008（NO.1）` whose names contain `可输出 PDF`
- HSK 4 listening: `H41008(NO.2)/H41008-听力-带有答案解析-可输出 PDF-三一-20261008.html`
- HSK 5 listening and reading: the H51008 三一 pages in `H51008(NO.3)` dated 20261006

Those five paths are under `/Users/yinshijin/Desktop/HSK2.0词汇-三级至六级/`. Copy the shell of the same level and the same section. HSK 4 has no reading shell with 输出 yet: copy an HSK 4 Trimulia reading page and add 输出 from [references/pdf-export.md](references/pdf-export.md). There is no HSK 6 HTML yet. The first HSK 6 page is copied from the H51008 page of the same section, then the item bank, the span, and the PDF identity strings are replaced. Do not create an HSK 6 page until a paper is in hand.

Replace the item bank from the paper, the key, and the listening script. Keep the Trimulia login (SEKOLAH KRISTEN TRIMULIA / 印尼万隆基督教三一学校, red `#b71c1c`) and the Trimulia Apps Script. A new page gets a new QUIZ_ID. Leave every 荣星 file untouched.

Reading `NOTES` come from the docx, one item at a time. `why` becomes `explain`. Each wrong row becomes one line of `wrong`: `letter  text — why`. The easy-mistake line becomes `trap`. Chinese stays inside the quotation and the gloss. The letter on the page is the letter in the key. When the docx letter and the key disagree, keep the key and rewrite `explain` so it argues for that letter.

Listening `NOTES` are written from the listening script and the key. They use the same fields plus `turns`. They are not in the reading-notes file.

Analysis stays hidden until 交卷. After 交卷 the page shows the score, posts `studentName`, `studentClass`, `score`, `total`, and `switchCount`, and 输出 can download the PDF. The download does not post a second row. Read [references/pdf-export.md](references/pdf-export.md) and include that button on every new page.

When a page already exists and only 输出 is missing, edit that file in place. Keep the item bank and the QUIZ_ID.

Done when both pages open, the keyed answers score full marks, one deliberate wrong answer scores one less, 输出 is refused before submit, and after submit it downloads the PDF named in the PDF reference. Intercept the school post during that check.
