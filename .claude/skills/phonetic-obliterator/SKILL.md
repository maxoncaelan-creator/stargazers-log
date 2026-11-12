---
name: phonetic-obliterator
description: SEO-safe phoneme reduction. Finds the best search keywords already in a text with DataForSEO, locks those phrases, then rewrites everything else to cut its phoneme count by a set level (low 20%, medium 40%, high 60%), checked with CMU Pronouncing Dictionary counts. Use when the user asks to "phonetically obliterate" a text, cut its phonemes while keeping keywords, or invokes /phonetic-obliterator. Arguments are the level (low, medium or high; default high), optional "whimsy", optional location (default United States), and the text.
argument-hint: "[low|medium|high] [whimsy] [location] <text>"
---

# Phonetic Obliterator

Shortens a text by **phonemes**, not words, while keeping the words searchers use.

| Level | Reduction of unlocked phonemes |
|---|---|
| low | 20% |
| medium | 40% |
| high (default) | 60% |

The reduction applies only to phonemes **outside** the locked keyword phrases. Locked phrases are never changed, so the reduction across the whole text comes out a bit lower. Report both numbers.

The counter is `scripts/phonemes.py` in this skill's folder (`.claude/skills/phonetic-obliterator/scripts/phonemes.py`). Use it for every count. Never estimate phonemes by hand.

## Step 0: Setup

1. Run `python3 -c "import cmudict"`. If that fails, run `pip install cmudict`.
2. Parse the arguments:
   - **Level:** low, medium or high. The default is high.
   - **Whimsy:** apply it if the word appears.
   - **Location:** default United States (`location_code` 2840, `language_code` "en").
   - **Text:** the rest of the arguments, or what the user pasted. If no text is given, ask for it.
3. Split off the parts that should not be counted or changed: headers (e.g. "🪰 DID YOU KNOW?"), sign-offs/bylines (e.g. a brand name at the end), emojis and hashtags. Keep them as they are and put them back at the end.
4. Write the countable body to `original.txt` in the scratchpad directory.

## Step 1: Phonetic transcription

Run `python3 phonemes.py count original.txt --ipa`. This prints every word with its IPA and ARPAbet spelling plus the phoneme total.
- The script splits words it can't find into two dictionary words (lampshade becomes lamp + shade).
- If it still stops with "No pronunciation for", add each missing word with `--pron WORD=ARPABET` and give stress digits on the vowels, e.g. `--pron housefly="HH AW1 S F L AY2"`. Reuse the same `--pron` flags on every later call.

## Step 2: Keyword research (DataForSEO)

Load the DataForSEO tool through ToolSearch (`select:mcp__DataForSEO__api_request`) if it isn't loaded yet. If DataForSEO is unavailable or needs sign-in, tell the user. Offer to continue with no locks, or with phrases they choose. Don't make up search volumes.

1. **Make candidates.** Pick 15–25 search phrases that someone looking for this text's content might type. Include:
   - Phrases taken from the text, normalized to how people search. "lesser houseflies" becomes "lesser house fly"; "attracted to the light" becomes "flies attracted to light".
   - Question forms ("why do flies fly in circles").
   - Short head terms.
2. **Get volumes.** POST `/v3/dataforseo_labs/google/keyword_overview/live` with `[{"keywords":[...], "location_code":..., "language_code":...}]`.
3. **Optional expansion.** For the two strongest seed terms, POST `/v3/dataforseo_labs/google/keyword_suggestions/live` with `{"keyword": seed, ..., "limit": 20, "order_by": ["keyword_info.search_volume,desc"]}`. Score any new phrases.
4. **Choose phrases to lock.** A keyword can only be locked if its wording **already appears in the original text**, as a phrase of consecutive words. Small changes in plural, articles or spacing are fine: the keyword "lesser house fly" matches the text "lesser houseflies". Lock the **text's wording**, not the keyword's.
   - Rank matches by search volume. Low keyword difficulty breaks ties.
   - Skip matches under about 30 searches a month unless nothing better matches.
   - Usually lock 1–4 phrases.
   - Don't lock a phrase so long that it leaves too little to cut.
5. Show a table: keyword | volume | difficulty | found in text? (quote the wording) | locked?

## Step 3: Set the budget

Run:

```
python3 phonemes.py target original.txt --level <level> --lock "<phrase 1>" --lock "<phrase 2>"
```

It prints the locked phonemes, the unlocked phonemes and the **unlocked budget**: the most phonemes the rewritten unlocked text may use.

## Step 4: Rewrite

Rewrite the body to fit the budget:
- **Locked phrases:** keep each one word-for-word, in the same order, and the same number of times. They may move to a new sentence, but their words don't change.
- **Facts:** keep the core facts and the main point. Drop filler, hedges and repeated ideas first.
- **Cheap words:** prefer words with fewer phonemes ("seen" over "noticed", "spin" over "reversing"). Contractions help.
- **Rhythm:** keep it readable and natural, never a word list.
- **Whimsy (if requested):** get it from word choice ("twirl", "dizzy love waltz", "a lady drops by"), not from added length. It has to fit the same budget.
- **Specific words the user asks to keep:** treat them as extra locks and add a `--lock` for each.

Write the draft to `candidate.txt`, then run:

```
python3 phonemes.py check original.txt candidate.txt --level <level> --lock ... [--pron ...]
```

If the result is FAIL, edit the draft and run the check again. Cut more when the reduction is under target; add words back when it is over. Repeat until it prints PASS (within ±3 points of target). Stop after 6 tries and report the closest version.

## Step 5: Output

1. The final text, with header, emojis and sign-off put back. Mark locked phrases with 🔒 and bold **only** in the preview. Also give a clean, copy-ready version with no markers.
2. Stats:
   - original phonemes = locked + unlocked
   - new phonemes = locked + unlocked
   - reduction of unlocked phonemes (the level target)
   - overall reduction
3. The keyword table from Step 2.
4. Things to flag:
   - **Unused high-volume keywords:** ones that weren't in the text and so couldn't be locked. Offer to work them in.
   - **Exact-match tradeoffs:** places where the locked wording differs from the searched keyword, and switching would mean changing a lock.
   - **Location:** say which one was used.
   - **Pronunciation:** CMUdict uses one General American pronunciation per word, so other accents change counts slightly.
5. Point to the IPA transcriptions of both versions (`count --ipa`) in the scratchpad. Give full absolute paths.
