# Pattern catalog, anti-patterns, and the custom-block skeleton

Reference for `loyjoy-phone-agent-builder`. Read when drafting or auditing a custom block. Section names referenced without a file belong to `SKILL.md`.

## Recommended section structure for the custom block

Proven order across verticals. Not every project needs every section.

1. **Override gegenüber Standard** (only if overrides exist: disabled knowledge tools, restricted tool whitelist, forced language, no context reuse, pronunciation)
2. **Tools** (available tools, usage rules per tool, eagerness class, confirmation behavior)
3. **Persona** (role, tone keywords, form of address, target audience, language, pacing, length per turn)
4. **Ziel** (one or two sentences on the success criterion for the call)
5. **Notfall-Vorrang** (before any business flow, if safety scenarios apply)
6. **Gesprächseinstieg** (first own sentence; clarify that the greeting is external)
7. **Erreichbarkeit** (time gate, if the agent decides between transfer and callback)
8. **Wissensnutzung** (when to search, when not to, price and figure discipline)
9. **Zielgruppen-Erkennung** (implicit, with concrete signal lists; or one short clarification if the distribution is mixed)
10. **Use Cases / Sub-Flows** (one labeled section per business flow, each with goal, steps, sample phrases, exit criterion)
11. **Datenerfassung** (numbered flows, digit-sequence handling, recap pattern)
12. **Einwandbehandlung / Eskalation** (objection phrases, escalation triggers and paths)
13. **Scope und Negativliste** (what the agent will NOT answer or do)
14. **Datenschutz** (sensitive-data negative list)
15. **Edge Cases** (unclear audio, abusive caller, silence, end-of-call signals)
16. **Gesprächsabschluss** (farewell text and tool sequence)

## Pattern catalog

Reusable patterns, each named so it can be referenced in conversation and read directly.

### Pattern: Tool-Eagerness und Bridging

Why: the gap between end-of-speech and the first audio token is the most damaging latency a caller perceives, and an undeclared eagerness class makes tool use erratic.

- Assign every tool exactly one class in the Tools section: **proaktiv** (call without asking, no preamble), **mit Vorankündigung** (one short line, then call immediately in the same response phase), **mit Zustimmung** (ask, call only after a clear yes).
- Default: read and search tools are proaktiv or mit Vorankündigung; anything that leaves the system (transfer, email, booking) is mit Zustimmung.
- Preambles are one to three words, varied, and describe the action, not the agent: "Moment bitte.", "Kurz nachgeschaut.", "Ich prüfe das." Never "Ich nutze jetzt mein Tool."
- Speak the preamble in parallel with the call, never sequentially. On reasoning models use the commentary channel for it.
- Skip the preamble on sub-second tools, on direct answers, on confirmations, and when audio was unclear.
- Never let bridging text claim success before the tool returns.

### Pattern: Sample Phrases mit Variety-Constraint

Why: agents fall back on the same acknowledgment, empathy phrase, and closing question, and sound robotic within three turns. Sample phrases fix the tone but lock the wording if not constrained.

- Give a small pool per function: acknowledgments, clarifiers, bridges, brief empathy, closers. Two to four each.
- Place state-specific phrases inside the use case they belong to, not in one global list.
- Always add the anti-lock-in line: the examples are inspiration, the agent varies them and does not repeat a sentence within a call.
- Forbid reuse of openers, empathy phrases, closing questions, and acknowledgment words across turns of one call.

### Pattern: Unklares Audio

Why: noisy lines, hands-free calls, silence, and background speech are the normal case on telephony, and an agent without an explicit rule guesses instead of asking.

- Respond only to clear audio or text.
- On ambiguous input, background noise, silence, or unintelligible speech, ask for clarification in the language the caller is speaking. Use "unintelligible" rather than "inaudible" as the trigger word; the wording measurably changes behavior.
- Forbid sound effects and onomatopoeia in the output.
- Define what happens after repeated unclear turns: escalate rather than loop (see Eskalations-Trigger).

