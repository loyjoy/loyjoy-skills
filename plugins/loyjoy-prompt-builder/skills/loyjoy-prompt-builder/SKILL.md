---
name: loyjoy-prompt-builder
description: Use this skill whenever creating, optimizing, or debugging a custom prompt for a LoyJoy chat agent (web chat, in-app chat, embedded chat widget). Covers methodology for combining the LoyJoy standard chat prompt with customer-specific extensions, common patterns for product consultation, routine recommendations, multi-sortiment consultation, exclusion lists, URL whitelist fallbacks, mechanic rules (tool budget, context persistence, URL hallucination protection), model-specific tuning for Gemma 4 31b and Gemma 4 31b Thinking, and debugging techniques. Triggers include "Custom-Prompt für Chat", "LoyJoy Chat-Prompt optimieren", "Chat-Agent debuggen", "Kunden-Erweiterung für Chat-Standard-Prompt", "Produktberatung im Chat", "Sortimentsregeln im Chat", "Gemma Thinking Prompt". For phone or voice agents, use the loyjoy-phone-agent-builder skill instead.
---

# LoyJoy Prompt Builder (Chat)

This skill helps build and iterate custom prompts for LoyJoy chat agents (web chat, in-app chat, embedded widgets). It captures the methodology developed across multiple chat projects and turns it into a repeatable workflow.

For phone, voice, or speech-to-speech agents, do not use this skill. The voice-specific patterns, anti-patterns, and debugging steps are different. Use the `loyjoy-phone-agent-builder` skill instead.

## How to start a session with this skill

When the user invokes this skill, do this in order:

1. **Confirm channel.** Verify that the project is actually a chat agent (text in, text out, web or app widget). If it is a phone / voice agent, switch to `loyjoy-phone-agent-builder` immediately.
2. **Confirm the current standard chat prompt.** The file `standard_prompt_web.md` in this skill folder contains the last known version of the LoyJoy chat standard, dated in its header. Open it and ask: "Verwendet ihr noch den Standard-Prompt vom [Datum aus Header]? Falls nicht, gib mir den aktuellen, dann arbeite ich darauf." Wait for confirmation or a paste before drafting.
3. **Identify the project type** through AskUserQuestion if not obvious: new customer block from scratch, optimization of existing block, debugging a misbehavior, or migration from old to new architecture.
4. **Always ask actively which model the agent will run on** (Gemma 4 31b Thinking, GPT-5.4, Claude Opus/Sonnet, etc.). This changes how defensive the custom block needs to be. If the user does not specify a model or remains unclear after asking once, default to **Gemma 4 31b Thinking** — this is the LoyJoy standard model for chat agents. The non-thinking Gemma 4 31b is no longer in active use (vorerst). Tune for the Thinking variant by default (see Tier 2 below): state constraints once and clearly, rely on the model's internal reasoning for negative constraints and priority order, and watch reasoning-token cost and latency. Note the assumed model explicitly in your response so the user can correct it if needed.

## Architecture: standard plus custom block

LoyJoy uses a two-layer prompt architecture:

- **Standard chat prompt** (generic, applies to all chat tenants): universal mechanics like tool budget, search strategy, URL discipline, context persistence, link format, internal checklist. Maintained centrally, evolves over time. The current version lives in `standard_prompt_web.md` and contains three runtime placeholders: `${tenantName()}`, `${localDate()}`, `${displayLanguage()}` (plus `<URL>` for the current page).
- **Custom block** (customer-specific, appended to the standard): role specifics, product/sortiment knowledge, recommendation priorities, naming rules, fallback URL whitelist, sequence rules for sales or consulting flows.

The custom block must not duplicate the standard. If a rule is already in the standard, do not repeat it in the custom block unless a customer-specific override is needed.

## Universal mechanic rules (already in the standard)

Do not reinvent these in custom blocks:

- Tool call budget per user message, outcome-oriented, with a safety limit (currently six) as runaway protection, not as a savings target.
- Budget resets fully with every new user message; tool calls from earlier turns do not count.
- A tool call in the current turn is required before naming or linking a product, item, or URL.
- The system message is orientation only, not an answer source for concrete product data. Specific products, variants, prices, availability, URLs must be confirmed by a tool call even if they appear in the system message.
- URL hallucination protection: URLs are never invented, guessed, or reconstructed. Only verbatim retrieval URLs or whitelist URLs.
- Link format consistency: link text equals full product or topic name, no parentheses, no suffixes like "(Link)".
- Internal checklist before each final answer: facts from retrieved context, current-turn search, verbatim URLs, link text matches target, context of last named entity maintained, language matches user.
- Context persistence: follow-up questions relate to the last concretely named entity, not to an earlier broader question.

## Working method for a new custom block

1. **Research the customer's website.** Use web_fetch to map the product structure, services, brand collections, gewerk bundles. Capture the URL schema and the structure of important sortiment pages.
2. **Ask clarifying questions** with AskUserQuestion: language, target audience (B2C/B2B/mixed), key topics to cover, known pain points, brand priorities, exclusion lists.
3. **Separate declarative knowledge from procedural rules** when drafting:
   - Declarative: structure of the product range, brand collections, services, gewerk bundles. Static and rarely changes.
   - Procedural: how to recommend, what to prioritize, exclusion rules, sequence rules. Evolves with feedback.
4. **Write in prose, in German** (unless the customer prefers English). Avoid heavy formatting. Use clear paragraph breaks and section headers.
5. **Length discipline.** The custom block should match the customer's complexity, not the maximum possible. Start lean, expand with feedback. Over-stuffed blocks hurt small models more than they help. For Thinking variants, over-stuffing also inflates reasoning-token cost and latency.

## Common chat-specific patterns

### Product consultation with routines (B2C beauty, cosmetics)

- Always recommend a routine, not a single product.
- Routine schema per category, e.g. hair: Shampoo, Kopfhautlotion, Conditioner, Treatment; skin: Reinigung, Toner, Spezialpflege, Creme.
- Sequence rule after a routine recommendation: define explicit ordered next steps for follow-up "Ja" confirmations (Wirkung → Anwendung → Profitipp → Cross-Sell → ergänzende Produkte; one step per "Ja"). Without this rule, the agent repeats the same routine on "Ja".

### Multi-sortiment consultation (B2B trade, distribution)

- Map applications that span multiple sortiment categories (e.g. Möbel = Bad & Küche, Wohnmöbel, Holzmöbel, Gartenmöbel).
- Use synonym clusters to broaden search (Putz/Verputz; lila/violett/aubergine; GK-Platte/Gipskartonplatte).
- Define Empfehlungs-Prioritäten explicitly (Hausmarke first, then alternatives).

### Exclusion lists for inactive products

- Block specific product lines or identifiers (e.g. all products with "Farbrezepte" in name).
- Brand cleansing pattern: when user asks for an excluded product, communicate "no longer available" plus alternative from active assortment.

### Fallback URL whitelist

- For customers where retrieval URLs are unreliable, define a static whitelist of verified URLs: sortiment overviews, brand microsites, tools like store finder or login.
- Without whitelist plus with strict URL rules, the agent fails to link anything.
- The whitelist must be maintained by the customer when their website changes (404 risk).

## Debugging techniques

### Symptom: agent hallucinates URLs

- Check whether a search happened in the current turn (open the technical message in the LoyJoy backend to see the knowledge_search tool call).
- If no search happened, the budget interpretation is likely cumulative across turns instead of per turn. Verify the reset rule is present and explicit.
- If a search happened but the URL is invented, the retrieval lacks proper URL data. Inspect the source page in the browser to see what the crawler extracted.

### Symptom: agent uses generic landing page instead of specific product page

