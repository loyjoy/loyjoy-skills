# loyjoy-headless

Inspect, edit, compare, and publish LoyJoy agent configurations through the LoyJoy Manager MCP server.

Part of [LoyJoy Skills](https://github.com/loyjoy/loyjoy-skills) — the official collection of Agent Skills and Claude Code plugins for the [LoyJoy Platform](https://www.loyjoy.com).

## What it does

1. **Inspect** agent configurations — read the BPMN XML that defines any LoyJoy AI Agent, grep for specific elements, and read templates or views.
2. **Edit** safely — narrow, semantic changes (instructions, prompts, modules, subprocesses, knowledge, tools, branding, locales) instead of full-document rewrites.
3. **Compare** staging against production — surface unpublished diffs before every write so unrelated changes never silently ride along.
4. **Publish** with intent — confirm tenant, confirm scope, then promote staging to production.

## How it works

The skill packages LoyJoy expert knowledge: tenant-confirmation gate, staging-vs-production diff before edits, semantic edit tools over full-document replacement, role-aware tool selection, and safe publishing workflows. Trigger it whenever a LoyJoy agent, process, module, or BPMN process is involved — including German phrasing like "Agent anpassen", "Modul hinzufügen", "Staging veröffentlichen".

## Installation

```bash
/plugin marketplace add loyjoy/loyjoy-skills
/plugin install loyjoy-headless@loyjoy-skills
```

## Requirements

1. A [LoyJoy](https://www.loyjoy.com) account with access to the **LoyJoy Manager MCP server**.
2. An Agent Skills–compatible AI assistant, e.g. [Claude Code](https://code.claude.com) or Claude.

The MCP server is preconfigured in this plugin at `https://app-cloud.loyjoy.com/mcp`.

## License

[Apache-2.0](../../LICENSE) © [LoyJoy GmbH](https://www.loyjoy.com)