### Pattern: Eskalations-Trigger

Why: without concrete triggers the agent either escalates on the first hesitation or never escalates at all, and the caller spends the call in a loop.

- List the triggers explicitly and countably: the caller asks for a human, a safety risk appears, severe dissatisfaction (repeated complaints, profanity), two failed tool attempts on the same task, three consecutive no-match or no-input turns, an out-of-scope or regulated request.
- Write the counts in words, not as pseudocode.
- Mandatory preamble before the handoff: acknowledge the wait, say what happens next, then call the handoff tool.
- Name the target of the escalation per trigger class. Outside business hours the escalation is a callback, not a transfer (see Erreichbarkeit als Gate).

### Pattern: Implizite Zielgruppen-Erkennung

Why: asking "are you a customer or a partner" sounds bureaucratic and reduces conversion in B2B contexts.

- Short signal list per target group, derived from how each group actually talks (own contract and claims versus commission and partner IDs).
- The default branch reflects actual call distribution. If the split is roughly even or unknown, ask one short clarifying question after the first utterance.
- Forbid the category question as the very first question.
- Keep signal lists free of terms that merely restate the category label.

### Pattern: Transfer-Anbieten statt direkt Durchstellen

Why: callers want control over whether and when they are put through. Even transparent transfers feel intrusive without a question.

- Offer the transfer with the destination number spoken aloud, ask for explicit consent, transfer only after a clear yes.
- If the receiving team has a short, memorable number, speak it actively even when a transfer tool exists. Many callers prefer to call back themselves.
- Outside business hours, never offer the transfer. Give the number and the hours and end politely.

### Pattern: Erreichbarkeit als Gate

Why: agents offer transfers outside business hours because the time check is written as a description rather than a precondition, and usually in several places at once.

- One section owns the opening hours and the check. Every use case that could transfer references it. Remove all other mentions.
- Write it as a numbered gate that runs **before** the transfer is offered or even mentioned. Outside the hours the agent must not name transfer as an option at all.
- The hours table must be unambiguous: one line per day, telephone hours only, no parenthetical alternatives, no on-site hours mixed in. A table with two candidate closing times per day cannot be resolved on a boundary case.
- Confirm the platform injects the current time of day, not only the date. If only the date is available, none of this is prompt-fixable.
- When resolving a contradiction in customer-supplied hours, state the resolution and ask for confirmation. A wrong closing time causes transfers into an empty office.

### Pattern: Step-by-step Datenerfassung mit Recap

Why: on the phone you ask one thing at a time. Voice transcripts are noisy; collecting in one shot produces wrong fields.

- Announce the capture once: "Damit unser Team Sie zurückrufen kann, brauche ich kurz einige Angaben."
- Then one field per turn, in priority order. A single question naming three fields is the worst possible ask, and disproportionately damaging on hands-free calls.
- Pre-fill from what the caller already said, including information inside compound words ("Stromzählerstand" carries the commodity). Make the pre-fill an explicit numbered first step; a passive "do not ask again for what was already said" does not fire.
- Read back high-precision fields immediately and ask "Ist das so richtig?", then wait. Number fields follow the Ziffernfolgen pattern.
- Recap all collected fields before the final action (email, booking) and ask for confirmation. If a project deliberately drops the recap, per-field confirmation carries the full weight and no other section may still reference a recap.

### Pattern: Ziffernfolgen erfassen

Why: numbers are the highest-risk field class on the phone, and the naive fixes make it worse.

Model the capture as a numbered flow:

