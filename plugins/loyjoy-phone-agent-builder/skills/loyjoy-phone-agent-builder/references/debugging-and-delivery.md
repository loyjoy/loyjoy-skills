# Debugging, layer routing, side workflows, and the delivery checklist

Reference for `loyjoy-phone-agent-builder`. Read when diagnosing test-call problems and before handing anything over.

## Debugging workflow

When test calls show problems, diagnose in this order before changing anything.

1. **Reproduce.** Get the recording and the transcript. Note where the failure happens (greeting, first user turn, mid-call, end). In Connected mode read the actual live prompt via `process_get_xml_grep` first. A surprising number of reported bugs are a prompt state nobody expected to be live.
2. **Classify the layer** using the table below. Most reported "prompt bugs" are not prompt bugs.
3. **Fix at the right layer.** Never patch retrieval, VAD, or telephony with prompt language.
4. **Find the cause before adding a rule** (Entfernen vor Verbieten).
5. **Suspect your own last edit first.** A new symptom right after a change is most likely caused by that change.
6. **Ask whether the symptom depends on call length.** Correct early, wrong late points at accumulated context, not a missing rule.
7. **Change one rule at a time**, then run the anticipation pass over the affected scenarios (see Antizipation statt Testanruf in `SKILL.md`). Never substitute a text chat evaluation for a voice test.
8. **Declare nothing fixed without a call.** Where real calls are not available, report the change as applied and the fix as unverified, with the scenarios that should be called first.

### Layer-Zuordnung

| Symptom | Layer | Prompt-fixable? |
| --- | --- | --- |
| Agent interrupts itself, hears its own audio | Telephony / echo cancellation | No |
| Long pause after caller stops speaking | VAD `silence_duration_ms`, or model latency | No. Lower the VAD value, consider semantic VAD or a lighter model |
| Agent interrupts the caller mid-sentence | VAD threshold too low | No |
| Agent keeps talking when interrupted | Barge-in disabled or suppressed by echo | Partly: break long readbacks into short blocks so turn boundaries occur more often |
| Greeting can be interrupted | VAD or front-end timing | No |
| Poor recognition on hands-free car calls | Road noise, echo, AGC | Marginally: shorter questions |
| Spoken compound numbers arrive with inserted zeros | Number normalization in transcription | Partly: question framing and interpretation rules. Fixed by deterministic normalization, DTMF, or a model with better alphanumeric recognition |
| Stray characters from other scripts, language drift mid-call | Recognition locale not pinned | Backstop only (Sprache und Anrede fixieren) |
| Caller ID wrong on transfer, DTMF unhandled, session restarts mid-call | Telephony | No |
| Hallucinated URLs, generic instead of specific answers, prices not retrievable | Knowledge index or crawler | Partly: Preis- und Zahlendisziplin limits the damage, it does not create the data |
| Missing, superfluous, or misnamed tools | Tool configuration | No. Fix the configuration |
| Correct early in the call, stale later | Standard prompt (context reuse) | Yes, via a declared override plus a standard change |
| Weak instruction following on a small model | Model | No. Consider an upgrade (Modell festlegen) |
| Unsolicited narration, commentary leakage, literal example matching on a reasoning model | Model generation | Partly: cut example lists, tighten channel usage. Verify against the model version |
| Calls without user input missing in analytics, empty CSV exports, missing or cut recordings, transcript and audio misaligned | Platform / pipeline | No |
| Rule missing, contradictory, or unclear | Prompt | Yes |

Name not-prompt-fixable items explicitly when reporting, route them to engineering, and keep prompt work on what the prompt can address.

## Scenario matrix für die Antizipation

Run all of these before every delivery. Add one row per configured use case. The rules for the pass are in `SKILL.md`, Antizipation statt Testanruf.

Run all of these. Add one row per configured use case.

| # | Scenario | What to check |
| --- | --- | --- |
| 1 | Happy path per use case | goal reached, exit transition fires, no section re-enters |
| 2 | Caller states the anliegen in the first utterance | no entry question, no repeated greeting |
| 3 | Anliegen unclear mid-call | classification without greeting and without the entry question |
| 4 | Number capture, digits stated cleanly | one field, block-wise readback, done after confirmation |
| 5 | Number capture, compound number ("einhundertachtundzwanzig") | accepted, not rejected, magnitude read correctly |
| 6 | Number capture, correction after readback | value replaced, not extended; "nein" not parsed as "neun" |
| 7 | Caller names data already given earlier | pre-fill fires, field not asked again |
| 8 | Emergency trigger mid-flow | flow interrupted, number spoken from the prompt, no tool call in between |
| 9 | Transfer request inside business hours | offer, consent, then transfer |
| 10 | Transfer request outside business hours | transfer never named, callback or number instead |
| 11 | Factual question late in a long call | fresh search, no reuse of earlier context |
| 12 | Price question with a result containing no price | fallback sentence, no calculation, no estimate |
| 13 | Question outside scope (competitor, small talk) | polite decline and steer back, no comparison |
| 14 | Caller volunteers sensitive data | not recorded, single mention that it may not be |
| 15 | Unintelligible audio, twice in a row | clarification, then escalation, no loop |
| 16 | Ambiguous end signal ("okay", "mhm") | clarification turn, no hangup |
| 17 | Clear end signal | farewell spoken in full, then hangup |
| 18 | Caller speaks another language | language rule holds, or the agreed multilingual behavior |
| 19 | Repetition across turns | acknowledgments and closings vary |
| 20 | Tool named in the prompt is unavailable at runtime | no invented success claim |

## Side workflows

### Customer feedback analysis

When a customer sends a spreadsheet, document, or mail with bug reports and observations, structure the response in four buckets:

1. **In Prompt lösbar**: each item with the concrete prompt change, and whether it is a removal, a narrowing, or a new rule.
2. **Tool-Konfiguration**: items requiring a tool to be activated, deactivated, or renamed.
3. **Außerhalb des Prompts**: VAD, audio, transcription, pipeline, retrieval, telephony, model. Route to engineering.
4. **Zusatz-Wünsche**: feature ideas needing product decisions.

Lead with the highest-severity finding even when the customer did not report it. Safety defects and legal exposure outrank the reported list. Deliver as a table or short numbered list scannable in under a minute, with a short paragraph of context above.

### Change-proposal Word document for customer review

- Title, date, and the realtime model the prompt is written for.
- Two to four sentences on the source of the changes (workshop, feedback, log analysis).
- Overview table: feedback item → proposed prompt action → type (removal / narrowing / new rule / tool config).
- Full updated prompt with new or changed sentences highlighted in yellow (color code 10), removed text struck through in red. In Connected mode derive this from `process_diff`, not by hand.
- Appendix listing items NOT addressed in the prompt (engineering and tool-configuration scope).
- Measured prompt size before and after.
- The anticipation matrix as the test script, with the open risks ordered by severity.
- One-paragraph recommendation on next steps (review, publish, test call, observe for two to three days).

Keep it under five pages. Customers read short documents.

### Stakeholder mail

- One-sentence acknowledgment of their input.
- Numbered list, one short bullet per item: what changed plus a one-clause reason.
- A separate block for what you need **from them**, phrased as concrete decisions, not open questions.
- A separate block for what is still open on your side, so they see it is tracked.
- One sentence on the next step, ideally an invitation to retest the exact scenario they reported.

Match the form of address used in the thread. Du with customer teams once first-name basis is established, Sie in early contacts and regulated verticals.

### Promoting a mechanic into the standard prompt

When the same mechanic has been written into a second tenant's custom block, or when a bug's cause sits in the standard, it belongs in the standard. Deliver one consolidated proposal with:

- The finding: current wording, the failure mode, and where it was observed.
- The proposed wording, tenant-independent and channel-specific.
- What is deliberately **not** part of the proposal, with the reason. Over-correction is the main risk.
- Consequences and trade-offs, including latency, tool-call volume, and prompt size.
- The custom blocks that already carry a version or a stopgap override, so duplicates get removed.
- Which tenant-specific parameters remain in the custom block.
- The open technical questions for engineering, collected in one place.

Order by priority, not by discovery order.

### Setup instructions for tenants without MCP access

1. Create the agent or new version in the tenant.
2. Confirm the configured realtime model matches the one the prompt was written for.
3. Paste the standard prompt if not already in place.
4. Paste the custom block.
5. Configure the tools, including deactivating the ones flagged as superfluous.
6. Configure the telephony number and routing.
7. Publish, then work through the anticipation matrix as a call script.

Pack the prompt as a `.txt` attachment to avoid mail-client formatting breakage. Add a short screen recording if the customer team is new to the platform.

## Quick checklist before delivering a custom block

1. Is the target realtime model confirmed, stated in the delivery, and is the prompt calibrated for it?
2. Does Persona state audience, tone, language, form of address, pacing, and length per turn, with the language binding?
3. Is there a Notfall-Vorrang section where the vertical needs one, with triggers and numbers defined only there and no tool call between trigger and number?
4. Is the greeting placement clarified, and is the opening question absent as a standalone instruction?
5. Is the mid-call "anliegen unclear" case covered without a greeting?
6. Is the Zielgruppen-Erkennung implicit or one clarification, never a bureaucratic first question?
7. Does every use case have a goal, sample phrases, and an explicit exit transition?
8. Is every stateful capture a numbered flow with an explicit "field is done" step, and are preconditions before the steps?
9. Do number captures follow Ziffernfolgen: whole sequence as one field, any input form accepted, block-wise readback, no digit counting, replace never extend, negation priority?
10. Is there a recap before any final action, or, if deliberately dropped, no remaining reference to one?
11. Is the search discipline free of contradictions between must-search and no-search, and is context reuse across turns excluded?
12. Are price rules tied to the content of the result, with calculation forbidden?
13. If a time-dependent decision exists: exactly one unambiguous hours table, telephone hours only, and the check as a gate before the offer?
14. Has every tool an assigned eagerness class, does it exist in the tenant with an exactly matching name, and has every superfluous tool been flagged for deactivation?
15. Are escalation triggers concrete and countable, with a preamble before the handoff?
16. Is the unclear-audio rule present, with no sound effects and no onomatopoeia?
17. Are sample phrases present per state, with an anti-lock-in line and a variety constraint?
18. Are sensitive data forbidden via a closed negative list, including what to do when volunteered?
19. Is the date dynamic, not hardcoded?
20. Is the end-of-call discipline defined?
21. Is any rule from the standard accidentally duplicated? If yes, remove it from the custom block.
22. Is every behavior defined exactly once, does every cross-reference resolve, and does every key term have exactly one meaning?
23. For every change this round: was a cause removed where one existed rather than a negative rule added, and was every superseded formulation deleted rather than left in parallel?
24. Is logic written in words, with no pseudocode, and are bullets used instead of paragraphs?
25. If test mode is active: does the test-mode section list every place that must change to switch it off?
26. Did `scripts/prompt_check.py` run, are all ERROR findings fixed, is every accepted warning justified in the delivery, and was the self-critique pass done?
27. Was the anticipation pass run over the full scenario matrix, are all defects fixed, and are the remaining risks listed as predictions rather than results?
28. Connected mode: XML round-trip identical after every write, blocking and `LOCALE_NOT_MAINTAINED` findings reviewed, `process_diff` reviewed, and publication status, telephony setup, and the real voice test reported separately?

