# LoyJoy Skills — Agent Skills for the LoyJoy Platform

**LoyJoy Skills** is the official collection of [Agent Skills](https://agentskills.io) and Claude Code plugins for the [LoyJoy Platform](https://www.loyjoy.com), the European conversational AI platform for customer engagement via chat and phone. With these skills, AI agents like Claude can create, edit, analyze, and publish LoyJoy AI agents on your behalf — no platform expertise required.

> A skill is a portable folder of expert knowledge that an AI agent loads on demand. These skills package years of LoyJoy know-how — agent configuration, prompt engineering for chat and voice, safe editing workflows — so your AI assistant can operate the LoyJoy Platform like a LoyJoy expert.

## What you can do with LoyJoy Skills

1. **Manage LoyJoy AI agents in natural language** — inspect, edit, compare, and publish agent configurations without touching the visual editor.
2. **Build and debug phone agents (voice bots)** — create telephony-ready AI agents, write and iterate custom voice prompts, and translate customer feedback into concrete prompt changes.
3. **Work safely** — the skills enforce LoyJoy best practices: tenant confirmation before every change, staging-vs-production diffs before edits, and minimal, semantic edits instead of risky full-document rewrites.

## Skills in this repository

| Plugin | What it does |
|---|---|
| [`loyjoy-headless`](plugins/loyjoy-headless) | Inspect, edit, compare, and publish LoyJoy agent configurations through the LoyJoy Manager MCP server. Covers instructions and prompts, modules and subprocesses, knowledge configuration, tools, branding, locales, and publishing workflows. |
| [`phone-agent-builder`](plugins/phone-agent-builder) | Create, configure, iterate, and debug LoyJoy phone agents and their custom voice prompts. Covers the standard-plus-custom prompt architecture, voice-specific patterns (spoken numbers, digit confirmation, transfer with consent), and debugging from real test calls. |

More skills are on the way, including analytics reporting, presentation and infographic generation from LoyJoy data, and knowledge management.

## Installation

### Claude Code

```bash
/plugin marketplace add loyjoy/loyjoy-skills
/plugin install loyjoy-headless@loyjoy-skills
/plugin install phone-agent-builder@loyjoy-skills
```

### Other agents

Any [Agent Skills](https://agentskills.io)–compatible agent (Claude, Cowork, and a growing ecosystem of tools) can use these skills. Copy the skill folders from `plugins/*/skills/` into your agent's skills directory.

## Requirements

1. A [LoyJoy](https://www.loyjoy.com) account with access to the **LoyJoy Manager MCP server** (the skills read and write agent configurations through MCP).
2. An Agent Skills–compatible AI agent, e.g. [Claude Code](https://code.claude.com) or Claude.

Without MCP access the skills still work in advisory mode: they produce copy-paste-ready prompts and setup instructions.

## Frequently asked questions

### What is LoyJoy?

[LoyJoy](https://www.loyjoy.com) is a conversational AI platform from Münster, Germany. Brands and mid-sized companies use it to build GDPR-compliant AI agents for the customer interface — web chat, in-app chat, and phone — for use cases like product consultation, customer service, lead generation, and marketing campaigns.

### What are Agent Skills?

[Agent Skills](https://agentskills.io) are an open standard, originally developed by Anthropic, for packaging procedural knowledge into folders that AI agents load on demand. Each skill is a `SKILL.md` file with instructions plus optional reference material.

### Can I manage my LoyJoy AI agents with Claude?

Yes. Install the `loyjoy-headless` plugin, connect the LoyJoy Manager MCP server, and ask Claude in plain language — for example *"Add a welcome question to my agent and publish it"* or *"Compare staging against production"*. The skill handles tenant checks, safe editing, and publishing.

### Do I need to be a developer?

No. The skills are designed so that marketing, sales, and customer-care teams can operate LoyJoy AI agents through an AI assistant. The expert knowledge lives in the skills.

## Contributing and support

1. Issues and suggestions: [GitHub Issues](https://github.com/loyjoy/loyjoy-skills/issues)
2. LoyJoy Platform: [loyjoy.com](https://www.loyjoy.com)
3. Contact: [loyjoy.com/contact](https://www.loyjoy.com/contact)

## License

[Apache-2.0](LICENSE) © [LoyJoy GmbH](https://www.loyjoy.com)
