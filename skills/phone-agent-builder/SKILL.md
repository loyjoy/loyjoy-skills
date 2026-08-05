---
name: "loyjoy-phone-agent-builder"
description: "Create and configure new LoyJoy phone agents in staging, and build, iterate, or debug their custom voice prompts. Covers the standard-plus-custom architecture, LoyJoy MCP workflows, model checks, maintainable prompt structure, tool reconciliation, common phone use cases, voice-specific testing, and the boundary between a configured process and a telephony-ready agent. Use for requests such as \"Erstelle einen vollständigen Phone Agent\", \"Phonebot Prompt\", \"Voice-Agent anpassen\", \"Custom-Prompt für Telefon\", \"Phone Agent Feedback umsetzen\", \"Telefonbot debuggen\", or \"Voice-Prompt optimieren\"."
---

# LoyJoy Phone Agent Builder

This skill captures the methodology, patterns, and debugging techniques developed across multiple LoyJoy phone-agent projects. It is the voice-specific counterpart to the `loyjoy-prompt-builder` skill (which covers chat agents). Use this skill whenever the work involves a phone agent, voice bot, or speech-to-speech assistant, regardless of vertical (insurance, utilities, automotive, retail, B2B sales, service hotline, etc.).

For chat agents (web chat, in-app chat, embedded widgets), use `loyjoy-prompt-builder` instead. Voice patterns (acknowledge-first, no markdown, spoken pronunciation rules, character-by-character digit confirmation, transfer with consent) and chat patterns (markdown links, bullet lists, link format consistency) do not translate between the two channels.

The skill is meant for internal LoyJoy use and for sharing with customers. It does not reference individual customer names. Patterns are written so they can be applied to any vertical.

## When to start

Invoke this skill when one of the following applies:
- The user wants to create or configure a complete phone agent in LoyJoy.
- The user wants to build a new phone-agent prompt from scratch.
- The user wants to optimize an existing phone-agent prompt based on test calls or customer feedback.
- The user wants to debug a specific misbehavior of a phone agent.
- The user wants to translate a workshop protocol, feature list, or use-case backlog into a working prompt.
- The user wants to produce a change-proposal document for a customer.
## Rückfragen vor Plan

Before producing a plan or a draft, decide deliberately whether to ask first. Drafting on wrong assumptions wastes more time than one round of questions.

Ask first when any of the following is true:
- The number of use cases, the target audience, or the success criterion of the call is not stated.
- Tool availability is unknown, or the brief names capabilities without naming tools.
- The source material is a raw workshop protocol, a feedback spreadsheet, or a meeting transcript, i.e. unstructured input with implicit priorities.
- Two plausible interpretations of the request would lead to materially different prompts.
- The change touches a live production agent and the desired blast radius is unclear.
Go straight to work when:
- The request is a narrow, well-specified single change ("Anrede auf Sie umstellen", "Notfall-Nummer korrigieren").
- The Ist-Stand is readable via MCP and the requested change is unambiguous against it.
- The user has already answered the same questions earlier in the conversation.
How to ask:
- One round, bundled. Use short, decision-shaped questions, not a sequence of open prose questions.
- Maximum four questions. Prioritize the ones that change the structure of the prompt, not the wording.
- State your own recommendation per question. The user wants a sparring partner, not a form.
- Never ask for information you can read yourself via MCP.
## Arbeitsmodus: Advisory oder Connected

Two working modes exist. Determine which one applies before starting.

**Connected**: the LoyJoy MCP tools are available for the relevant tenant. This is the default whenever they are. Work against the real state of the agent, not against a pasted snapshot.

**Advisory**: no MCP access (customer tenant, strict role separation, external stakeholder). Deliver copy-paste-ready text and setup instructions.

Note that a tenant may contain a prototype or demo copy of a customer agent while the productive agent lives in the customer's own tenant. Never edit a prototype as a proxy for the real agent. Confirm which artifact is live before touching anything.

### Toolchain in Connected mode

Before the first connected write, read `../loyjoy-headless/SKILL.md` and follow its rules for tenant selection, targeted reads, staging writes, round-trip validation, model checking, diff review, and publishing. This skill adds the phone-specific decisions; it does not replace the headless safety workflow.

Use this tool sequence as appropriate:

1. `tenant_meta` and `processes_list` — confirm the tenant and resolve an existing agent by name. Never guess IDs.
2. `process_get_xml_grep` — read the smallest relevant XML fragments, including the current custom instruction and configured tools. Use `process_get_xml` only when the whole structure is genuinely needed.
3. `process_create`, `process_set_attribute`, and `process_add_extension_element` — create or edit the staging process. Update an existing instruction with `process_set_attribute(..., name="text", value="...")`. Create a missing custom instruction with `process_add_extension_element(element_type="instruction", initial_attrs={"type":"custom","text":"..."})`.
4. `process_staging_xml_roundtrip_diff` — run after every write. Continue only when the result is identical.
5. `process_model_check` — check BPMN correctness and inspect `LOCALE_NOT_MAINTAINED` issues for language gaps before delivery or publishing.
6. `process_diff` — review the complete production-to-staging change.
7. `process_publish` — publish only after the user explicitly requests or approves publication.
### Rules for write access

- Never write without having read the current state in the same session.
- Never write a block the user has not seen and approved.
- Run `process_staging_xml_roundtrip_diff` after every write and `process_diff` after the complete change.
- One logical change per write. If the user asked for five things, that can still be one write, but do not bundle unrelated cleanup into it silently. Name what you changed.
- Work in staging. Touch production only through `process_publish`, and only with explicit approval.
### Hard limits of Connected mode

- MCP can create, configure, validate, diff, and publish a process. It currently cannot create or upload assets, assign a phone number, configure the external telephony routing, or perform a real voice call. Existing assets may only be referenced after their exact IDs and suitability have been verified.
- **Do not use `chat_completions_eval` for phone agents.** It is a text chat path and does not represent the voice channel. Verification of a voice agent happens through real test calls, not through simulated text turns.

### What “complete phone agent” means

Never treat “complete” as one undifferentiated state. Report these levels separately:

1. **Staging configuration complete**: the process is a phone agent, contains exactly one `AI_AGENT_SUBPROCESS`, has a custom instruction, its configured tools match the requested use cases, all process locales have complete i18n texts, XML round-trip validation is identical, model checking has no blocking findings, and the diff has been reviewed.
2. **Published**: the validated staging state was published after explicit user approval.
3. **Telephony ready**: a phone number and external routing are connected, the active standard voice prompt and realtime model are confirmed, and representative real voice calls passed.

The current MCP workflow can achieve levels 1 and 2. It cannot by itself prove level 3. Therefore a request such as “Erstelle einen vollständigen Phone Agent” is actionable, but the result must be described as a fully configured staging process unless telephony setup and real test calls were completed outside MCP.
## Order of operations

