# Conformance with the OpenAI Realtime prompting guide

Reference for `loyjoy-phone-agent-builder`. Read before every delivery and on every audit.

## Konformität mit dem OpenAI Realtime Prompting Guide

OpenAI's realtime prompting guide is the reference for GPT-Realtime prompts. Check every custom block against it, and state deviations deliberately instead of drifting into them.

### Section order

The guide's order is Role & Objective, Personality & Tone, Context, Reference Pronunciations, Tools, Instructions / Rules, Conversation Flow, Safety & Escalation. The LoyJoy custom block maps onto it as follows, with the two LoyJoy-specific deviations declared:

| Guide section | LoyJoy custom block |
| --- | --- |
| Role & Objective | Persona, Ziel |
| Personality & Tone | Persona (tone keywords, Sie/Du, pacing, length per turn) |
| Context | Wissensnutzung, Erreichbarkeit |
| Reference Pronunciations | Override gegenüber Standard, or its own section |
| Tools | Tools |
| Instructions / Rules | Scope und Negativliste, Datenschutz, Edge Cases |
| Conversation Flow | Use Cases, Datenerfassung, Gesprächsabschluss |
| Safety & Escalation | Notfall-Vorrang, Einwandbehandlung / Eskalation |

Declared deviations:
- **Notfall-Vorrang sits near the top, not at the end.** Safety routing must outrank every business flow, and a section the model reads last loses ties against an active flow.
- **Tools and overrides come before Persona.** The LoyJoy custom block is appended to a standard prompt, so the first thing it must settle is what the standard said that no longer applies.

### Formatting rules from the guide

- Short bullets outperform long paragraphs. Convert any paragraph of rules into bullets.
- Capitalize the few key rules that must not be missed. Use it sparingly; capitalizing everything removes the signal.
- Write logic in words, never as pseudocode. "IF x > 3 THEN ESCALATE" becomes "wenn mehr als drei Versuche gescheitert sind, übergib an einen Menschen".
- One topic per section. A section that carries two topics gets split, not extended.
- Ambiguous, conflicting, or unclear instructions degrade realtime models measurably. Resolving a contradiction beats adding a rule.

### Guide elements that are easy to miss

Check these explicitly on every audit. Each is cheap to add and each shows up as a real call defect when missing.

1. **Sample phrases per conversation state**, with an explicit anti-lock-in line: the examples are inspiration, the agent varies them. Without the anti-lock-in line the agent repeats the examples verbatim for the whole call.
2. **Pacing instruction**: deliver the audio fast without sounding rushed, and change only the speed, not the content.
3. **Unclear-audio rule**: respond only to clear audio or text; on ambiguous input, background noise, silence, or unintelligible speech, ask for clarification in the caller's language. Use the word "unintelligible" rather than "inaudible"; the guide reports a measurable difference.
4. **No sound effects or onomatopoeia** in the output. Without it, models occasionally produce hums and background noises.
5. **Per-tool eagerness class** (see Pattern: Tool-Eagerness und Bridging).
6. **Explicit escalation triggers** (see Pattern: Eskalations-Trigger).
7. **Exit criteria per conversation state**, minimal and concrete.
8. **Self-critique pass before delivery** (see Prompt-Budget und Redundanzprüfung, step 5).

### Where LoyJoy deliberately departs from the guide

- **Digit readback.** The guide recommends reading each character separately with hyphens and repeating the sequence exactly. LoyJoy reads back in blocks of two to three digits with a sentence boundary after each block, because block-wise readback survives barge-in and gives the caller natural interruption points on German telephony. The "repeat exactly, invent nothing" part of the guide rule still applies.
- **Tool confirmation.** The guide favors proactive tool calls without confirmation. LoyJoy requires consent before a transfer, because an unannounced transfer is the most frequent complaint in German B2C calls. Read and search tools stay proactive.
- **No preamble on sub-second tools.** The guide always asks for a preamble before a tool call. Where LoyJoy knowledge lookups return in well under a second, a preamble adds a turn instead of hiding latency. Keep preambles for slow tools and for anything that might take more than about a second.

