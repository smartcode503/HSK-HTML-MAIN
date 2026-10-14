# One unit

`scripts/build_notes.py` reads this JSON. It writes the banner, the intro (from `key_source`), the headings, and the tables. You write the title, the summary, the vocabulary rows, and every question. The block below shows the fields. A real file lists every reading question, so this block alone will not build.

```json
{
  "code": "H41009",
  "level": 4,
  "key_source": "the printed answer page: H41009卷答案.pdf",
  "units": [
    {
      "title": "Two names, a class, and Beijing",
      "questions": "46–50",
      "part": 1,
      "summary": "Two to five sentences.",
      "vocab": [
        {"word": "植物", "pinyin": "zhíwù", "english": "a plant", "level": "HSK 4"}
      ],
      "higher": [
        {"word": "负担", "pinyin": "fùdān", "english": "a burden", "level": "HSK 6"}
      ],
      "offlist": [
        {"word": "相约", "pinyin": "xiāngyuē", "english": "to agree to meet"}
      ],
      "items": [
        {
          "number": 46,
          "answer": "B",
          "answer_text": "植物",
          "pinyin": "zhíwù",
          "why": "One paragraph.",
          "wrongs": [
            {
              "choice": "A",
              "text": "篇",
              "mistake": "Collocation",
              "why": "One or two sentences."
            }
          ]
        }
      ]
    }
  ]
}
```

Omit `higher` or `offlist` when the unit has none. Omit `answer_text` and `pinyin` on an ordering item: `"answer": "ACB"`, and each wrong `choice` is an order such as `BAC` with `text` left empty.

The builder rejects a word whose level disagrees with `scripts/hsk_vocab.py`, a word in the wrong table for this paper, an off-list word that is actually on the 2012 list, a missing question number, and an HSK 4 part-2 item that does not have exactly two wrong orders.

## Title and summary

The title is a concrete scene in about three to eight words: `Two baskets of stones`, `A math exam, coffee, and thin clothes`. It names things in the passage.

The summary retells the Chinese in order, in two to five sentences. It includes the printed example when the unit has one. It does not give the answer letter.

## Vocabulary rows

Run `--segment` on the passage, the prompts, and the example. Keep the first time each word appears. Then add option words that have not appeared, in question order and in A-to-D order.

Keep a word only when its level is in this paper’s band (`references/paper-map.md`). Leave the others out.

On an HSK 5 or 6 paper, leave out a one-character word when a learner at that level already knows it and the question does not turn on it. H51553C left out 满, 重, and 够, which the list marks HSK 4. Keep the word when it is the answer or the explanation depends on it.

`offlist` is only for a word the question depends on that the lookup prints as off-list, such as 相约 and 精美 on H51553C. Do not list every unlisted character. On an HSK 6 paper this is the second table. There is no higher HSK band above 6.

Pinyin uses tone marks. A compound is closed (`zhíwù`). A neutral particle or a loose phrase takes a space (`lái de jí`, `bào míng`). 不 before a fourth tone is `bú`; 一 changes the same way.

The English is the sense this unit uses. Add a second sense, after a semicolon, only when the two senses are easy to mix up.

## Why the answer fits

One paragraph. Start from the line, the blank, or the question. Quote the Chinese that decides it, and gloss that piece in English. End on why the key is the choice that fits. For an ordering item, say which sentence has to come first and which link word forces the next one. For a 语病 item, name the error.

The paragraph does not open with the letter of the answer.

## Why the other choice fails

One or two sentences. Quote its Chinese. Say which other line or blank it belongs to, or what it would mean in this sentence.

Use one of these labels when it names the error. Coin a new label of two to four words only when none of these fits.

`Collocation`, `Similar-word mix-up`, `Wrong word class`, `Wrong time`, `Wrong focus`, `Wrong link`, `Wrong place`, `Wrong person`, `Wrong number`, `Wrong direction`, `Wrong tone`, `Opposite`, `Keyword trap`, `Half true`, `Scope`, `Too absolute`, `Point of view`, `Literal reading`, `Outside knowledge`, `Not in the text`, `Nearby-sentence trap`, `Does not answer`, `Looks odd`.

`Does not answer` is the printed example, already used. `Looks odd` is a grammatical sentence in an HSK 6 语病 item, so it is not the faulty one. The why-paragraph of that item still names the error in the faulty sentence.
