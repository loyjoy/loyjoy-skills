---
name: "loyjoy-phone-agent-builder"
description: "Create and configure new LoyJoy phone agents in staging, and build, iterate, or debug their custom voice prompts. Covers the standard-plus-custom architecture, the mandatory realtime-model gate, reading the versioned LoyJoy standard voice prompt from the monorepo, LoyJoy MCP workflows, maintainable prompt structure, a scripted prompt-budget and redundancy check, conformance with the OpenAI Realtime prompting guide, tool reconciliation, common phone use cases, an anticipation pass that replaces unavailable test calls, and the boundary between a configured process and a telephony-ready agent. Use for requests such as \"Erstelle einen vollständigen Phone Agent\", \"Phonebot Prompt\", \"Voice-Agent anpassen\", \"Custom-Prompt für Telefon\", \"Phone Agent Feedback umsetzen\", \"Telefonbot debuggen\", or \"Voice-Prompt optimieren\"."
---

# LoyJoy Phone Agent Builder

This skill captures the methodology, patterns, and debugging techniques developed across multiple LoyJoy phone-agent projects. It is the voice-specific counterpart to `loyjoy-prompt-builder` (chat agents). Use it whenever the work involves a phone agent, voice bot, or speech-to-speech assistant, in any vertical.

For chat agents (web chat, in-app chat, embedded widgets), use `loyjoy-prompt-builder` instead. Voice patterns (acknowledge-first, no markdown, spoken pronunciation, character-by-character digits, transfer with consent) and chat patterns (markdown links, bullet lists) do not translate between the channels.

The skill is meant for internal LoyJoy use and for sharing with customers. It names no individual customers. Patterns are written so they apply to any vertical.

## Reference files

This file carries the workflow and the rules that apply to every job. Three reference files carry the detail; read the relevant one when the step calls for it.

- `references/patterns.md` — recommended section structure for the custom block, the full pattern catalog, the anti-pattern list, and the template skeleton. Read when drafting or auditing a block.
- `references/openai-guide.md` — conformance with the OpenAI Realtime prompting guide: section mapping, formatting rules, easily missed elements, and LoyJoy's declared deviations. Read before every delivery.
- `references/debugging-and-delivery.md` — debugging workflow, symptom-to-layer routing table, side workflows (feedback analysis, change-proposal document, stakeholder mail, standard-prompt promotion, advisory setup), and the delivery checklist.

One script carries the checks that must not be done by hand:

- `scripts/prompt_check.py` — size against budget, duplicate sentences, overlap with the standard prompt, cross-reference resolution, tool consistency, search-discipline contradictions, and voice-formatting defects. Run it before every delivery.

Section names referenced without a file belong to this file.

## When to start

Invoke this skill when the user wants to:
- create or configure a complete phone agent in LoyJoy,
- build a new phone-agent prompt from scratch,
- optimize an existing prompt from test calls or customer feedback,
- debug a specific misbehavior,
- turn a workshop protocol, feature list, or use-case backlog into a working prompt,
- produce a change-proposal document for a customer.

## Rückfragen vor Plan

Before producing a plan or a draft, decide deliberately whether to ask first. Drafting on wrong assumptions wastes more time than one round of questions.

Ask first when any of the following is true:
- The target model is unknown (see Modell festlegen). This one is never skippable.
- The number of use cases, the target audience, or the success criterion of the call is not stated.
- Tool availability is unknown, or the brief names capabilities without naming tools.
- The source material is a raw workshop protocol, a feedback spreadsheet, or a transcript, i.e. unstructured input with implicit priorities.
- Two plausible interpretations would lead to materially different prompts.
- The change touches a live production agent and the desired blast radius is unclear.

Go straight to work when:
- The request is a narrow, well-specified single change ("Anrede auf Sie umstellen", "Notfall-Nummer korrigieren").
- The Ist-Stand is readable via MCP and the requested change is unambiguous against it.
- The user has already answered the same questions earlier in the conversation.

How to ask:
- One round, bundled. Short, decision-shaped questions, not open prose.
- Maximum four questions. Prioritize the ones that change the structure of the prompt, not the wording.
- State your own recommendation per question. The user wants a sparring partner, not a form.
- Never ask for information you can read yourself via MCP.

## Modell festlegen

