# loyjoy-phone-agent-builder

Create, configure, iterate, and debug LoyJoy phone agents and their custom voice prompts.

Part of [LoyJoy Skills](https://github.com/loyjoy/loyjoy-skills) — the official collection of Agent Skills and Claude Code plugins for the [LoyJoy Platform](https://www.loyjoy.com).

## What it does

1. **Create** telephony-ready LoyJoy AI Agents in staging, end to end.
2. **Build** custom voice prompts using the standard-plus-custom architecture — one maintainable, layered prompt instead of ad-hoc rewrites.
3. **Iterate** on real test calls — turn concrete call feedback into concrete prompt changes without regressing existing behavior.
4. **Debug** misbehavior — trace acknowledge-first, spoken-number, digit-confirmation, and transfer-with-consent issues to their prompt sources.

## Voice vs. chat

This is the voice-specific counterpart to `loyjoy-prompt-builder` (chat). Voice patterns (acknowledge-first, no markdown, spoken pronunciation, character-by-character digit confirmation, transfer with consent) and chat patterns (markdown links, bullets, link consistency) do not translate between the two channels — the skill handles that boundary explicitly.

## Installation

```bash
/plugin marketplace add loyjoy/loyjoy-skills
/plugin install loyjoy-phone-agent-builder@loyjoy-skills
```

Depends on [`loyjoy-headless`](../loyjoy-headless), which is installed automatically.

## Requirements

1. A [LoyJoy](https://www.loyjoy.com) account with access to the **LoyJoy Manager MCP server** and phone-agent capabilities.
2. An Agent Skills–compatible AI assistant, e.g. [Claude Code](https://code.claude.com) or Claude.

## License

[Apache-2.0](../../LICENSE) © [LoyJoy GmbH](https://www.loyjoy.com)
