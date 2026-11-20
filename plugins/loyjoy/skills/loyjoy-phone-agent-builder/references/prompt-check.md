# Prompt checker specification

Reference for `loyjoy-phone-agent-builder`. The plugin ships no executable code. Before the first check of a session, write a throwaway checker script in the session working directory that implements this specification exactly, and run it on every iteration (see Prompt-Budget und Redundanzprüfung in `SKILL.md`). Never ship or commit the script. Do not perform these checks by hand.

## Interface

- Input: the custom block file (`custom.txt`), optionally the standard file (`standard.txt`), and a budget: `single`, `service` (default), `complex`, or a number `N` (target `N`, ceiling `N × 1.4`).
- Output: one line per finding, `[LEVEL] check message`, sorted ERROR, WARN, INFO, then by check; then `<n> Fehler, <m> Warnungen.` Messages are German and name the line number and the section.
- Exit code 1 when at least one ERROR exists, otherwise 0.

## Shared helpers

1. **Normalize** a sentence: lowercase, Unicode NFKD, drop combining marks, replace everything except `a-z0-9` and space with a space, split into tokens.
2. **Sentences**: per line, skip empty lines and lines starting with `#`; split on whitespace after `.`, `!`, `?`, `:`; strip leading/trailing ` -*+0123456789.)`; keep parts with at least 4 words, together with their line number.
3. **Jaccard** of two token lists: size of the intersection of the token sets divided by the size of their union (0 if either is empty).
4. **Containment**: share of the shorter token set contained in the longer one.
5. **Headings**: lines matching up to 3 spaces, 1 to 4 `#`, whitespace, title. The section name is the title without a leading `N.` or `N)` and without anything from the first `(`. Every line belongs to the nearest heading above it.
6. **Reference sentence**: contains, case-insensitively as a whole word, `siehe`, `vgl`, `wechsle in`, `nutze`, `gemäß`, `gemäss`, or `see`. Such a sentence delegates, it does not regulate.
7. **Template expression**: `${…}`.

## Checks

