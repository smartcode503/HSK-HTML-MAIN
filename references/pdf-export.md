# Score PDF

Every listening page and every reading page, levels 3, 4, 5, and 6, shows the score after 交卷 and then downloads a PDF. Copy the working block from a shell that already has it. The shells are listed in the skill. Change only the identity strings below.

## What the student sees

The button is `<button type="button" class="tool-btn" id="export-pdf" title="下载成绩单 PDF">输出</button>`, last in `.utility-inner`.

CSS, placed after the last rule:

```css
.utility-inner{padding-right:6.8rem}
#export-pdf{position:absolute;top:.42rem;right:.85rem;z-index:2;min-width:4.8rem;background:var(--sage-dark);color:#fff;border-color:var(--sage-dark)}
#export-pdf:hover{background:#304a35;color:#fff}
#export-pdf:disabled{opacity:.65;cursor:progress;transform:none}
#export-pdf:disabled:hover{background:var(--sage-dark);color:#fff;transform:none}
```

`.utility-bar` is `position:fixed`, so the button sits on the right of that bar.

Before submit, the click alerts and returns. Listening: `请先交卷。交卷后才能输出题目、解析和听力原文。` Reading: `请先交卷。交卷后才能输出题目、解析和阅读原文。` While the PDF is built the label is `生成中`, then it returns to `输出`.

Say so in the login line, the section line, the result line, and the footer: `交卷后，右上角「输出」可下载 PDF。`

## Timing

Next to `navigationAwayCount`, add `examStartedAt` and `examSubmittedAt`, both starting at 0.

Save `examStartedAt` with the progress object. On restore, `examStartedAt = data.examStartedAt || data.timestamp || 0`. After login, `if (!examStartedAt) examStartedAt = Date.now()`. In `gradeAndSend`, after the result line, `examSubmittedAt = Date.now()`.

A page that already has questions keeps its QUIZ_ID. Adding these fields does not change `quizVersion`.

## The file

Copy from the shell, up to but not including `function fitOneLine`:

- listening: `currentScore`, `formatDuration`, `examTimeBits`, `sectionName`, `pictureCaptionMap`, `questionPrompt`, `optionLines`, `displayChoice`, then `pdfFilename` through the click listener
- reading: the same timing helpers, `readingItem`, `choiceText`, then `pdfFilename` through the click listener

Replace the paper code, the level word (三级 / 四级 / 五级 / 六级), the question span, and the section labels. The filename is:

`{姓名}-{YYYYMMDD}-{HHmm}-{code}听力|{code}阅读-{score}分.pdf`

The name has the characters `\ / : * ? " < > |` and control characters removed. An empty name becomes `学生`.

`sectionName` follows the part headings printed on that paper. On H51008 listening: 1–20 第一部分, 21–30 第二部分, 31–45 第三部分.

`readingItem` must match that page's `DATA`. H31008 reading uses `matches`, `banks`, and `short`. H51008 reading uses `cloze` (46–60), `match` (61–70), and `long` (71–90). Copy the `readingItem` of the shell you copied. A shell from another level will throw when `DATA` has different keys.

Listening rows on H51008 are `[number, letter, option texts]`. The question line is the transcript turn that starts with `问：`, or, on a shared passage, the last turn of that item. HSK 3 and 4 rows may also carry a true/false mark and picture labels; keep the shell's `questionPrompt` when you copy an HSK 3 or 4 listening page.

Each PDF page is one A4 JPEG. The first page is the score sheet: school, paper, time, score, rate, duration, and page-switch count. Then every question, in order: the prompt, the options, 我的选择, 正确答案, 解析 (答案, 题型, 讲解, 其他选项, 易错点), and the reading passage or the listening transcript. A correct item is marked 正确. A wrong or blank item is marked 错误.

The click builds the blob in the page. On an iPad it uses `navigator.share` when that can share the file. Otherwise it downloads. The click does not call `fetch`.

## Check

Open the page in headless Chrome. Stub `window.fetch` before 交卷 so the school sheet receives no row. The real `sendScore` still posts `studentName`, `studentClass`, `score`, `total`, and `switchCount`, and treats `{ "result": "success" }` as 成绩提交成功.

Confirm all four:

- 输出 before 交卷 alerts and does not download
- the keyed answers score full marks, and one deliberate wrong answer scores one less
- the result line names 输出
- `buildScorePdf()` returns a blob whose first bytes are `%PDF-1.4` and whose `/Count` is at least 2, named as above

The H51008 三一 pages dated 20261006 passed this check on 2026-10-13: reading 44/45, 48 pages; listening 44/45, 44 pages. The 荣星 copies in that folder were left without 输出.