Follow these steps in order on every job. They are designed to avoid the most common waste pattern, which is starting to draft a prompt before knowing the technical and business constraints.

1. Determine the working mode (Connected or Advisory).
2. In Connected mode: confirm the tenant, resolve the process, and read the smallest relevant XML fragments. For an existing instruction, record its BPMN element ID and current `text`; for a new instruction, plan an `instruction` extension element with `type=custom`. In Advisory mode: request the current custom block as text.
3. Confirm which model the phone agent runs on. Ask the user once if it is not evident. If the user does not know, assume the faster non-reasoning realtime voice model as fail-safe, because defensive rules calibrated for it also work on the stronger reasoning model.
4. Confirm the LoyJoy standard voice prompt currently in use. The standard evolves. Ask for the current version if you have any doubt. The custom block must complement the standard, not duplicate it.
5. Identify the project type: new build, optimization, debugging, or proposal document.
6. Apply the Rückfragen-vor-Plan gate. Collect remaining constraints in one bundled round (see Clarification checklist). Do not silently assume, and do not ask what the XML already told you.
7. Reconcile the tool inventory (see Tool-Inventar abgleichen).
8. Draft, deliver, iterate. When iterating, always return the full updated custom block, not just the diff. Customers prefer copy-paste-ready output.
9. In Connected mode, run the round-trip check after every write. Before delivery, run model checking, review its locale-related issues, and inspect the production-to-staging diff.
10. Report the three completeness levels separately. Publish only on explicit approval, and always leave the real voice test visible as an open requirement until it has actually happened.

### Creating a new phone agent in Connected mode

Do not create an empty process while essential requirements are still unknown. First establish the target audience, use cases, process locales, form of address, tools, knowledge sources, handoff behavior, emergency routing, data restrictions, greeting placement, and intended realtime model.

Then follow “Create a phone agent” in `../loyjoy-headless/references/examples.md`. Its exact tool arguments and validation sequence are authoritative; the summary below highlights the phone-specific gates:

1. Create the process with `process_create` and immediately run `process_staging_xml_roundtrip_diff`.
2. Set `name="loyjoy:type"` to `value="phone_agent"` on `element_id=process_id`, then run the round-trip check again.
3. Add exactly one subprocess with `process_add_subprocess(process_id, parent_id=process_id, subprocess_type="AI_AGENT_SUBPROCESS")`, retain its ID, and run the round-trip check again.
4. Under that subprocess, add one custom `instruction` extension element with `type=custom` and the complete approved prompt text. Run the round-trip check.
5. Configure only tools required by the approved use cases. Use exact available element types and attributes discovered through the schema and existing process structure; never invent a tool name or element type.
6. Add all customer-visible texts for every configured process locale. Run `process_model_check` and resolve every `LOCALE_NOT_MAINTAINED` issue introduced by the task.
7. Run `process_model_check`, resolve blocking findings, and review `process_diff`.
8. Report what is complete and what remains for telephony readiness. Publish only after explicit approval.

### Editing an existing custom instruction in Connected mode

1. Locate the custom instruction with `process_get_xml_grep` and read its full current text.
2. Apply the prompt methodology in this skill and obtain approval for the complete replacement text.
3. Write it with `process_set_attribute(process_id, element_id, name="text", value="...")`.
4. Run `process_staging_xml_roundtrip_diff`, `process_model_check`, and `process_diff`; inspect locale-related warnings as well as blocking findings.
## Clarification checklist

Before drafting a new custom block, the following items must be either known from the brief, readable via MCP, or asked.

- Target audience: B2C, B2B, or mixed (typical distribution if mixed).
- Language and form of address (Du / Sie / dialect), and whether callers in other languages must be served at all.
- Tone keywords (warm, sober, energetic, formal, etc.).
- Tools that will be available to the agent (knowledge search, product search, email send, transfer, hangup, calendar/booking, custom integrations).
- Whether the knowledge base will exist at launch or whether the agent must work without one (no-knowledge override).
- Email recipients for transcripts, callback requests, lead handoffs.
- Transfer target (real telephony transfer with hidden number, or just spoken referral).
- Working hours of the receiving human team, and whether the platform injects the current time of day rather than only the date.
- Emergency or safety scenarios that require special routing (utilities: outages, gas leaks; insurance: claims with injuries; automotive: accidents).
- Sensitive data the agent must never collect or disclose (bank details, health data, third-party identifiers, contract numbers of others).
- Which number fields the agent must capture (customer number, contract number, meter reading, booking reference) and whether DTMF keypad entry is available.
- Greeting placement: spoken by the agent or external (Twilio/IVR layer)? In LoyJoy phone setups the greeting is usually external. Confirm explicitly.
## Architecture

LoyJoy phone agents use a two-layer prompt:

- **Standard voice prompt**: maintained by LoyJoy, applies to all tenants. Covers role basics, voice-output rules, turn-taking, tool-use mechanics, knowledge discipline, data capture, edge cases, anti-jailbreak, anti-hallucination, termination conditions, date injection, locale, response length.
- **Custom block**: tenant-specific, appended to the standard. Covers tenant role, tools allowed for this tenant, scope, knowledge sources, business flows, customer-facing phrasing, sensitive-data negative list, escalation paths, email templates.
Hard rule: do not duplicate rules from the standard in the custom block. Only override or extend. When an override is needed, state explicitly that it overrides the standard, and place it in the section that owns the topic. A custom rule that merely asserts the opposite of a standard rule without declaring itself an override will lose in ambiguous cases.

When a mechanic turns out to be tenant-independent, promote it to the standard instead of copying it into the next custom block, and remove it from the custom blocks that already carry it. Number capture is the canonical example.

## Wartbare Prompt-Struktur

A phone-agent prompt is a long-lived artifact that will be changed by several people over months. Structure it so the next change is cheap. This matters more than elegance of any single instruction.

Principles:

1. **One rule, one place.** Every behavior is defined exactly once. If two sections need it, one references the other by section name. Duplicated rules drift apart and then contradict each other.
2. **Shared building blocks are centralized.** Data capture, farewell, escalation, and email templates are defined once as their own sections. Use cases reference them ("nutze Datenerfassung, Felder 1 bis 4") instead of restating the steps.
3. **Use cases are self-contained and named.** Each has a goal, the steps, and an explicit exit ("wechsle in Gesprächsabschluss"). Adding a use case must not require editing existing ones.
4. **Stable section labels.** Use `## N. Name` headings that stay constant across versions, so change requests and review comments can reference them and so diffs stay readable.
5. **Abstract the requirement, do not enumerate the instances.** Prefer one rule covering a class of situations over ten examples of it. Examples are for disambiguation only: use two or three where the class boundary is genuinely unclear, not as the rule itself. Long example lists teach the model to pattern-match instead of generalize, and they are the main driver of prompt bloat.
6. **Interaction sequences are numbered flows, not bullet lists.** Anything with a state (asked, received, read back, confirmed, done) must be written as an ordered flow. Bullets carry no order and no state, so the model re-fires earlier steps. This is the single most reliable cause of loops in data capture.
7. **Preconditions come before steps.** A condition written after the flow ("only take this down if outside business hours") is read as an afterthought and ignored.
8. **One term, one meaning.** Reserve a phrase for exactly one actor and one action. Before adding a rule, search the prompt for the terms you are about to use. A phrase that means one thing for the caller and another for the agent will collapse into a loop.
9. **Length discipline.** Keep the custom block under roughly three thousand tokens unless the use case truly requires more. Before adding, check whether an existing section can absorb the change. A prompt that only ever grows is a prompt nobody will dare to touch.
10. **No dead weight.** Rules for use cases that were dropped, tools that no longer exist, or scenarios that never occurred get deleted, not commented out.
## Recommended section structure for the custom block