1. Ask once, and ask for the individual digits in that one question. Ask for what the caller can see, not for an abstract value. "Lesen Sie mir die Ziffern auf dem Display vor" produces a digit sequence, "wie ist Ihr Zählerstand" produces a compound number. Framing the question is a cheaper lever than fixing the parse.
2. Let the caller state the whole sequence in one utterance. Do not interrupt, do not ask between digits, do not confirm single digits.
3. Accept whatever form arrives. Never reject a compound number and never repeat the request for digits here. A caller who ignores the instruction must not hit a dead end.
4. Read back once, in blocks of two to three digits with a sentence boundary after each block, then ask for confirmation. Repeat exactly what was given; never add, drop, or round a digit.
5. On confirmation the field is done. Move on. State this explicitly, otherwise the agent asks again.
6. Only on negation discard the value entirely and return to step 2, with an escalation phrase used nowhere else in the prompt, for example a request for a slower repetition.

Interpretation rules that accompany the flow:
- **The complete sequence is one field.** Otherwise the "one field per turn" rule is applied per digit and the agent confirms every single digit.
- **Replace, never extend.** The value is only ever set or replaced by a complete statement. Digits arriving in a confirmation turn are not appended.
- **Negation outranks digit interpretation.** German "nein" against "neun": at the start of an answer to a confirmation question, such a token is a negation.
- **Magnitude words are place values, not concatenated blocks.** Otherwise "einhundertachtundzwanzig" is rendered as 100 followed by 28. Two examples with the correct and the wrong reading are justified here.
- **Never state the number of digits and never validate by digit count.** Models count unreliably. A wrong count triggers a correction round on a correct value or rejects a valid number. Block-wise readback already lets the caller hear a spurious digit.
- Partial corrections are valid only when the caller names a position explicitly.

Honest limit: the compound-number misparse can happen in transcription, below the prompt. If the magnitude rule does not hold after two test calls, it is not prompt-fixable. Route it to engineering: deterministic number normalization or DTMF keypad entry are the real fixes. DTMF eliminates the error class and is the first question whenever number capture is central. A model with better alphanumeric recognition is the second (see Modell festlegen).

This pattern is tenant-independent and belongs in the standard voice prompt. Where it is in the standard, remove it from the custom blocks.

### Pattern: Notfall-Vorrang

Why: in utilities, insurance, and automotive contexts the agent receives calls about safety-critical situations. Sending those callers through a normal flow is harmful.

- Place the section before all use cases.
- Define the trigger class as any situation with risk to life, health, or property, with a handful of vertical-specific anchors.
- **The emergency numbers stand in the prompt text and are spoken from there, with no tool call in between.** An instruction to search the knowledge base before naming an emergency number is a serious defect. Check for it on every audit; it appears often because the general search-first rule gets copied into the emergency section.
- The agent interrupts any flow on these triggers, speaks the safety instruction first where one applies, then the number, digits individually.
- Only afterwards does it gently return to the original topic.
- Keep triggers and numbers in this section only. Use cases reference it.

### Pattern: Mandatory Search Trigger

Why: phone agents are eager and answer concrete questions from the system prompt instead of calling the knowledge tool, which produces outdated or invented answers.

- Default: if in doubt, search.
- Define the must-search class by property, not by enumeration: anything factual, current, priced, contractual, or configuration-specific.
- Give a short, closed whitelist of what may be answered without a search: greetings, repetition, the one-sentence company explanation, scope confirmation, and anything standing verbatim in the prompt such as emergency numbers and opening hours.
- **Check the must-search and no-search lists for items in both.** Opening hours and emergency numbers are the common copy artifact and produce erratic tool use plus needless latency.
- If several named tools exist instead of one generic one, say so explicitly. The model otherwise invents a generic name.

Kontext-Wiederverwendung as its own failure mode:
- A standard prompt may permit reusing retrieved context from earlier in the same call. This causes a distinct bug: the longer the call, the more accumulated context, the more often the model decides an earlier result already answers the new question and skips the search.
- The symptom is that early answers are correct and later answers are stale or subtly wrong. It is easily misdiagnosed as a retrieval problem, because retrieval was never invoked.
- The permission is worded backwards wherever it says "if it clearly answers the new question": it grants reuse exactly when the model feels confident, which is when it is most often wrong.
- Fix: narrow the permission in the standard so reuse is allowed only when the caller explicitly asks for the same information again. Add a declared override in the affected custom block as a stopgap.
- Do not overcorrect into "search before every reply". Confirmations, process questions, and clarifications need no search, and the added latency is the more expensive defect. The cut is at the new factual question, not at the turn.