- Inspect the source page in the browser. Check whether the product links have meaningful text content (anchor text, title, aria-label, image alt).
- If link texts are empty (e.g. color swatches are just colored circles), the crawler extracts `[](URL)` and the agent cannot map name to URL.
- Fix is at the data/crawler layer, not in the prompt. Crawler should derive name from URL slug as fallback.

### Symptom: agent repeats previous answer when user says "Ja"

- Add explicit sequence rule for "Ja" follow-ups with ordered next steps.
- Forbid repetition of already-given content.
- Define what the agent does at each step ("erst Wirkung erklären, dann Anwendung, …").

### Symptom: agent skips search and uses prompt knowledge

- The system message contains too much concrete product data. The model treats it as the answer source.
- Add explicit clarification: "this knowledge section is orientation only, not an answer source for concrete product data".
- For small non-thinking models (Gemma 31b), the rule must be very explicit and possibly repeated near the relevant section. Thinking variants usually respect it after a single explicit statement.

### Symptom: agent does not follow priority order (e.g. brand A before brand B)

- Compliance problem rather than knowledge problem.
- Move the priority rule to a more prominent position.
- Add a negative constraint ("never name brand B before brand A").
- For strong models and Thinking variants, this is usually enough; for small non-thinking models, also repeat in the final checklist.
- If still unreliable: sort in code after retrieval, before passing to model.

## Model-specific considerations

Default assumption when no model is specified: **Gemma 4 31b Thinking** (LoyJoy standard, Tier 2 below). The non-thinking Gemma 4 31b (Tier 1) is no longer in active use (vorerst) and is kept here only as a fallback reference for legacy tenants. Always confirm the model with the user.

Three tiers, from most to least defensive:

### Tier 1: Small non-thinking models (Gemma 4 31b and similar — legacy, no longer in active use)

Kept for reference only. Use the more defensive tuning here if a legacy tenant still runs the non-thinking model:

- Strict, explicit rules needed.
- Repetition of key constraints helps.
- Negative constraints often ignored under retrieval pressure. Consider data-layer filtering as a fallback.
- Tool call limits should be soft (safety limit), not hard ceiling.
- Context persistence rule essential.
- Sequence rules for follow-ups must be explicit; the model rarely infers them.

### Tier 2: Small Thinking models (Gemma 4 31b Thinking — LoyJoy default)

This is the default LoyJoy chat model. It runs internal reasoning before answering, which changes the tuning:

- **Less repetition needed.** State each key constraint once, clearly. Repeating the same rule three times mostly wastes tokens and can clutter the reasoning trace. Drop the "repeat near the relevant section" duplication that Tier 1 relies on.
- **Negative constraints and priority order become reliable.** Multi-step rules like "never name brand B before brand A" and "exclude all Farbrezepte products" are usually followed after the reasoning step. Data-layer filtering becomes a robustness nice-to-have, not a functional necessity.
- **Sequence logic is partly self-inferred.** The model can derive ordered "Ja" follow-up steps from a compact description; you still name the steps, but you do not need to spell out every micro-instruction.
- **Watch reasoning-token cost and latency.** Thinking variants emit reasoning tokens on top of the answer. Over-stuffed custom blocks and redundant constraints inflate cost and time-to-first-token noticeably. Length discipline matters more here than for non-thinking models. Keep the block lean.
- **Do not over-trim the standard mechanics.** Tool budget, current-turn-search rule, URL hallucination protection, and context persistence still belong in the prompt. Thinking does not invent retrieval discipline on its own.
- **Internal checklist:** keep it, but a single consolidated checklist is enough. No need to mirror it inside individual sections as Tier 1 sometimes does.

### Tier 3: Strong models (GPT-5.4, Claude Opus/Sonnet)

- Many defensive rules are overengineered. The model handles many things implicitly.
- Less need for repetition.
- Tool call decisions self-regulate well.
- Customer-specific rules still need to be explicit (these are not model-known).
- Long context tolerated (e.g. eighteen example routines OK), but token cost and maintainability remain real concerns.
- Architectural improvements (routines in data, post-processing URL validation) become wartability questions rather than functional necessity.

