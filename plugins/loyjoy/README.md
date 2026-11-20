# LoyJoy

Build, edit, compare, and publish LoyJoy AI Agents for chat and phone through the LoyJoy Manager MCP server.

Part of [LoyJoy Skills](https://github.com/loyjoy/loyjoy-skills) — the official collection of Agent Skills and Claude Code plugins for the [LoyJoy Platform](https://www.loyjoy.com).

## Skills

### loyjoy-headless

1. **Inspect** agent configurations — read the BPMN XML that defines any LoyJoy AI Agent, grep for specific elements, and read templates or views.
2. **Edit** safely — narrow, semantic changes (instructions, prompts, modules, subprocesses, knowledge, tools, branding, locales) instead of full-document rewrites.
3. **Compare** staging against production — surface unpublished diffs before every write so unrelated changes never silently ride along.
4. **Publish** with intent — confirm tenant, confirm scope, then promote staging to production.

Trigger it whenever a LoyJoy agent, process, module, or BPMN process is involved — including German phrasing like "Agent anpassen", "Modul hinzufügen", "Staging veröffentlichen".

### loyjoy-phone-agent-builder

1. **Create** telephony-ready LoyJoy AI Agents in staging, end to end.
2. **Build** custom voice prompts using the standard-plus-custom architecture — one maintainable, layered prompt instead of ad-hoc rewrites.
3. **Iterate** on real test calls — turn concrete call feedback into concrete prompt changes without regressing existing behavior.
4. **Debug** misbehavior — trace acknowledge-first, spoken-number, digit-confirmation, and transfer-with-consent issues to their prompt sources, and route the ones that are not prompt-fixable to the right layer.
5. **Gate on the model** — the target realtime model (`gpt-realtime-1.5`, `gpt-realtime-2.1`, …) is fixed before the first line of prompt text, because it decides length budget, defensiveness, reasoning effort, and how examples are read.
6. **Keep prompts lean** — `scripts/prompt_check.py` measures size against budget and sweeps for duplicates, overlap with the standard prompt, dangling cross-references, tool inconsistencies, and voice-formatting defects. Errors block delivery.
7. **Anticipate instead of guess** — where real test calls are not available, a 20-scenario anticipation matrix predicts behavior against the written prompt and doubles as the call script.

The standard voice prompt is not duplicated in the skill. It is read at runtime through the `instruction_sub_types_get` tool of the LoyJoy Manager MCP server. Voice patterns and chat patterns do not translate between the two channels; the skill handles that boundary explicitly.

## Installation

```bash
/plugin marketplace add loyjoy/loyjoy-skills
/plugin install loyjoy@loyjoy-skills
```

## Requirements

1. A [LoyJoy](https://www.loyjoy.com) account with access to the **LoyJoy Manager MCP server** (and phone-agent capabilities for the phone agent builder).
2. An Agent Skills–compatible AI assistant, e.g. [Claude Code](https://code.claude.com) or Claude.

The MCP server is preconfigured in this plugin at `https://app-cloud.loyjoy.com/mcp`.

## License

[Apache-2.0](../../LICENSE) © [LoyJoy GmbH](https://www.loyjoy.com)