### Pattern: Preis- und Zahlendisziplin

Why: invented prices are the most damaging hallucination class, because callers act on them.

- Tie the rule to the **content of the search result**, not to whether a result exists. The common failure is not an empty search but a result about tariffs containing no price, which the model then fills in.
- A price is spoken only when it appears as a figure in the retrieved result. No approximation, no example value, no range.
- **Forbid deriving a price by calculation** from base price and unit price.
- Give the fallback sentence and the exit: the price depends on tariff and consumption, followed by transfer or callback.
- If prices are poorly retrievable, say so plainly. Price data lives in tables, calculators, and PDFs and crawls badly. A curated price document beats any crawl tuning.

### Pattern: Tool-Routing nach Themenklasse

Why: with several knowledge tools (marketing site, docs, web search) the model picks unpredictably.

- Define a default for tenant-general questions, a switch condition (how-to questions go to docs), and when supplementary tools are allowed and how to treat their results.
- Forbid invented tool names.

### Pattern: Sprache und Anrede fixieren

Why: speech-to-speech models drift into another language mid-call, and into Du when knowledge sources use Du. Both are easy to overlook because specifying the form of address looks like it covers language.

- State the language as binding even when the caller speaks another language or a source is in another language, unless multilingual service is actually wanted. Decide that question explicitly.
- State the form of address as a hard constraint in Persona, with: even when sources, FAQs, or other inputs use Du, every answer is formulated in Sie, with no mid-answer switching.
- The real fix for language drift is pinning the recognition locale in the session configuration. The prompt rule is the backstop. Stray characters from other scripts in the transcript are always an engineering item.

### Pattern: Reference Pronunciation

Why: TTS engines mispronounce brand names, loanwords, and technical terms ("Lead" rendered as "Lied").

- List only terms that actually were mispronounced in test calls. Ten to twenty maximum.
- Form: "Sprich 'X' aus wie 'Y'". No IPA.
- One sentence per term. A positive instruction makes the negative counter-example redundant.
- Refresh as new errors appear; remove entries that no longer occur.

### Pattern: Sensible-Daten-Negativliste

Why: phone agents will collect any field they are told to. In regulated verticals this is legal exposure.

- Explicit "Frage NIEMALS nach" section with the concrete forbidden fields for the vertical.
- Place it near the top, not at the end.
- Say what to do when the caller volunteers such data: do not record it, mention once that you may not.
- One of the legitimate uses of negative rules. Keep it a closed list.

### Pattern: Datum dynamisch

Why: hardcoded dates go stale and produce wrong output the moment the date passes.

- Always use a date template variable. In LoyJoy: `${localDate()}` or equivalent.
- If templates are unsupported in custom blocks, agree on a refresh cadence and a calendar reminder.

### Pattern: Out-of-Scope Steering

Why: callers will ask about competitors, weather, generic chat.

- Define what is in scope, and what to do outside it: politely decline, steer back, optionally offer to pass the topic to a colleague.
- Competitor questions: never compare, never criticize. Steer to own value.
- Where a default or free tier exists, forbid recommending it proactively. It may be mentioned only if the caller asks for it or confirms they use it.

### Pattern: Greeting external

Why: in most LoyJoy setups the greeting belongs to the IVR or telephony layer. If the model also greets, callers hear "Willkommen … Willkommen".

- State it explicitly: the greeting is external, the agent's first own utterance is [exact sentence].
- **Never put the opening question into the prompt as its own instruction.** A line like `Frage: "Wie kann ich Ihnen helfen?"` in an intent-recognition section has its own trigger and re-fires whenever the agent returns to intent recognition, which the caller experiences as the call starting over. Write intent recognition as a classification task on the caller's utterance.
- Cover the mid-call case: when the anliegen is unclear later on, the agent asks about the concrete request without greeting and without repeating the entry question.
- If the restart symptom persists after this fix, look for a session restart in the telephony layer.