| Check | Rule | Level |
| --- | --- | --- |
| `size` | characters, words, tokens = characters / 3.0 (German, conservative). Budgets: `single` 800 / 1,500, `service` 2,000 / 3,000, `complex` 3,000 / 4,000. Over ceiling | ERROR |
| | Over budget | WARN |
| | Always report the measurement | INFO |
| `duplicate` | Compare every sentence (at least 3 tokens) with all earlier ones; stop at the first hit. Jaccard ≥ 0.95 | ERROR |
| | Jaccard ≥ 0.7 | WARN |
| | Containment ≥ 0.8 (partial duplicate; report the shorter sentence as contained in the longer) | WARN |
| `sections` | A section name used more than once | ERROR |
| | A shared section whose name starts with `datenerfassung`, `gesprächsabschluss`, `gespraechsabschluss`, `eskalation`, `erreichbarkeit`, `notfall`, `wissensnutzung`, or `einwandbehandlung` and whose name does not occur in the text outside its own heading | WARN |
| | List of all sections | INFO |
| `crossref` | Every match of (`siehe`, `vgl`, `vgl.`, `wechsle in`, `nutze`, `gemäß`, `see`, case-insensitive) followed by a capitalized phrase of 4 to 41 characters (letters, digits, umlauts, space, `-`, `/`); strip trailing `.,;:`. Warn when neither the target starts with a section name nor a section name starts with the target (case-insensitive) | WARN |
| `standard` | Only with a standard file; otherwise one INFO that the check was skipped. A custom sentence with Jaccard ≥ 0.6 to any standard sentence: delete it or declare it an override | ERROR |
| | Each of these terms occurring in both texts (case-insensitive): `markdown`, `emoji`, `begrüßung`, `begruessung`, `ziffer`, `buchstabier`, `wissenssuche`, `such`, `weiterleit`, `preis`, `sprache`, `abschluss`, `acknowledge`, `bridging`, `tool`, `datum`, `uhrzeit`, `locale` | INFO |
| `topics` | Per topic and section, count sentences that match the topic (case-insensitive prefix at a word boundary) and are not reference sentences. A section with at least 2 such sentences owns the topic. A topic owned by 2 or more sections | WARN |
| | Topic map of the topics owned by exactly one section, or a note that no known topic was found | INFO |
| `tools` | Find the section titled `Tools` or `Tool` (optionally numbered). Missing section | WARN |
| | Tool names: lines `- name:` / `- name –` / `` `name`: `` with a name of 3 to 41 characters from `a-z0-9_`. No names found | WARN |
| | A bullet line in the section without an eagerness class (`proaktiv`, `mit vorank…`, `mit zustimmung`, `proactive`, `confirmation`) | WARN |
| | A tool name that occurs only once in the whole text | INFO |
| `search` | No sentence matching the must-search pattern (word starting with `such`, `recherchier`, `nachschlag`, `knowledge`, `wissensbasis`) | WARN |
| | Forbidden pattern: `ohne such`, `nicht such`, `keine such`, `no search`, `ohne tool` (a sentence matching it counts as forbidden, not as required). A normalized word longer than 5 characters occurring in both a required and a forbidden sentence | ERROR |
| `format` | Inline markdown: `[text](url)`, `**`, `__`, or a backtick span of up to 40 characters; report the first occurrence only | WARN |
| | An emoji (U+1F000 to U+1FAFF, U+2600 to U+27BF) | ERROR |
| | Pseudocode after masking template expressions: `IF … THEN` within 40 characters, `==`, `>=`, `<=`, `&&`, `\|\|`, `{{`, or the word `ELSE` | ERROR |
| `primitives` | Validation by digit count: `anzahl der ziffern`, `zähl`, `zaehl`, `wie viele ziffern`, `digit count` | ERROR |
| `date` | A hardcoded date (`D.M.YY[YY]`) or a year `20NN` while no template expression containing `Date`/`date` exists | WARN |
| | A dynamic template expression (`${…` with a call to `formattedLocalDate`, `formattedLocalDateTime`, `localDate`, `localDateDayOfWeek`, `localDateDayOfMonth`, `localDateMonthOfYear`, `localDateYear`, `localDateTime`, `displayLanguage`, `clientLocale`, `arrayIncludes`, `arrayLength`, `toInteger`, `timestamp`, `timestampMs`) in the first 70 percent of the lines: it breaks the cacheable static prefix and belongs at the end | WARN |
| `flow` | A section with at least 3 bullet lines, no numbered line, and at least 3 state verbs (word starting with `frag`, `erfass`, `lies vor`, `wiederhol`, `bestätig`, `bestaetig`, `notier`, `prüf`, `pruef`, `warte`, `übernimm`, `uebernimm`, `sende`, `leite`) | ERROR |
| `variety` | Sample phrases (`beispielformulierung`, `sample phrase`, `beispielsätze`) without an anti-lock-in line (`variiere`, `wiederhole kein`, `vary`, `nicht wörtlich`) | ERROR |
| | No anti-lock-in line at all | WARN |

## Topic terms

Matched as case-insensitive prefixes at a word boundary. Extend the list when a tenant adds a topic; WARN is a pointer, not a verdict.

| Topic | Terms |
| --- | --- |
| Ziffern erfassen | `ziffer` |
| Preis | `preis`, `kosten`, `tarif`, `gebühr`, `gebuehr` |
| Suche/Wissen | `suche`, `sucht`, `suchen`, `wissensbasis`, `knowledge`, `nachschlag` |
| Transfer/Weiterleitung | `transfer`, `weiterleit`, `durchstell`, `durchverbind` |
| Datenschutz/sensible Daten | `datenschutz`, `sensibl`, `gesundheitsdaten` |
| Erreichbarkeit/Zeiten | `erreichbar`, `servicezeit`, `öffnungszeit`, `geöffnet`, `geoeffnet`, `geschlossen` |
| Sprache | `sprache`, `englisch`, `deutsch`, `fremdsprache` |
| Begrüßung | `begrüßung`, `begruessung`, `grüß`, `gruess` |
| Gesprächsabschluss | `gesprächsabschluss`, `gespraechsabschluss`, `verabschied`, `auf wiederhör`, `auf wiederhoer`, `tschüss`, `tschuess`, `aufleg` |
| Notfall | `notfall`, `notruf`, `gefahr`, `gefähr` |
| E-Mail | `e-mail`, `email` |