**The target realtime model must be established before the first line of prompt text is written.** It is not a detail to clarify later: it decides prompt length budget, how defensive the rules have to be, whether reasoning effort and message channels are available, and how examples are interpreted. A prompt written for the wrong model class has to be rewritten, not patched.

Establish it in this order:

1. In Connected mode, read the configured model from the tenant instead of asking. If the tenant does not expose it, ask.
2. If the user does not know, ask which model class the deployment runs on and do not proceed with a draft until it is answered.
3. Only if the question genuinely cannot be answered in this session, write for the weakest plausible model (the non-reasoning class) and state that assumption in the first line of the delivery. Rules calibrated for the weaker model also work on the stronger one; the reverse is false.

### Model classes and what they change

| Class | Examples | Reasoning | Prompt implications |
| --- | --- | --- | --- |
| Non-reasoning realtime | `gpt-realtime-1.5` (LoyJoy default via Azure, EU data zone) | none | Needs more defensive rules, explicit flows, tighter scope. Blanket `never`/`always` are tolerated but still cost instruction-following budget. No message channels, no reasoning effort. |
| Reasoning realtime | `gpt-realtime-2`, `gpt-realtime-2.1`, `gpt-realtime-2.1-mini` | configurable effort | Set reasoning effort to low by default; raise only for multi-step planning use cases. Use message channels (commentary vs final) for preambles. Literal reading of `must`/`never`/`always` makes the agent rigid: use precise scope instead. |

Known behavior deltas worth asking about before promising anything:
- `gpt-realtime-2.1` improves alphanumeric recognition, silence and noise handling, and interruption behavior over `gpt-realtime-2`. If number capture is the pain point, a model upgrade may be the cheaper fix than another prompt round.
- `gpt-realtime-2.1` is tuned for open conversation and is reported to regress on deterministic, branched flows: unsolicited narration, commentary-channel leakage, and literal matching of examples instead of semantic intent. On a strictly scripted agent, verify the flow on real calls before migrating, and cut example lists further than you would on 1.5.
- Azure-hosted `gpt-realtime-1.5` in the EU data zone lacks Semantic VAD. Turn-taking complaints on that deployment are an infrastructure item, not a prompt item.
- Model names and availability change. Confirm the configured model per tenant; never infer it from this table.

### Record the model in the delivery

Every prompt delivery, change proposal, and stakeholder mail states the model the prompt was written for. A custom block handed over without that line will eventually be pasted onto a different model and blamed for the result.

## Arbeitsmodus: Advisory oder Connected

**Connected**: the LoyJoy MCP tools are available for the relevant tenant. Default whenever they are. Work against the real state of the agent, not a pasted snapshot.

**Advisory**: no MCP access (customer tenant, strict role separation, external stakeholder). Deliver copy-paste-ready text and setup instructions.

A tenant may contain a prototype or demo copy while the productive agent lives in the customer's own tenant. Never edit a prototype as a proxy for the real agent. Confirm which artifact is live before touching anything.

### Toolchain in Connected mode