### Pattern: End-of-call discipline

Why: agents either hang up on an ambiguous "okay" or never hang up at all.

- Define unambiguous end signals ("Tschüss", "Auf Wiederhören", "Vielen Dank, das war's").
- Define ambiguous signals that require a clarification turn instead ("mhm", "okay", "alles klar").
- Require the farewell sentence to be spoken in full before the hangup tool is called.

### Pattern: Testmodus

Why: agents are tested against live telephony and live mailboxes before go-live. Ad-hoc test overrides scattered through the prompt are forgotten and cause real transfers and real customer mails.

- Put the switch in its own section at the very top, with an explicit on/off marker.
- Where an override has to sit at the point of action (tool section, transfer step, mail routing), keep it there, because the model needs it where it acts.
- In exchange, list in the test-mode section every place that has to change when switching it off. Two lines there save an incident at go-live.

### Pattern: Compliance-Hinweise

Why: EU AI Act disclosure and recording notices are legal requirements, not nice-to-haves.

- One-sentence AI disclosure in the external greeting or the agent's first own sentence. If asked, the agent confirms being an AI voice assistant of the tenant.
- Recording notice only if recording actually happens. Reference the data protection page rather than reading the full text.
- In regulated verticals (insurance, healthcare, finance), coordinate the exact wording with the customer's compliance team.

### Pattern: Wunschtermin statt Bestätigung

Why: appointment bookings on the phone often need internal approval. Communicating a confirmed appointment when a human still has to check creates legal and trust risk.

- Phrase the closing as passing on a preferred slot, not as a booked appointment.
- Send the internal handoff mail with an explicit "Wunschtermin" subject.
- Tell the caller the formal confirmation arrives separately.

## Anti-patterns

Each of these reliably hurts quality. The fix is in the named section.

1. **Negativregel-Akkretion (scar tissue)**: patching behavior with a counter-rule instead of removing its cause → Entfernen vor Verbieten.
2. **Duplizierte Regeln über Sektionen**: the same behavior defined twice; they drift and then contradict → Wartbare Prompt-Struktur 1, Redundanzprüfung.
3. **Konkurrierende Formulierungen**: a better phrasing added without deleting the old one → Hygiene rules.
4. **Beispiel-Inflation**: a long list of instances replacing a general rule. The model pattern-matches and fails on the unlisted case → Wartbare Prompt-Struktur 5.
5. **Bullet-Liste für einen Interaktionsablauf**: no order, no state, so the agent loops → Wartbare Prompt-Struktur 6.
6. **Terminologie-Kollision**: one phrase for several meanings, typically describing both caller and agent action → Wartbare Prompt-Struktur 8.
7. **Regeln auf unzuverlässigen Primitiven**: validation depending on counting, arithmetic, or length control → Ziffernfolgen.
8. **Pseudocode im Prompt**: IF/THEN notation instead of a sentence → `openai-guide.md`, Formatting rules.
9. **Constraint overload with "always" / "never" / "must"**: reasoning models follow them literally and get rigid → use precise scope.
10. **Bulk data capture**: several fields in one question → Datenerfassung.
11. **Re-asking already-captured fields**: make the skip an explicit step, not a passive rule → Datenerfassung.
12. **Hard rejection of caller behavior**: refusing input because the caller did not follow an instruction. A dead end is always worse than a degraded path → Ziffernfolgen step 3.
13. **Direct transfer without consent** → Transfer-Anbieten.
14. **Suchpflicht vor der Notfallnummer**: any tool call between an emergency trigger and the spoken number → Notfall-Vorrang.
15. **Entscheidungstabellen mit Mehrdeutigkeit**: an hours or pricing table with two candidate values per row → Erreichbarkeit als Gate.
16. **Kontext-Wiederverwendung über Turns**: answering a new factual question from context retrieved earlier. Degrades silently, only in longer calls → Mandatory Search Trigger.
17. **"Du darfst einfache Fragen aus dem Orientierungsblock beantworten"**: too vague, the model answers concrete pricing questions from memory → closed whitelist.
18. **Sequential bridging**: long preamble first, then the tool call. Adds latency instead of hiding it → Tool-Eagerness und Bridging.
19. **Bridging text claims success before the tool returns** → same section.
20. **Prompt-Regeln gegen überflüssige Tools**: telling the agent not to use a tool that should be deactivated → Tool-Inventar.
21. **Tool names in the prompt that do not exist in the configuration**: the model invents the name or fakes success → Tool-Inventar.
22. **No variety constraint**: robotic within three turns → Sample Phrases mit Variety-Constraint.
23. **Sample phrases without an anti-lock-in line**: the agent repeats the examples verbatim → same section.
24. **End-of-call on ambiguous signals** → End-of-call discipline.
25. **Hardcoded date** → Datum dynamisch.
26. **Chat patterns in a voice prompt**: markdown, emoji, long enumerations. The model reads brackets and stars out loud → Mandatory voice-output rules.
27. **Vague tone descriptors only ("sei hilfsbereit")**: add concrete tone keywords plus a verbose anti-example → Persona, Abschnitt 3 der Struktur oben.
28. **Prompt written before the model was fixed** → Modell festlegen.

