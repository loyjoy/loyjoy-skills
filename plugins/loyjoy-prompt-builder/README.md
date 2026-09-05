# loyjoy-prompt-builder

Build, optimize, and debug custom prompts for LoyJoy chat agents on top of the LoyJoy standard chat prompt.

Part of [LoyJoy Skills](https://github.com/loyjoy/loyjoy-skills) — the official collection of Agent Skills and Claude Code plugins for the [LoyJoy Platform](https://www.loyjoy.com).

## What it does

1. **Layer** customer-specific rules onto the LoyJoy standard chat prompt instead of rewriting it — the standard carries the universal mechanics, the custom block carries what is specific to the tenant.
2. **Cover** the recurring chat patterns: product consultation, routine recommendations, multi-assortment advice, exclusion lists, and URL whitelist fallbacks.
3. **Enforce** the mechanics that keep a chat agent reliable: tool-call budget, search strategy, context persistence across follow-up questions, and protection against hallucinated URLs.
4. **Debug** misbehavior — trace wrong links, lost context, or skipped searches back to the prompt line that caused them.

## Chat vs. voice

This is the chat counterpart to [`loyjoy-phone-agent-builder`](../loyjoy-phone-agent-builder). Chat patterns (markdown links, bullet lists, link format consistency) and voice patterns (acknowledge-first, no markdown, spoken pronunciation, digit confirmation) do not translate between the two channels — the skill handles that boundary explicitly.

## Installation

```bash
/plugin marketplace add loyjoy/loyjoy-skills
/plugin install loyjoy-prompt-builder@loyjoy-skills
```

Depends on [`loyjoy-headless`](../loyjoy-headless), which is installed automatically.

## Requirements

1. A [LoyJoy](https://www.loyjoy.com) account with access to the **LoyJoy Manager MCP server**.
2. An Agent Skills–compatible AI assistant, e.g. [Claude Code](https://code.claude.com) or Claude.

## License

[Apache-2.0](../../LICENSE) © [LoyJoy GmbH](https://www.loyjoy.com)