Before the first connected write, load the `loyjoy-headless` skill (this plugin's dependency) and follow its rules for tenant selection, targeted reads, staging writes, round-trip validation, model checking, diff review, and publishing. This skill adds the phone-specific decisions; it does not replace the headless safety workflow.

1. `tenant_meta` and `processes_list` — confirm the tenant and resolve an existing agent by name. Never guess IDs.
2. `process_get_xml_grep` — read the smallest relevant XML fragments: the custom instruction, the configured tools, and the model configuration. Use `process_get_xml` only when the whole structure is genuinely needed.
3. `process_create`, `process_set_attribute`, `process_add_extension_element` — create or edit the staging process. Update an instruction with `process_set_attribute(..., name="text", value="...")`. Create a missing one with `process_add_extension_element(element_type="instruction", initial_attrs={"type":"custom","text":"..."})`.
4. `process_staging_xml_roundtrip_diff` — run after every write. Continue only when the result is identical.
5. `process_model_check` — BPMN correctness; inspect `LOCALE_NOT_MAINTAINED` issues for language gaps before delivery or publishing.
6. `process_diff` — review the complete production-to-staging change.
7. `process_publish` — only after the user explicitly requests or approves publication.

### Rules for write access

- Never write without having read the current state in the same session.
- Never write a block the user has not seen and approved.
- Run `process_staging_xml_roundtrip_diff` after every write and `process_diff` after the complete change.
- One logical change per write. Five requested items can be one write, but do not bundle unrelated cleanup into it silently. Name what you changed.
- Work in staging. Touch production only through `process_publish`, and only with explicit approval.

### Hard limits of Connected mode

- MCP can create, configure, validate, diff, and publish a process. It cannot create or upload assets, assign a phone number, configure external telephony routing, or perform a real voice call. Existing assets may only be referenced after their exact IDs and suitability have been verified.
- **Do not use `chat_completions_eval` for phone agents.** It is a text chat path and does not represent the voice channel.
- **Real test calls are currently not available from this workflow.** Nothing in the toolchain can place or evaluate a call. This does not lower the bar, it moves the work forward: run the anticipation pass (see Antizipation statt Testanruf) and report the voice test as open.

### What "complete phone agent" means

Report these levels separately, never as one state:

1. **Staging configuration complete**: the process is a phone agent, contains exactly one `AI_AGENT_SUBPROCESS`, has a custom instruction written for the confirmed model, its configured tools match the requested use cases, all process locales have complete i18n texts, XML round-trip is identical, model checking has no blocking findings, and the diff has been reviewed.
2. **Published**: the validated staging state was published after explicit user approval.
3. **Telephony ready**: a phone number and external routing are connected, the active standard voice prompt and realtime model are confirmed, and representative real voice calls passed.

MCP can reach levels 1 and 2. It cannot prove level 3, and no test call can be placed from this workflow at all. "Erstelle einen vollständigen Phone Agent" is therefore actionable, but the result is described as a fully configured staging process whose voice behavior is anticipated, not verified. Never describe an anticipation pass as a test.

## Order of operations

1. Determine the working mode (Connected or Advisory).
2. Connected: confirm the tenant, resolve the process, read the smallest relevant XML fragments. Record the instruction's BPMN element ID and current `text`. Advisory: request the current custom block as text.
3. **Fix the target model (see Modell festlegen). Do not draft before this is answered.**
4. Read the current LoyJoy standard voice prompt from the monorepo (see Den Standard-Prompt lesen). Do not ask the user which version is live. The custom block complements the standard, it does not duplicate it.
5. Identify the project type: new build, optimization, debugging, or proposal document.
6. Apply the Rückfragen-vor-Plan gate. Collect remaining constraints in one bundled round (see Clarification checklist).
7. Reconcile the tool inventory (see Tool-Inventar abgleichen).
8. Draft using the section structure and patterns in `references/patterns.md`. When iterating, always return the full updated custom block, not just the diff.
9. Run `scripts/prompt_check.py` (Prompt-Budget und Redundanzprüfung), then check the block against `references/openai-guide.md`.
10. Run the anticipation pass over the scenario matrix (see Antizipation statt Testanruf) and deliver its result with the prompt.
11. Connected: round-trip check after every write; before delivery run model checking, review locale issues, inspect the production-to-staging diff.
12. Work through the delivery checklist in `references/debugging-and-delivery.md`.
13. Report the three completeness levels separately. Publish only on explicit approval. Leave the real voice test visible as an open requirement until it has happened.

When test calls show problems, diagnose with the workflow and the layer table in `references/debugging-and-delivery.md` before changing anything.

### Creating a new phone agent in Connected mode

Do not create an empty process while essential requirements are unknown. Work through the Clarification checklist first.

Then follow "Create a phone agent" in the `loyjoy-headless` skill's `references/examples.md`. Its tool arguments and validation sequence are authoritative. The phone-specific gates:

1. `process_create`, then `process_staging_xml_roundtrip_diff`.
2. Set `name="loyjoy:type"` to `value="phone_agent"` on `element_id=process_id`, round-trip again.
3. Add exactly one `process_add_subprocess(process_id, parent_id=process_id, subprocess_type="AI_AGENT_SUBPROCESS")`, retain its ID, round-trip again.
4. Under that subprocess, add one custom `instruction` extension element with `type=custom` and the complete approved text. Round-trip.
5. Configure only tools required by the approved use cases. Use exact element types and attributes discovered through the schema and existing structure; never invent a tool name.
6. Add all customer-visible texts for every configured process locale. Run `process_model_check` and resolve every `LOCALE_NOT_MAINTAINED` issue introduced by the task.
7. `process_model_check`, resolve blocking findings, review `process_diff`.
8. Report what is complete and what remains for telephony readiness. Publish only after explicit approval.

### Editing an existing custom instruction in Connected mode

1. Locate the instruction with `process_get_xml_grep` and read its full current text.
2. Apply the methodology in this skill and obtain approval for the complete replacement text.
3. Write with `process_set_attribute(process_id, element_id, name="text", value="...")`.
4. Run `process_staging_xml_roundtrip_diff`, `process_model_check`, `process_diff`; inspect locale warnings as well as blocking findings.

## Clarification checklist

Before drafting, each item must be known from the brief, readable via MCP, or asked.

- Target realtime model and, for reasoning models, the intended reasoning effort.
- Target audience: B2C, B2B, or mixed (typical distribution if mixed).
- Language and form of address (Du / Sie / dialect), and whether callers in other languages are served at all.
- Tone keywords (warm, sober, energetic, formal).
- Tools available to the agent (knowledge search, product search, email, transfer, hangup, booking, custom integrations).
- Whether a knowledge base exists at launch or the agent must work without one.
- Email recipients for transcripts, callback requests, lead handoffs.
- Transfer target: real telephony transfer with hidden number, or spoken referral only.
- Working hours of the receiving human team, and whether the platform injects the current time of day rather than only the date.
- Emergency or safety scenarios requiring special routing (outages, gas leaks, claims with injuries, accidents).
- Sensitive data the agent must never collect or disclose.
- Number fields to capture (customer number, contract number, meter reading, booking reference) and whether DTMF keypad entry is available.
- Greeting placement: spoken by the agent or external (Twilio/IVR)? In LoyJoy setups it is usually external. Confirm explicitly.

## Architecture

LoyJoy phone agents use a two-layer prompt:

- **Standard voice prompt**: maintained by LoyJoy, applies to all tenants. Role basics, voice-output rules, turn-taking, tool mechanics, knowledge discipline, data capture, edge cases, anti-jailbreak, anti-hallucination, termination conditions, date injection, locale, response length.
- **Custom block**: tenant-specific, appended to the standard. Tenant role, allowed tools, scope, knowledge sources, business flows, customer-facing phrasing, sensitive-data negative list, escalation paths, email templates.

Hard rule: do not duplicate standard rules in the custom block. Only override or extend. When an override is needed, say explicitly that it overrides the standard, and place it in the section that owns the topic. A custom rule that merely asserts the opposite of a standard rule without declaring itself an override will lose in ambiguous cases.

When a mechanic turns out to be tenant-independent, promote it to the standard instead of copying it into the next custom block, and remove it from the custom blocks that already carry it. Number capture is the canonical example.

### Den Standard-Prompt lesen, nicht danach fragen

The standard is versioned in the LoyJoy monorepo and readable through the GitHub tools of the LoyJoy Admin MCP server. Read it at the start of every job instead of asking the user which version is live.

Source of truth, `owner=loyjoy`, `repository=loyjoy`:

```
libs/loyjoy-bpmn-pom/loyjoy-bpmn-extension/src/main/java/
  com/loyjoy/bpmn/extension/ai/instructions/InstructionSubTypesEnum.java
```

Read it with `github_repos_contents_get_string`. The prompt is not a resource file: every building block is a string constant in that enum. The blocks a phone agent receives:

| Constant | Covers |
| --- | --- |
| `ROLE_PHONE` | role, scope boundary against other companies |
| `BASE_PHONE` | turn-taking, acknowledge-first, bridging before tool calls, search obligation, tool budget (four calls per user message), URLs |
| `PHONE_PRONUNCIATION_DEFAULT` | voice output, no markdown, spoken numbers and dates, spelled-out email addresses, digit-by-digit readback, data capture |
| `REPLY_LENGTH_PHONE` | one to two sentences per turn |
| `ANSWER_LANGUAGE_PHONE`, `ANSWER_LANGUAGE_QUESTION` | locale via `${displayLanguage()}` |
| `CONTEXT_DATE` | date injection via `${localDateTime()}` |
| `NAME_DEFAULT`, `REASONING_DEFAULT`, `PERSONALITY_DEFAULT`, `GUARDRAIL_ALL` | shared with chat agents |

Which blocks a given agent type actually gets is decided in `seedPhoneAgent(...)`:

```
services/loyjoy-manager/loyjoy-manager-core/src/main/java/
  com/loyjoy/manager/service/instructions/impl/InstructionsSeedServiceImpl.java
```

The final system message is assembled at runtime in `getSystemMessageWithInstructions(...)` (`services/loyjoy-runtime/loyjoy-runtime-ai/.../util/AiAgentSubProcessUtils.java`), which concatenates the active instructions with blank lines. Chat agents use a different set (`ROLE_DEFAULT`, `BASE`, `OUTPUT_FORMAT_MARKDOWN`, `REPLY_LENGTH_DEFAULT`, `CONTEXT_WEBSITE`, `ANSWER_LANGUAGE_DEFAULT`), which is why chat rules must never be copied into a voice block.

Two properties of the current standard that change how a custom block is written:
- `PHONE_PRONUNCIATION_DEFAULT` is written in German while the other blocks are English. A tenant served in another language needs an explicit language override, and a pronunciation rule in that language, in the custom block.
- The phone tool budget is four calls per user message and resets with every new user message. A use case that needs more lookups than that per turn has to be restructured, not prompted harder.

Extract the standard into a local file for the mechanical checks:

```
python3 scripts/prompt_check.py custom_block.txt --standard standard_prompt.txt
```

Every rule the checker reports as duplicated against the standard is deleted from the custom block or rewritten as a declared override. There is no third option.

## Wartbare Prompt-Struktur

A phone-agent prompt is a long-lived artifact changed by several people over months. Structure it so the next change is cheap. This matters more than elegance of any single instruction.

1. **One rule, one place.** Every behavior is defined exactly once. If two sections need it, one references the other by section name. Duplicated rules drift apart and then contradict each other. Conflicting instructions are the single largest quality loss on realtime models.
2. **Shared building blocks are centralized.** Data capture, farewell, escalation, and email templates are their own sections. Use cases reference them ("nutze Datenerfassung, Felder 1 bis 4") instead of restating the steps.
3. **Use cases are self-contained and named.** Each has a goal, the steps, sample phrases, and an explicit exit ("wechsle in Gesprächsabschluss"). Adding a use case must not require editing existing ones.
4. **Stable section labels.** `## N. Name` headings that stay constant across versions, so change requests and review comments can reference them and diffs stay readable.
5. **Abstract the requirement, do not enumerate the instances.** One rule covering a class beats ten examples of it. Examples disambiguate only: two or three where the class boundary is genuinely unclear. Long example lists teach the model to pattern-match instead of generalize, and they are the main driver of prompt bloat. Reasoning models match examples more literally, so cut harder there.
6. **Interaction sequences are numbered flows, not bullet lists.** Anything with a state (asked, received, read back, confirmed, done) is an ordered flow. Bullets carry no order and no state, so the model re-fires earlier steps. This is the most reliable cause of loops in data capture. Everything that is not a sequence stays a short bullet, never a paragraph.
7. **Preconditions come before steps.** A condition written after the flow ("only take this down outside business hours") reads as an afterthought and is ignored.
8. **One term, one meaning.** Reserve a phrase for exactly one actor and one action. Before adding a rule, search the prompt for the terms you are about to use. A phrase that means one thing for the caller and another for the agent will collapse into a loop.
9. **Length discipline.** See Prompt-Budget und Redundanzprüfung. Before adding, check whether an existing section can absorb the change.
10. **No dead weight.** Rules for dropped use cases, removed tools, or scenarios that never occurred get deleted, not commented out.

## Prompt-Budget und Redundanzprüfung

Run this before every delivery, on every iteration, not only on the first draft. **This check is mechanical and is not done by hand.** Measuring size, spotting near-duplicate sentences, resolving cross-references, and finding overlap with the standard are exactly the tasks a model performs unreliably and a script performs exactly.

### The checker

```
python3 scripts/prompt_check.py custom_block.txt \
    --standard standard_prompt.txt \
    --budget single|service|complex
```

Write the current custom block and the extracted standard prompt to files first (in Connected mode, take the block from `process_get_xml_grep`, the standard from the monorepo). The checker reports:

| Check | What it catches |
| --- | --- |
| `size` | words, characters, token estimate, verdict against budget and hard ceiling |
| `duplicate` | sentences inside the block that repeat each other above 70 percent similarity |
| `standard` | sentences that duplicate a standard rule, which must be deleted or declared as an override |
| `sections` | duplicate section names, and shared sections no use case references |
| `crossref` | "siehe X" pointing at a section that does not exist |
| `tools` | tool lines without an eagerness class, tools no use case uses |
| `search` | a term appearing in both a must-search and a no-search rule |
| `format` | markdown, emoji, pseudocode in a voice prompt |
| `primitives` | validation that depends on counting digits |
| `flow` | a stateful sequence written as a bullet list instead of a numbered flow |
| `variety` | sample phrases without an anti-lock-in line, or no variety rule at all |
| `date` | a hardcoded date without a date template |

Exit code 1 means at least one ERROR. **Errors are fixed before delivery.** Warnings are decided deliberately and the decision is stated; they are not ignored silently. INFO lines are context, not findings.

The checker finds mechanical defects. It cannot tell whether a rule is correct, whether a flow matches the business process, or whether the tone fits the brand. Those stay with you.

### Budgets

| Scope | Budget | Hard ceiling |
| --- | --- | --- |
| Custom block, single use case | 800 tokens | 1,500 |
| Custom block, typical service agent (3 to 6 use cases) | 2,000 tokens | 3,000 |
| Custom block, complex multi-flow agent | 3,000 tokens | 4,000 |
| Standard plus custom, total | 5,000 tokens | 7,000 |

Over budget the prompt still works, but every further change gets more expensive and instruction following degrades unevenly. Over the hard ceiling, stop adding and restructure. On reasoning models the prompt is re-read every turn, so the budget is also a latency and cost lever.

**Cut in this order** when over budget: example lists first, then duplicated rules, then use cases the customer dropped, then rules for tools that are not configured, then wording. Never cut safety sections, the sensitive-data list, or the emergency numbers to save length.

### Self-critique pass

The checker does not read for meaning. After it comes back clean, re-read the block once against four questions and fix what you find: which instructions are ambiguous, which terms are undefined, which pairs conflict, which assumptions are unstated. Apply fixes surgically; a rewrite at this stage loses the review history.

### Report

Deliver the checker output together with the prompt: measured size, what was removed, what was added, remaining warnings and why they were accepted.

## Antizipation statt Testanruf

Real test calls are not available from this workflow. That does not make the verification step optional, it changes what it consists of: instead of observing behavior, you predict it, in writing, against the prompt you just wrote. Done seriously this catches the majority of defects that a first test call would have caught, and it produces the script that whoever does get to call can work through.

Rules for the pass:

- **Simulate against the text, not from memory.** For each scenario, walk the caller's turns one by one and name the section and the sentence the agent would follow. A prediction without a cited sentence is a guess and does not count.
- **Predict the failure, not the success.** Assume the caller is uncooperative: interrupts, answers a different question, gives a compound number, changes topic mid-flow, says "okay" ambiguously. The happy path is the least informative case.
- **Two sections firing on the same turn is a finding.** Whenever two sections could both match a caller utterance, write down which one wins and why. If you cannot say, the prompt cannot either.
- **Mark every prediction as a prediction.** It is a hypothesis until a human calls. Never phrase it as a result.

The scenario matrix to run, twenty rows plus one per configured use case, is in `references/debugging-and-delivery.md`.

### Deliverable of the pass

A short table: scenario, predicted behavior, the section and sentence it comes from, and a verdict of ok, risk, or defect. Defects are fixed before delivery. Risks are listed for the first real call, ordered by severity, so whoever calls knows what to try first.

State in one sentence that this is anticipation and that levels of certainty differ from a test. Hand the matrix over as the test script.

## Änderungen am bestehenden Prompt: Entfernen vor Verbieten

The most common way a prompt degrades is scar tissue: the agent does something unwanted, and instead of removing the instruction that caused it, a negative rule is stacked on top. The prompt then contains both an instruction and its prohibition. It grows, it contradicts itself, and instruction following degrades across the board.

Default on every change request: **find and remove or rewrite the cause first.**

1. Locate the instruction that produces the behavior. Search the custom block first, then the standard. When the custom block looks clean, the cause is usually in the standard, and the right fix is a change to the standard plus a declared override as a stopgap.
2. If the cause is in the custom block, remove or narrow it. A rule whose scope was too wide gets a precise scope, not a counter-rule.
3. If the behavior comes from a use case that is no longer wanted, delete the use case rather than telling the agent not to run it.
4. Only if no removable cause exists is a negative rule the right answer. Place it in the section that owns the topic, not at the end.

Negative rules are legitimate, and belong in the prompt explicitly, for:
- legal or compliance boundaries (sensitive-data list, no advice in regulated domains),
- scope boundaries against caller-initiated topics the prompt never mentions (competitors, off-topic chat),
- overriding standard-prompt behavior that cannot be edited per tenant,
- suppressing a model tendency with no source in the prompt at all (invented tool names, invented URLs, defaulting to the free tier).

Judgment rule: if you can point to the sentence that causes the behavior, remove that sentence. If you cannot, a negative rule is justified. State which of the two you did and why, so the user can disagree.

### Hygiene rules for the edit itself

These are the mistakes made while fixing other mistakes. They cost more test calls than the original bugs.

- **Replace, do not add in parallel.** A better phrasing means the old one is deleted in the same edit. Two formulations for the same moment produce unpredictable behavior.
- **Grep before you write.** Search for every key term in your new rule. If it already appears, decide whether to reuse it consistently or pick a different term.
- **Sweep the dependents when removing a rule.** A deleted rule usually has references elsewhere. Search for them in the same edit.
- **After the third patch to one section, rewrite the section.** Three rounds of patching means the structure, not the wording, is wrong.
- **Do not build a rule on a primitive the model is bad at.** Counting, arithmetic across many items, and precise length control are unreliable. Validation that depends on them produces false positives on correct data, which is worse than no validation.
- **After a series of edits to one section, run the anticipation pass over that section** before touching it again, and say that it is unverified. Repeated blind edits compound.
- **Verify by search, not by memory.** After an edit round, grep for the terms you removed and for every cross-reference, and confirm each resolves.

## Tool-Inventar abgleichen

Prompt and tool configuration must match. In Connected mode, inspect the configured tool elements with `process_get_xml_grep`. Reconcile on every job.

1. Derive the required tool set from the use cases (knowledge search, email, transfer, hangup, booking, custom integrations).
2. Compare against what is actually configured.
3. **Missing tools**: name them explicitly and ask the user to add them before the prompt goes live. Never write a prompt referencing a tool that does not exist. The model will invent the name or claim success without calling anything.
4. **Superfluous tools**: a configured tool that no use case needs is an active risk, because the model will eventually use it. Ask the user to deactivate it. Do not solve this in the prompt with a negative rule. A stray web search tool is the classic case: it silently turns a curated knowledge agent into an open-web agent.
5. **Name mismatch**: the prompt uses the exact configured tool name. Correct the prompt, not the configuration, unless the configured name is itself misleading.
6. Deliver the result as a short soll/ist list the user can act on in one pass.

## Mandatory voice-output rules (in standard, do not repeat)

The LoyJoy standard voice prompt already enforces these. The custom block inherits them by being appended and must not restate them:

- No markdown, no bullet syntax, no list rendering, no emoji.
- Numbers, dates, prices, currencies spoken as words.
- URLs spoken in pronounceable form in the active language (German "Punkt", not English "dot").
- Email addresses spelled out.
- Phone numbers, IDs, codes spoken character by character.
- Acknowledge-first preamble where it hides latency.
- Verbosity capped at one to two sentences per turn.
- Never claim a tool ran successfully unless it did.

A tenant-specific override (e.g. a pronunciation rule) is stated explicitly in the custom block as an override.

## Style for working with the user

- Compact answers. No filler, no unnecessary em dashes.
- Numbered lists where the user needs to reference items by number.
- Honest diagnostics. When a problem cannot be solved at the requested layer, say so plainly and route it.
- When iterating, always return the full updated artifact, not just the diff.
- Sparring tone: push back when the proposed change creates a new problem, especially when it would add scar tissue instead of removing a cause, or when a literal reading would overcorrect.
- When the user proposes a better solution than yours, say so plainly and adopt it.
- Mark exactly what is new and what was removed. Removals matter as much as additions.
- **Measure before promising.** Do not quote a reduction in words, tokens, or lines without counting first, and report the measured result afterwards even when it undershoots.
- **Own your own regressions explicitly.** When a symptom traces back to your previous edit, say so in the first sentence.
- Be transparent about where a finding came from, including when it came from an artifact you were later asked not to use.
- Never recommend chat-specific patterns for voice prompts.

