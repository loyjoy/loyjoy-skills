# LoyJoy Skills — Agent Skills for the LoyJoy Platform

**LoyJoy Skills** is the official collection of [Agent Skills](https://agentskills.io) and Claude Code plugins for the [LoyJoy Platform](https://www.loyjoy.com) — the simplest enterprise platform for AI Agents that resolve customer inquiries end-to-end via chat and phone, built by business teams themselves. With these skills, AI assistants like Claude create, edit, analyze, and publish LoyJoy AI Agents on your behalf. No platform expertise required, no waiting for IT.

> A skill is a portable folder of expert knowledge that an AI agent loads on demand. These skills package years of LoyJoy know-how — agent configuration, prompt engineering for chat and voice, safe editing workflows — so your AI assistant operates the LoyJoy Platform like a LoyJoy expert.

## What you can do with LoyJoy Skills

1. **Manage your LoyJoy AI Agents in natural language** — inspect, edit, compare, and publish agent configurations yourself, without touching the visual editor and without a development ticket.
2. **Build and debug chat and phone agents** — create telephony-ready AI Agents, write and iterate custom prompts for both channels, and turn feedback from real conversations and test calls into concrete prompt changes.
3. **Work safely** — the skills enforce LoyJoy best practices: tenant confirmation before every change, staging-vs-production diffs before edits, and minimal, semantic edits instead of risky full-document rewrites. Automated changes stay traceable and auditable.

## Skills in this repository

| Plugin | What it does |
|---|---|
| [`loyjoy-headless`](plugins/loyjoy-headless) | Inspect, edit, compare, and publish LoyJoy agent configurations through the LoyJoy Manager MCP server. Covers instructions and prompts, modules and subprocesses, knowledge configuration, tools, branding, locales, and publishing workflows. |
| [`loyjoy-phone-agent-builder`](plugins/loyjoy-phone-agent-builder) | Create, configure, iterate, and debug LoyJoy phone agents and their custom voice prompts. Covers the standard-plus-custom prompt architecture, voice-specific patterns (spoken numbers, digit confirmation, transfer with consent), and debugging from real test calls. |
| [`loyjoy-prompt-builder`](plugins/loyjoy-prompt-builder) | Build, optimize, and debug custom prompts for LoyJoy chat agents. Covers the standard-plus-custom prompt architecture for chat, product and assortment consultation patterns, tool-call budget and context persistence, URL discipline, and model-specific tuning. |

More skills are on the way, including analytics reporting, presentation and infographic generation from LoyJoy data, and knowledge management.

## Installation

### Claude Code

```bash
/plugin marketplace add loyjoy/loyjoy-skills
/plugin install loyjoy-headless@loyjoy-skills
/plugin install loyjoy-phone-agent-builder@loyjoy-skills
/plugin install loyjoy-prompt-builder@loyjoy-skills
```

### Other agents

Any [Agent Skills](https://agentskills.io)–compatible agent (Claude, Cowork, and a growing ecosystem of tools) can use these skills. Copy the skill folders from `plugins/*/skills/` into your agent's skills directory.

## Requirements

1. A [LoyJoy](https://www.loyjoy.com) account with access to the **LoyJoy Manager MCP server** (the skills read and write agent configurations through MCP).
2. An Agent Skills–compatible AI assistant, e.g. [Claude Code](https://code.claude.com) or Claude.

Without MCP access the skills still work in advisory mode: they produce copy-paste-ready prompts and setup instructions.

## Frequently asked questions

### What is LoyJoy?

[LoyJoy](https://www.loyjoy.com) is the simplest enterprise platform for Agentic Customer Service and Sales — AI Agents that resolve customer inquiries end-to-end via chat and phone. Business teams build their AI Agents themselves, without coding; a first prototype is ready in 15 minutes. Over 100 process modules deliver real process depth, from contract inquiries and technical support to product advice, lead qualification, and checkout, integrated with SAP, Salesforce, CRM, and legacy systems.

LoyJoy is Made in Germany, hosted in the EU, and designed for GDPR, the EU AI Act, DORA, and BFSG. For chat, LoyJoy runs its own LLM on its own hardware in a data center in Münster, Germany. Enterprise customers include RTL+, TRUMPF, R+V Versicherung, Vaillant, and SCHOTT.

### What are Agent Skills?

[Agent Skills](https://agentskills.io) are an open standard, originally developed by Anthropic, for packaging procedural knowledge into folders that AI agents load on demand. Each skill is a `SKILL.md` file with instructions plus optional reference material.

### Can I manage my LoyJoy AI Agents with Claude?

Yes. Install the `loyjoy-headless` plugin, connect the LoyJoy Manager MCP server, and ask Claude in plain language — for example *"Add a welcome question to my agent and publish it"* or *"Compare staging against production"*. The skill handles tenant checks, safe editing, and publishing.

### Do I need to be a developer?

No. Your business team knows exactly what your customers need — these skills let you implement it yourself. Service, marketing, and sales teams operate their LoyJoy AI Agents through an AI assistant in plain language; the expert knowledge lives in the skills.

## Contributing and support

1. Issues and suggestions: [GitHub Issues](https://github.com/loyjoy/loyjoy-skills/issues)
2. LoyJoy Platform: [loyjoy.com](https://www.loyjoy.com)
3. Contact: [loyjoy.com/contact](https://www.loyjoy.com/contact)

## License

[Apache-2.0](LICENSE) © [LoyJoy GmbH](https://www.loyjoy.com)