## Appendix: template skeleton for a fresh custom block

```
# Modell: [gpt-realtime-1.5 | gpt-realtime-2.1 | ...], Reasoning Effort: [low | ...]

## Override gegenüber Standard
[only if needed: disabled tools, language override, no context reuse, pronunciation]

## Tools
- [exact tool name]: [when to use] [proaktiv | mit Vorankündigung | mit Zustimmung]

## Persona
Du bist der KI-Sprachassistent von [tenant]. Tonalität: [keywords]. [Sie/Du-Form].
Sprache: [language], verbindlich, auch wenn Quellen oder Anrufer eine andere Sprache nutzen.
Zielgruppe: [audience].
Antworte in ein bis zwei Sätzen. Sprich zügig, ohne gehetzt zu klingen.

## Ziel
[one or two sentences on the call success criterion]

## Notfall-Vorrang (only if applicable)
[trigger class + numbers spoken from here, no tool call + safety instruction + return to topic]

## Gesprächseinstieg
Die Begrüßung erfolgt extern. Du begrüßt nicht selbst, auch nicht später im Gespräch.

## Erreichbarkeit prüfen (only if transfer or callback decisions exist)
[one unambiguous hours table + numbered gate before offering a transfer]

## Wissensnutzung
[closed no-search whitelist, search for everything else, no context reuse,
 price only if it appears as a figure in the result]

## Use Case 1: [name]
[precondition, goal, steps, sample phrases, exit transition, references to shared sections]

## Datenerfassung (shared, referenced by use cases)
[pre-fill from what was already said, one field per turn,
 Ziffernfolgen flow for number fields, recap before the final action]

## Eskalation
[triggers: Wunsch nach Mensch, Sicherheitsrisiko, starke Unzufriedenheit,
 zwei gescheiterte Tool-Versuche, drei unverständliche Turns, Out-of-Scope
 + Vorankündigung + Ziel je Trigger]

## Scope und Negativliste
[what is in scope; what is NOT answered]

## Datenschutz
Frage NIEMALS nach: [closed list] + what to do when volunteered

## Edge Cases
[unklares Audio: nur auf klares Audio reagieren, sonst nachfragen; keine Geräusche;
 aggressiver Anrufer; Stille; Abschluss-Signale]

## Beispielformulierungen
[2 bis 4 je Funktion: Bestätigung, Rückfrage, Überleitung, Empathie, Abschluss]
Diese Beispiele sind Inspiration. Variiere sie und wiederhole keinen Satz im selben Gespräch.

## Gesprächsabschluss
[farewell text + tool sequence, mail only where a use case requires it]
```