The following section order has proven to work well across verticals. Not every project needs every section. Add what is relevant.

1. **Override gegenüber Standard** (only if there are overrides, e.g. knowledge tools disabled, tool whitelist restricted, language forced, context reuse disallowed)
2. **Tools** (which tools are available, with usage rules per tool, especially eagerness and confirmation behavior)
3. **Persona** (role, tone, form of address, target audience)
4. **Ziel** (one or two sentences on the success criterion for the call)
5. **Notfall-Vorrang** (always before any business flow if safety scenarios apply)
6. **Gesprächseinstieg** (first sentence; clarify whether greeting is external)
7. **Erreichbarkeit** (time check, if the agent must decide between transfer and callback)
8. **Wissensnutzung** (when to search, when not to, price and figure discipline)
9. **Zielgruppen-Erkennung** (implicit, with concrete signal lists; or explicit short clarification question if distribution is mixed)
10. **Use Cases / Sub-Flows** (one labeled section per business flow)
11. **Datenerfassung** (numbered flows, digit-sequence handling, recap pattern)
12. **Einwandbehandlung / Eskalation** (objection-handling phrases, escalation paths)
13. **Scope und Negativliste** (what the agent will NOT answer or do)
14. **Datenschutz** (sensitive data negative list)
15. **Edge Cases** (unclear audio, abusive caller, end-of-call signals)
16. **Gesprächsabschluss** (farewell text and tool sequence)
## Änderungen am bestehenden Prompt: Entfernen vor Verbieten

The most common way a phone-agent prompt degrades is scar tissue: the agent does something unwanted, and instead of removing the instruction that caused it, a negative rule is stacked on top. The prompt now contains both an instruction and its prohibition. It grows, it contradicts itself, and instruction following gets worse across the board.

Default on every change request: **find and remove or rewrite the cause first.**

Procedure when the user reports unwanted behavior:

1. Locate the instruction that produces it. Search the custom block first, then the standard prompt. When the custom block looks clean, the cause is usually in the standard, and then the right fix is a change to the standard plus a declared override as a stopgap.
2. If the cause is an instruction in the custom block, remove or narrow that instruction. A rule whose scope was too wide gets a precise scope, not a counter-rule.
3. If the behavior stems from a use case that is no longer wanted, delete the use case rather than telling the agent not to run it.
4. Only if no removable cause exists does a negative rule become the right answer. Then place it in the section that owns the topic, not at the end of the prompt.
Negative rules are legitimate in these cases, and here they belong in the prompt explicitly:
- Legal or compliance boundaries (sensitive-data negative list, no advice in regulated domains).
- Scope boundaries against caller-initiated topics the prompt never mentions (competitors, off-topic chat).
- Overriding a behavior that lives in the standard prompt and cannot be edited per tenant.
- Suppressing a model tendency that has no source in the prompt at all (invented tool names, invented URLs, defaulting to the free tier).
Judgment rule: if you can point to the sentence that causes the behavior, remove that sentence. If you cannot, a negative rule is justified. State which of the two you did and why, so the user can disagree.

### Hygiene rules for the edit itself

These are the mistakes made while fixing other mistakes. They cost more test calls than the original bugs.

- **Replace, do not add in parallel.** When introducing a better phrasing for a question, an instruction, or an example, delete the old one in the same edit. Two competing formulations for the same moment produce unpredictable behavior.
- **Grep before you write.** Search the prompt for every key term in your new rule. If the term already appears, decide whether to reuse it consistently or pick a different one.
- **Sweep the dependents when removing a rule.** A deleted rule usually has references elsewhere ("read it back with the digit count"). Search for them in the same edit.
- **After the third patch to one section, rewrite the section.** Three rounds of patching means the structure, not the wording, is wrong. Re-derive the section as a flow instead of patching a fourth time.
- **Do not build a rule on a primitive the model is bad at.** Counting, arithmetic across many items, and precise length control are unreliable. A validation rule that depends on them produces false positives on correct data, which is worse than no validation.
- **After a series of edits to one section, stop and require a test call** before touching it again. Repeated blind edits compound.
- **Verify by search, not by memory.** After an edit round, grep the prompt for the terms you removed and for every cross-reference, and confirm each resolves.
## Tool-Inventar abgleichen

Prompt and tool configuration must match. In Connected mode, inspect the configured tool elements with `process_get_xml_grep`; use `process_get_xml` only if targeted reads cannot establish the complete inventory. Reconcile the inventory on every job.

1. Derive the required tool set from the use cases (knowledge search, email, transfer, hangup, booking, custom integrations).
2. Compare against what is actually configured.
3. **Missing tools**: name them explicitly and ask the user to add them before the prompt goes live. Never write a prompt that references a tool that does not exist. The model will invent the name or claim success without calling anything.
4. **Superfluous tools**: a tool configured but not needed by any use case is an active risk, because the model will eventually use it. Ask the user to deactivate it. Do not try to solve this in the prompt with a negative rule, that is exactly the scar tissue pattern. Deactivating is the clean fix. A stray web search tool is the classic case: it silently turns a curated knowledge agent into an open-web agent and produces answers that are sometimes right and sometimes invented.
5. **Name mismatch**: the prompt must use the exact configured tool name. Correct the prompt, not the configuration, unless the configured name is itself misleading.
6. Deliver the result as a short soll/ist list so the user can act on it in one pass.
## Mandatory voice-output rules (in standard, do not repeat)

The LoyJoy standard voice prompt already enforces these. The custom block should reference them by virtue of being appended, not restate them:

- No markdown, no bullet syntax, no list rendering.
- Numbers, dates, prices, currencies spoken as words.
- URLs spoken in pronounceable form in the active language (e.g. German "Punkt", not English "dot").
- Email addresses spelled out.
- Phone numbers, IDs, codes spoken character by character.
- Acknowledge-first preamble on every reply to mask latency.
- Verbosity capped at one to two sentences per turn.
- Tool execution rule: never claim a tool ran successfully unless it actually did.
If a customer-specific override is needed (e.g. language pronunciation rule per tenant), state it explicitly in the custom block.