## Routing problems correctly: prompt vs other layers

When a problem appears, diagnose which layer it belongs to before drafting a prompt fix:

- **Prompt-fixable:** sortiment logic, naming, sequence behavior, style, exclusion of clearly named items, role behavior.
- **Retrieval-fixable:** product data quality, URL-linktext mapping, index structure, missing fields like color name on color swatches.
- **Pipeline-fixable:** URL validation, hard limits enforcement, tool routing, calendar lookups, post-processing.
- **Model-upgradeable:** compliance with complex negative constraints, fine-grained priority order, multi-step internal reasoning. Upgrading a non-thinking small model to its Thinking variant often resolves compliance issues that no amount of prompt tightening fixed.

A common failure mode is to try to fix retrieval problems in the prompt. The prompt cannot create data that is not in the index.

## Iterative refinement pattern

Customer feedback loops are central. Typical iteration sequence:

1. Initial release based on website research and clarification.
2. After first user tests: tighten rules where compliance is weak. Distinguish compliance issues from architecture issues.
3. After deeper testing: identify retrieval and data limits separate from prompt limits.
4. Architecture handoff: explicitly route problems that the prompt cannot solve to data, retrieval, post-processing, or model upgrade.

Be a sparring partner, not a yes-person. When the customer asks for the third prompt iteration to fix something that is a retrieval problem, say so clearly and route to the right team. When repeated compliance tightening fails on a non-thinking small model, propose switching to the Thinking variant instead of stacking more rules.

## Style for prompt outputs

When drafting custom blocks, use:

- Prose, no heavy formatting unless the customer requested it.
- German for customer-facing rules and examples.
- English for the universal mechanic block if the customer's standard is English.
- Minimal lists unless explicit enumeration is required.
- Clear section headers.
- Verbal cues like "verbindlich", "niemals", "immer" for hard rules. Soft cues for soft preferences.
- A final checklist that combines all critical checks, not multiple checklists.

## Style for communication with the user (LoyJoy team)

When working with a LoyJoy team member through this skill:

- Be a sparring partner, not a yes-person.
- Numbered lists where the user needs to reference items.
- No filler phrases, no unnecessary em dashes.
- Honest diagnostics: when a problem is not prompt-fixable, say so and route to the right layer.
- Compact answers, but substantive. Brevity does not mean shallow.
- When uncertain about a customer specifics, ask via AskUserQuestion before drafting.
- When iterating on an existing custom block, return the full updated block rather than only the diff. Copy-paste-ready output is preferred.

## When NOT to use this skill (use loyjoy-phone-agent-builder instead)

Switch to `loyjoy-phone-agent-builder` whenever:

- The agent speaks or listens (telephony, SIP, WebRTC voice).
- The model is `gpt-realtime-1.5`, `gpt-realtime-2`, or any other speech-to-speech model.
- The user mentions Phonebot, Voicebot, Telefonassistent, Sprachassistent, Anrufer, IVR, Twilio, call recording, latency, turn-taking, VAD, barge-in, or echo.
- The work involves voice-only patterns: bridging preambles, character-by-character digit confirmation, transfer with consent, Notfall-Vorrang, KI-Transparenz disclosure.

Chat patterns (markdown links, bullet lists, long enumerated answers, link format consistency) do not translate to voice. Voice patterns (acknowledge-first, no markdown, spoken pronunciation rules) do not apply to chat.

## File overview in this skill

- `SKILL.md`: this file.
- `standard_prompt_web.md`: last known version of the LoyJoy chat standard prompt with date header.

When the chat standard evolves, update `standard_prompt_web.md`, adjust the date in its header, and commit the change. The voice standard is maintained in the `loyjoy-phone-agent-builder` skill.