## Pattern catalog

The following patterns recur across phone-agent projects. Reuse them. Each is named so you can reference it in conversation and so the user can read the section directly.

### Pattern: Bridging vor Tool-Calls (parallel, variabel, kurz)

Why: the gap between user end-of-speech and the first audio token is the most damaging latency a caller perceives. A short, varied preamble spoken in parallel with the tool call hides it.

Rules:
- Speak the preamble immediately, then call the tool in the same response phase. Not sequentially.
- Provide a list of varied phrases. Match length to expected tool duration. Knowledge lookups in modern LoyJoy stacks are sub-second, so use one to three words: "Moment bitte.", "Kurz nachgeschaut.", "Einen Augenblick.", "Ich prüfe das."
- Do not let the model produce filler about itself ("Ich überlege gerade", "Ich nutze jetzt mein Tool"). Describe the action.
- Skip the preamble when the answer is direct, when the user is only confirming, or when audio was unclear.
### Pattern: Implizite Zielgruppen-Erkennung

Why: asking the caller "are you a customer or a partner" sounds bureaucratic and reduces conversion in B2B contexts.

Rules:
- Provide a short signal list per target group, derived from how each group actually talks (own contract and claims versus commission and partner IDs).
- Default branch must reflect actual call distribution. If most callers are end customers, the default is the end-customer flow. If the split is roughly even or unknown, ask one short clarifying question after the first utterance.
- Forbid the agent from asking "are you a customer or a broker" as the very first question.
- Keep signal lists free of terms that merely restate the label of the category. They add length without adding discrimination.
### Pattern: Transfer-Anbieten statt direkt Durchstellen

Why: callers want control over whether and when they are put through. Even technically transparent transfers feel intrusive when they happen without a question.

Rules:
- The agent always offers the transfer with the destination phone number spoken aloud, then asks for explicit consent ("Soll ich Sie durchstellen?"), then transfers only after a clear "ja".
- If the receiving team has a short, memorable number, speak it actively, even if a transfer tool is available. Many callers prefer to call back themselves and write the number down.
- If outside business hours, never offer the transfer; provide the number and the hours and end the call politely.
### Pattern: Erreichbarkeit als Gate

Why: agents offer transfers outside business hours because the time check is written as a description rather than as a precondition, and usually in several places at once. The caller then gets an offer that cannot be honoured.

Rules:
- One section owns the opening hours and the check. Every use case that could transfer references it. Remove all other mentions, however well meant.
- Write it as a numbered gate that runs **before** the transfer is offered or even mentioned. Outside the hours the agent must not name transfer as an option at all, otherwise the caller asks for it.
- The hours table used for the decision must be unambiguous: one line per day, telephone hours only, no parenthetical alternatives, no on-site hours mixed in. On-site hours belong in the use case that answers questions about them. A table with two candidate closing times per day cannot be resolved by the model on a boundary case.
- Confirm that the platform injects the current time of day, not only the date. If only the date is available, none of this is prompt-fixable.
- When resolving a contradiction in customer-supplied hours, state the resolution explicitly and ask for confirmation. A wrong closing time causes transfers into an empty office.
### Pattern: Step-by-step Datenerfassung mit Recap

Why: at the phone you ask one thing at a time, never a bundle. Voice transcripts are noisy; collecting in one shot leads to wrong fields.

Rules:
- Announce data capture once: "Damit unser Team Sie zurückrufen kann, brauche ich kurz einige Angaben."
- Then ask for one field per turn, in priority order (most important first). A single question that names three fields is the worst possible ask, and it is disproportionately damaging on hands-free calls.
- Read back high-precision fields immediately and end with "Ist das so richtig?" and wait. For number fields follow the Ziffernfolgen pattern below.
- Before starting, pre-fill from what the caller already said, including information embedded in compound words ("Stromzählerstand" carries the commodity). Confirm what you took over in one short sentence and ask only for the missing fields. A general rule like "do not ask again for what was already said" is too passive to fire; make the pre-fill an explicit numbered step at the start of the capture.
- Before the final action (email send, booking write), perform a recap that lists all collected fields and asks for confirmation. If a project deliberately drops the recap to shorten calls, per-field confirmation must carry the full weight, and no other section may still reference a recap.
### Pattern: Ziffernfolgen erfassen

Why: numbers are the highest-risk field class on the phone, and the naive fixes make it worse. This pattern is the distilled result of several failed attempts on a live agent.

Model the capture as a numbered flow, not a bullet list:

1. Ask once, and ask for the individual digits in that one question. Ask for what the caller can see, not for an abstract value. "Read me the digits on the display" produces a digit sequence, "tell me your meter reading" produces a compound number. Framing the question is a cheaper lever than fixing the parse.
2. Let the caller state the whole sequence in one utterance. Do not interrupt, do not ask between digits, do not confirm single digits.
3. Accept whatever form arrives. Never reject a compound number and never repeat the request for digits at this point. A caller who ignores the instruction must not hit a dead end.
4. Read back once, in blocks of two to three digits with a sentence boundary after each block, then ask for confirmation.
5. On confirmation the field is done. Move on. State this explicitly, otherwise the agent asks again.
6. Only on negation discard the value entirely and return to step 2, with an escalation phrase used nowhere else in the prompt. If step 1 already asks for individual digits, the escalation must differentiate itself some other way, for example by asking for a slower repetition.
Interpretation rules that accompany the flow:
- **The complete sequence is one field.** Say so. Otherwise the general "one field per turn" rule is applied per digit and the agent confirms every single digit.
- **Replace, never extend.** The value is only ever set or replaced by a complete statement. Digits arriving in a confirmation turn are not appended. Without this, a misheard fragment gets merged into the value.
- **Negation outranks digit interpretation.** Language-specific homophones exist (German "nein" against "neun"). At the start of an answer to a confirmation question, such a token is a negation.
- **Magnitude words are place values, not concatenated blocks.** Otherwise "einhundertachtundzwanzig" is rendered as 100 followed by 28. Two examples with the correct and the wrong reading are justified here, because this is exactly the confusion.
- **Never have the agent state the number of digits, and never validate by digit count.** Models count unreliably. A wrong count triggers a correction round on a correct value, or rejects a valid number outright. The block-wise readback already lets the caller hear a spurious digit.
- Partial corrections are only valid when the caller names a position explicitly. A rule like "repeat only the corrected part" without that condition teaches the agent to merge fragments into the value.
Honest limit: the compound-number misparse can happen in transcription, below the prompt. If the magnitude rule does not hold after two test calls, it is not prompt-fixable. Route it to engineering, where deterministic number normalization or DTMF keypad entry are the real fixes. DTMF eliminates the entire error class and should be the first question whenever number capture is central to the use case.

This pattern is tenant-independent and belongs in the LoyJoy standard voice prompt rather than in each custom block. Where it is in the standard, remove it from the custom blocks.

### Pattern: Wunschtermin statt Bestätigung

Why: appointment bookings on the phone often need internal approval. Communicating a "confirmed appointment" when the human still has to check creates legal and customer-trust risk.

Rules:
- Phrase the closing as "I will pass your preferred slot on" not "your appointment is booked".
- Send the internal handoff email with explicit subject "Wunschtermin" or equivalent.
- Tell the caller that the formal confirmation will arrive separately after the human has checked.
### Pattern: Notfall-Vorrang

Why: in utilities, insurance, and automotive contexts, the agent may receive calls about safety-critical situations. Sending such callers through a normal flow is harmful.

Rules:
- Place the Notfall-Vorrang section before all use cases.
- Define the trigger class as any situation with risk to life, health, or property, with a handful of vertical-specific triggers as anchors.
- **The emergency numbers belong in the prompt text and are spoken from there, with no tool call in between.** An instruction to search the knowledge base before naming an emergency number is a serious defect: it adds latency in a life-safety moment and can fail. Check for this on every audit, it appears surprisingly often because the general search-first rule gets copied into the emergency section.
- The agent interrupts any flow on these triggers, speaks the safety instruction first where one applies, then the number, digits spoken individually.
- Only after the emergency reference does the agent gently return to the original topic.
- Keep the trigger list and the numbers in this section only. Use-case sections must reference it instead of repeating either.
### Pattern: Mandatory Search Trigger

Why: phone agents are eager and frequently answer concrete questions from the system prompt instead of calling the knowledge tool, leading to outdated or invented answers.

Rules:
- State the default as "if in doubt, search".
- Define the must-search class by property, not by enumeration: anything factual, current, priced, contractual, or configuration-specific triggers a search.
- Provide a narrow whitelist of what may be answered without a search (greetings, repetition, one-sentence company explanation, scope confirmation, and anything that stands verbatim in the prompt such as emergency numbers and opening hours). This list must be short and closed.
- **Check for contradictions between the must-search list and the no-search list.** Items appearing in both (opening hours, emergency numbers) are a common copy artifact and produce erratic tool use plus needless latency.
- If the project uses multiple named tools instead of one generic one, say so explicitly. The model otherwise invents a generic tool name.
Kontext-Wiederverwendung als eigener Fehlermodus:
- A standard prompt may explicitly permit reusing retrieved context from earlier in the same call. This looks harmless and is the cause of a distinct bug: the longer the call, the more accumulated context exists, the more often the model decides an earlier result already answers the new question and skips the search. The answer then comes from a merely similar earlier lookup.
- The symptom is that early answers are correct and later answers are stale or subtly wrong. It is easy to misdiagnose as a retrieval problem, because the retrieval was never invoked.
- The permission is worded backwards wherever it says "if it clearly answers the new question": it grants reuse exactly when the model feels confident, which is when it is most often wrong.
- Fix: narrow the permission in the standard so that reuse is allowed only when the caller explicitly asks for the same information again, and every new factual question triggers a fresh search regardless of call progress. Add a declared override in the affected custom block as a stopgap until the standard ships.
- Do not overcorrect into "search before every reply". Confirmations, process questions, and clarifications do not need a search, and on a voice call the added latency is the more expensive defect. The cut is at the new factual question, not at the turn.
### Pattern: Preis- und Zahlendisziplin

Why: invented prices are the most damaging hallucination class in utilities, insurance, and retail, because callers act on them.

Rules:
- Tie the rule to the **content of the search result**, not to whether a result exists. The common failure is not an empty search but a result about tariffs that contains no price, which the model then fills in.
- State it explicitly: a price is only spoken when it appears as a figure in the retrieved result. No approximation, no example value, no range.
- **Forbid deriving a price by calculation** from base price and unit price. Models do this readily and it is a liability.
- Provide the fallback sentence and the exit: the price depends on tariff and consumption, followed by transfer or callback.
- If prices are poorly retrievable from the website, say so plainly. Price data usually lives in tables, calculators, or PDFs and crawls badly. A curated price document maintained by the customer beats any crawl tuning, and no prompt rule can compensate for missing retrieval.
### Pattern: Tool-Routing nach Themenklasse

Why: when multiple knowledge tools exist (e.g. marketing site, docs site, web search), the model picks unpredictably.

Rules:
- Define a default for tenant-general questions.
- Define a switch condition (e.g. "how-to questions go to docs").
- Define when supplementary tools (web search) are allowed and how to treat their results.
- Forbid invented tool names.
### Pattern: Variety-Constraint gegen Wiederholungen

Why: phone agents fall back on the same empathy phrase, the same acknowledgment, the same closing question, making the call sound robotic.

Rules:
- Add an explicit instruction not to reuse openers, empathy phrases, closing questions, or acknowledgment words across turns within one call.
- Provide a small pool of variations the agent may draw from.
### Pattern: Anti-Du-Drift bei Sie-Form

Why: if knowledge sources contain Du-form text, the model often drifts into Du even on a Sie-form tenant, sometimes within a single answer.

Rules:
- State the form of address as a hard constraint in the Persona section.
- Add: "Even when sources, FAQs, or other inputs use Du, every answer is formulated in Sie. No mid-answer switching."
### Pattern: Sprachfixierung

Why: speech-to-speech models drift into another language mid-call, and transcripts show stray characters from other scripts. Both come from unstable language detection.

Rules:
- The custom block needs an explicit language rule. Its absence is easy to overlook because the form of address is usually specified and looks like it covers language.
- State the language as binding even when the caller speaks another language or a knowledge source is in another language, unless multilingual service is actually wanted. Decide that question explicitly rather than leaving it open.
- The real fix is pinning the recognition locale in the session configuration. The prompt rule is the backstop, not the solution. Stray characters in the transcript are always an engineering item.
### Pattern: Reference Pronunciation

Why: TTS engines mispronounce brand names, English loanwords, and technical terms, leading to confusion ("Lead" rendered as "Lied").

Rules:
- List only the terms that have actually been mispronounced in test calls. Ten to twenty maximum.
- Use the form "Pronounce 'X' as 'Y'" not IPA.
- One sentence per term. A positive instruction makes the negative counter-example ("never say it with a W") redundant.
- Refresh the list as new errors appear, and remove entries that no longer occur.
### Pattern: Sensible-Daten-Negativliste

Why: phone agents will follow instructions to collect any field if not constrained. For regulated verticals this is a legal exposure.

Rules:
- Explicit "Frage NIEMALS nach" section listing the concrete forbidden fields for this vertical.
- Place near the top of the custom block, not at the end.
- Add what to do when the caller volunteers such data: do not record it, mention once that you may not.
- This is one of the legitimate uses of negative rules. Keep it as a closed list, not a growing one.
### Pattern: Datum dynamisch

Why: hardcoded dates in the prompt go stale and produce wrong outputs the moment the date passes.

Rules:
- Always use a date template variable. In LoyJoy: `${localDate()}` or equivalent.
- If the platform does not support templates in custom blocks, agree on a refresh cadence and a calendar reminder.
### Pattern: Out-of-Scope Steering

Why: callers will ask about competitors, weather, generic chat, or other topics.

Rules:
- Define what is in scope.
- Define what to do for out-of-scope (politely decline, steer back, optionally offer to send the topic to a colleague for follow-up).
- For competitor questions: never compare, never criticize. Steer to own value.
### Pattern: Greeting external

Why: in most LoyJoy setups the greeting is part of the IVR or telephony layer and not part of the model output. If the model also greets, callers hear "Willkommen … Willkommen".

Rules:
- State explicitly: "Die Begrüßung erfolgt extern. Deine erste eigene Äußerung ist [exakter Satz]."
- **Never put the opening question into the prompt as its own instruction.** A line like `Frage: "Wie kann ich Ihnen helfen?"` in an intent-recognition section has its own trigger and re-fires whenever the agent returns to intent recognition, which the caller experiences as the agent starting the call over and repeating the greeting. Write intent recognition as a classification task on the caller's utterance instead.
- Cover the mid-call case explicitly: when the anliegen is unclear later on, the agent asks about the concrete request without greeting and without repeating the entry question.
- If the restart symptom persists after this fix, look for a session restart in the telephony layer.
### Pattern: End-of-call discipline

Why: phone agents tend to either hang up too eagerly (on ambiguous "okay") or never hang up (waiting forever after farewell).

Rules:
- Define unambiguous end signals ("Tschüss", "Auf Wiederhören", "Vielen Dank, das war's").
- Define ambiguous signals that require a clarification turn instead of a hangup ("mhm", "okay", "alles klar").
- Require the agent to speak the farewell sentence in full before calling the hangup tool.
### Pattern: Testmodus

Why: agents are often tested against live telephony and live mailboxes before go-live. Ad-hoc test overrides scattered through the prompt are forgotten at go-live and cause real transfers and real customer mails.

Rules:
- Put the test-mode switch in its own section at the very top, with an explicit on/off marker.
- Where a test override has to sit at the point of action (tool section, transfer step, mail routing), keep it there rather than centralizing it, because the model needs it where it acts.
- In exchange, list in the test-mode section every place that has to be changed when switching it off. Two lines there save an incident at go-live.
### Pattern: Free-/Default-Tier deemphasis

Why: when knowledge sources mention a default or free tier as one of several options, the model often defaults to recommending it, which can hurt revenue.

Rules:
- Explicitly tell the agent not to proactively recommend the default tier.
- The default tier may only be mentioned if the caller asks for it or confirms they use it.
### Pattern: KI-Transparenz / EU AI Act

Why: AI agents in the EU must disclose their AI nature when asked, and proactive disclosure is recommended for telephony.

Rules:
- Place a one-sentence disclosure in the external greeting or in the agent's first own sentence.
- If asked, the agent confirms being an AI voice assistant of the tenant.
- For regulated verticals (insurance, healthcare, finance), coordinate the exact wording with the customer's compliance team.
### Pattern: DSGVO-Aufzeichnungshinweis

Why: if calls are recorded, a one-line disclosure is required.

Rules:
- Include the recording notice only if recording actually happens.
- Reference the data protection page on the website rather than reading the full text.
## Anti-patterns

Avoid these. They reliably hurt phone-agent quality.

1. **Sequential bridging**: long preamble first, then tool call. Adds latency instead of hiding it. Use parallel preamble.
2. **Bulk data capture**: asking for name, email, phone, time, topic in one turn. Voice transcripts cannot disambiguate. One field per turn always.
3. **Direct transfer without consent**: technically convenient, conversationally aggressive. Always offer first.
4. **Hardcoded date**: prompt rot. Use template variable.
5. **Markdown in voice output**: the model will read brackets and stars out loud. Markdown link rules belong in chat prompts, not voice prompts.
6. **Emoji instructions in voice prompts**: emojis cannot be spoken. Remove from any persona/tone block when migrating from chat.
7. **Vague tone descriptors only ("be helpful")**: leaves room for drift. Add concrete tone keywords plus a verbose anti-example.
8. **Constraint overload with "always" / "never" / "must"**: reasoning voice models follow these literally and get rigid. Use precise scope, not blanket constraints.
9. **Tool names mentioned in prompt that do not exist in the tool list**: the model will invent the name or pretend the action succeeded.
10. **No variety constraint**: agent becomes robotic within three turns.
11. **End-of-call on ambiguous signals**: callers hang up frustrated mid-thought.
12. **Bridging text claims success before tool returns**: classic hallucination vector. Bridge neutrally, confirm only after success.
13. **"You may answer simple questions from the orientation block"**: too vague. The model will answer concrete pricing or feature questions from memory. Replace with a closed whitelist.
14. **Re-asking already-captured fields**: skip fields that came up earlier in the call, and make the skip an explicit step rather than a passive rule.
15. **Negativregel-Akkretion (scar tissue)**: patching unwanted behavior with a counter-rule instead of removing its cause. The prompt then contains both the instruction and its prohibition, grows monotonically, and instruction following degrades. See "Änderungen am bestehenden Prompt".
16. **Beispiel-Inflation**: replacing a general rule with a long list of instances. The model pattern-matches the examples and fails on the case that was not listed. Abstract the rule, keep at most two or three disambiguating examples.
17. **Duplizierte Regeln über Sektionen**: the same behavior defined in two places. They drift apart on the next edit and then contradict each other.
18. **Prompt-Regeln gegen überflüssige Tools**: telling the agent not to use a tool that should simply be deactivated in the configuration.
19. **Terminologie-Kollision**: one phrase used for several meanings, typically a phrase that describes both what the caller should do and what the agent should do. The model cannot separate them and re-fires the wrong one. Reserve one term per meaning and grep before adding.
20. **Regeln auf unzuverlässigen Primitiven**: validation that depends on counting, arithmetic, or precise length control. It fires on correct data and blocks valid captures. Prefer mechanics that let the human notice the error.
21. **Konkurrierende Formulierungen**: a better phrasing added without deleting the old one. Two questions for the same moment, two examples for the same rule. Always replace instead of adding in parallel.
22. **Bullet-Liste für einen Interaktionsablauf**: a capture or escalation sequence written as bullets. No order, no state, so the agent loops. Write it as a numbered flow.
23. **Hard rejection of caller behavior**: refusing to process input because the caller did not follow an instruction. Accept the attempt, then escalate if it failed. A dead end is always worse than a degraded path.
24. **Kontext-Wiederverwendung über Turns**: allowing the agent to answer a new factual question from context retrieved earlier in the call. Degrades silently and only in longer calls, and is easily misread as a retrieval fault. See Mandatory Search Trigger.
25. **Suchpflicht vor der Notfallnummer**: any tool call between an emergency trigger and the spoken emergency number. The numbers belong in the prompt and are spoken immediately.
26. **Entscheidungstabellen mit Mehrdeutigkeit**: an opening-hours or pricing table that offers two candidate values per row. The model cannot resolve boundary cases and will pick wrongly.
## Debugging workflow

When test calls show problems, diagnose in this order before changing the prompt.

1. **Reproduce**: get a recording and the transcript. Note where the failure happens (greeting, first user turn, mid-call, end). In Connected mode, read the actual prompt via `process_get_xml_grep` first. A surprising number of reported bugs are a prompt state nobody expected to be live.
2. **Classify**: which layer owns this?
   - Audio layer: echo, distortion, cut-off, hold-music interpreted as speech, hands-free calls in cars. Not prompt-fixable.
   - VAD layer: agent interrupts user, agent does not let user finish, agent talks on when interrupted, long pauses after user end-of-speech. Tune `turn_detection.silence_duration_ms`, `threshold`, barge-in handling, consider semantic VAD.
   - Telephony layer: caller ID shown wrong on transfer, DTMF not handled, session restarts mid-call. Not prompt-fixable.
   - Transcription layer: numbers, homophones, spelled-out strings arriving wrong, stray characters from other scripts, language drift. Partly mitigable in the prompt, not fixable there.
   - Knowledge layer: agent hallucinates URLs, returns generic instead of specific answer, prices not retrievable. Often the index or crawler is the issue, not the prompt.
   - Tool configuration: missing, superfluous, or misnamed tools. Fix the configuration, not the prompt.
   - Standard prompt: a rule in the layer you did not write. Check it whenever the custom block looks clean. Stale answers late in a call are the classic example.
   - Model layer: instruction following weak on small models. Consider model upgrade or stricter rules.
   - Prompt layer: the rule was missing, contradictory, or unclear. Fix in the custom block.
3. **Fix at the right layer**: prompt fixes for prompt problems only. Do not try to patch retrieval, VAD, or telephony issues with prompt language.
4. **Find the cause before adding a rule**: apply "Entfernen vor Verbieten". Removing the offending instruction is the first candidate, not the last.
5. **Suspect your own last edit first.** When a new symptom appears right after a change, the change is the most likely cause. Re-read what you wrote before theorizing about the model.
6. **Ask when the symptom depends on call length.** Behavior that is correct early and wrong late points at accumulated context, not at a missing rule.
7. **Test minimal change**: one rule change at a time. Re-run the same call scenario on a real call. Do not substitute a text chat evaluation for a voice test.
8. **Confirm with second sample**: avoid one-call regressions. Run two to three calls before declaring fixed.
## What is NOT prompt-fixable

The following recurring complaints cannot be solved in the prompt. Route them to the right layer.

- Self-interruption because the agent hears its own audio: echo cancellation in telephony layer.
- Long pause between user end-of-speech and agent response: VAD `silence_duration_ms` too high, or model latency. Lower the VAD value, consider semantic VAD, consider lighter model.
- Agent interrupts the caller mid-sentence: VAD threshold too low, or interruption handling.
- Agent keeps talking when the caller tries to interrupt: barge-in disabled or suppressed by echo of the agent's own output. Prompt-side mitigation is limited to breaking long readbacks into short blocks so turn boundaries occur more often.
- Poor recognition on hands-free calls in a car: road noise, echo, automatic gain control. Shorter questions help marginally, nothing else in the prompt does.
- Spoken compound numbers arriving with inserted zeros: number normalization in the transcription path. Mitigable through question framing and interpretation rules, properly fixed by deterministic normalization or DTMF.
- Stray characters from other scripts in the transcript, and language drift mid-call: recognition locale not pinned. Engineering.
- Prices not retrievable from the website: tables, calculators, and PDFs crawl badly. Needs index work or a curated document, not prompt work.
- Calls without user input not counted in analytics: platform-side metric.
- CSV exports empty: platform issue.
- Recording missing or cut off: telephony or recording pipeline.
- Transcript and audio not aligned: pipeline.
- Greeting can be interrupted by user: VAD or front-end timing.
When the user reports such issues, name them as not-prompt-fixable explicitly, route them to engineering, and focus prompt work on what the prompt can actually address.

## Model considerations

- Reasoning voice models (current generation, e.g. the `gpt-realtime-2` class): set reasoning effort to low as default; raise only for use cases that need multi-step planning. Take advantage of message channels (commentary vs final) for preambles. Be careful with literal interpretation of `must` / `never` / `always`.
- Fast non-reasoning voice models (e.g. the `gpt-realtime-1.5` class): need more defensive rules. Rules calibrated for them also work on the reasoning models, so when uncertain about the target model, write for the weaker one.
- For both: prefer precise scope ("for write actions modifying customer data, ask for confirmation") over blanket constraints ("always ask for confirmation").
- Model names change. Confirm the actual configured model per tenant rather than trusting the names above.
## Side workflows

The job around the prompt itself is often as important as the prompt. These patterns recur.

### Customer feedback analysis

When a customer sends a spreadsheet, document, or mail with bug reports, feature requests, and observations, structure the response in four buckets.

1. **In Prompt lösbar**: each item with the concrete prompt change proposed. State per item whether it is a removal, a narrowing, or a new rule.
2. **Tool-Konfiguration**: items that require activating, deactivating, or renaming a tool.
3. **Außerhalb des Prompts**: items belonging to VAD, audio, transcription, pipeline, retrieval, telephony. State this clearly and route them to engineering.
4. **Zusatz-Wünsche**: feature ideas that need product decisions.
Lead with the highest-severity finding even when the customer did not report it. Safety defects and legal exposure outrank the reported list.

Deliver as a table or short numbered list the customer can scan in under a minute, with a short paragraph of context above.

### Change-proposal Word document for customer review

When the customer needs to see and approve changes before they go live, produce a Word document with:

- Title and date.
- Two- to four-sentence intro explaining the source of changes (workshop, feedback, log analysis).
- Overview table: feedback item → proposed prompt action → type of action (removal / narrowing / new rule / tool config).
- Full updated prompt with new or changed sentences highlighted in yellow (color code 10), removed text struck through in red. In Connected mode, derive this from `process_diff` (prod vs staging) rather than comparing by hand.
- Appendix listing items NOT addressed in the prompt (engineering and tool-configuration scope).
- One-paragraph recommendation on next steps (review, publish, test call, observe for two to three days).
Keep page count under five if possible. Customers read short documents.

### Stakeholder mail

When a topic has been addressed and the customer team needs an update, write a short mail with:

- One-sentence acknowledgment of their input.
- Numbered list, one short bullet per item: what changed plus a one-clause reason.
- A separate short block for what you need **from them**, phrased as concrete decisions, not as open questions.
- A separate short block for what is still open on your side, so they can see it is tracked.
- One sentence on the next step, ideally an invitation to retest the exact scenario they reported.
Match the form of address used in the existing thread (Du or Sie). Default to Du with customer teams once first-name basis is established, Sie in early contacts and regulated verticals.

### Promoting a mechanic into the standard prompt

When the same mechanic has been written into a second tenant's custom block, or when the cause of a bug turns out to sit in the standard, it belongs in the standard. Deliver one consolidated proposal containing:

- The finding: current wording, the failure mode it produces, and where it was observed.
- The proposed wording, written tenant-independent and channel-specific.
- What is deliberately **not** part of the proposal, with the reason. Over-correction is the main risk when fixing a standard rule.
- Consequences and trade-offs, including latency and tool-call volume.
- The list of custom blocks that already carry a version of the mechanic or a stopgap override, so the duplicates get removed rather than left to drift.
- A note on which tenant-specific parameters remain in the custom block.
- The open technical questions for engineering, collected in one place.
Order the proposal by priority, not by the order you discovered the items.

### Setup instructions for tenants without MCP access

In Advisory mode the customer applies the changes. Provide a numbered step list, and a short screen recording if the customer team is new to the platform:

1. Create the agent or new version in the tenant.
2. Paste the standard prompt (if not already in place).
3. Paste the custom block.
4. Configure the tools, including deactivating the ones flagged as superfluous.
5. Configure the telephony number and routing.
6. Publish and run a test call.
Pack the prompt as a `.txt` attachment to avoid mail-client formatting breakage.

## Style for working with the user

LoyJoy team members and customer-team users share certain preferences observed across projects.

- Compact answers. No filler, no unnecessary em dashes.
- Numbered lists where the user needs to reference items by number.
- Honest diagnostics. When a problem cannot be solved at the requested layer, say so plainly and route it.
- When iterating, always return the full updated artifact, not just the diff. The customer almost always wants copy-paste-ready output.
- Sparring tone: push back when the proposed change creates a new problem. Do not just agree. In particular, push back when a requested change would add scar tissue instead of removing a cause, and when a literal reading of the request would overcorrect.
- When the user proposes a better solution than yours, say so plainly and adopt it.
- When proposing changes to a customer-facing prompt, mark exactly what is new and what was removed. Removals are as important to show as additions.
- **Measure before promising.** Do not quote a reduction in words, tokens, or lines without counting first, and report the measured result afterwards even when it undershoots the estimate. A wrong estimate silently absorbed is worse than a small delivered gain.
- **Own your own regressions explicitly.** When a symptom traces back to your previous edit, say so in the first sentence. The user is testing on a live agent and needs to know whose bug it is.
- **Be transparent about where a finding came from**, including when it came from an artifact you were later asked not to use.
- For voice prompts, never recommend chat-specific patterns (markdown links, emojis, long enumerations).
## Quick checklist before delivering a custom block

Run through this before handing a prompt to the user.

1. Does the persona section state the target audience, tone, language, and form of address, and is the language binding?
2. Is there a Notfall-Vorrang section if the vertical has safety scenarios, are its triggers and numbers defined only there, and is there no tool call between trigger and number?
3. Is the greeting placement clarified, and is the opening question absent as a standalone instruction?
4. Is the mid-call "anliegen unclear" case covered without greeting?
5. Is the Zielgruppen-Erkennung implicit or with one clarification, never with a bureaucratic first question?
6. Does every use case end with a clear next action and an explicit transition out?
7. Is every data capture with a state written as a numbered flow, with an explicit "field is done" step, and are preconditions before the steps?
8. Do number captures follow the Ziffernfolgen pattern: whole sequence as one field, any input form accepted, block-wise readback, no digit counting, replace never extend, negation priority?
9. Is there a recap before any final action, or, if the recap was deliberately dropped, is there no remaining reference to one anywhere?
10. Is the search discipline free of contradictions between must-search and no-search, and is context reuse across turns excluded?
11. Are price rules tied to the content of the result, with calculation forbidden?
12. If a time-dependent decision exists: is there exactly one hours table, unambiguous, telephone hours only, and is the check a gate before the offer?
13. Do all referenced tools exist in the tenant with exactly matching names, and has every superfluous tool been flagged for deactivation?
14. Are sensitive data forbidden via a closed negative list, including what to do when volunteered?
15. Is the date dynamic, not hardcoded?
16. Is the form of address protected against drift from sources?
17. Is the variety constraint in place?
18. Is the end-of-call discipline defined?
19. Has any rule from the standard been accidentally duplicated? If yes, remove from custom.
20. Is every behavior defined exactly once across sections, and does every cross-reference resolve to an existing section?
21. Does every key term have exactly one meaning throughout the prompt?
22. For every change in this round: was a cause removed where one existed, rather than a negative rule added, and was every superseded formulation deleted rather than left in parallel?
23. If test mode is active: does the test-mode section list every place that must be changed to switch it off?
24. Is the block still within the length budget, and are examples limited to genuine disambiguation?
25. In Connected mode: was the XML round-trip identical after every write, were blocking and `LOCALE_NOT_MAINTAINED` model-checking findings reviewed, was `process_diff` reviewed, and were publication status, telephony setup, and the real voice test reported separately?
## Appendix: template skeleton for a fresh custom block

```
## Override gegenüber Standard
[only if needed: disabled tools, language override, no context reuse, pronunciation]

## Tools
- [exact tool name]: [when to use, eagerness, confirmation rules]

## Persona
Du bist der KI-Sprachassistent von [tenant]. Tonalität: [keywords]. [Sie/Du-Form].
Sprache: [language], verbindlich.
Zielgruppe: [audience].

## Ziel
[one or two sentences on call success criterion]

## Notfall-Vorrang (only if applicable)
[trigger class + numbers spoken from here, no tool call + safety instruction + return-to-topic]

## Gesprächseinstieg
Die Begrüßung erfolgt extern. Du begrüßt nicht selbst, auch nicht später im Gespräch.

## Erreichbarkeit prüfen (only if transfer or callback decisions exist)
[one unambiguous hours table + numbered gate before offering a transfer]

## Wissensnutzung
[closed no-search whitelist, search for everything else, no context reuse,
 price only if it appears as a figure in the result]

## Use Case 1: [name]
[precondition, goal, steps, exit transition, references to shared sections]

## Datenerfassung (shared, referenced by use cases)
[pre-fill from what was already said, one field per turn,
 Ziffernfolgen flow for number fields, recap before the final action]

## Scope und Negativliste
[what is in scope; what is NOT answered]

## Datenschutz
Frage NIEMALS nach: [closed list] + what to do when volunteered

## Edge Cases
[unclear audio, abusive caller, silence, end-of-call signals]

## Gesprächsabschluss
[farewell text + tool sequence, mail only where a use case requires it]
```
