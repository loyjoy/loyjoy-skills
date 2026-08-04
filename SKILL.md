---
name: loyjoy-headless
description: Inspect, edit, compare, and publish LoyJoy agent configurations through the LoyJoy Manager MCP server. Use this skill whenever a LoyJoy agent, process, module, or BPMN process XML is involved in any way, including changing an instruction or prompt, adding or removing a module or subprocess, adjusting knowledge configuration, tools, widget or branding settings, locales, comparing staging against production, or publishing an agent. Trigger it on German phrasing too, such as "Agent anpassen", "Prozess ändern", "Modul hinzufügen", "Instruction umschreiben", "Staging veröffentlichen", "Template ansehen", or a bare process id or agent name plus a change request. Use it even when the user only wants to look at an agent, and even when the request sounds like a one-line tweak, because the tool choice and the tenant check matter more than the size of the change.
---

# Manage LoyJoy agents through MCP

Treat the staging BPMN XML as the complete agent configuration and the source of truth. Read it with targeted greps and change it with narrow, semantic tools. Full-document replacement is the exception, not the default.

Read [references/examples.md](references/examples.md) before your first write in a task. It walks through the common changes call by call, including which lookup precedes which write.


## Confirm the active tenant first

Every later step operates against whatever tenant the current login points at. A wrong or stale login means inspecting, editing, or publishing the wrong customer's configuration, so confirm the tenant before doing anything else. Run this gate once at the start of a task.

1. Call `tenant_meta` to retrieve the active tenant.
2. Show the user the tenant name (and any other identifying metadata the tool returns).
3. Ask the user to confirm that the login is valid and this is the intended tenant with a clickable button (Elicitation-Tool).
4. Proceed only after explicit confirmation. If the user does not confirm, stop and ask them to fix the login or tenant selection before continuing.
Do not skip this gate and do not treat an unrelated instruction as confirmation. Re-confirm if anything suggests the login or tenant changed mid-task.


## Choose the smallest tool

Pick the first tool in this list that can express the change:

1. `process_put_instruction` for the text of a custom AI agent instruction.
2. `process_put_i18n` for a single-locale text on a `loyjoy:i18n` element.
3. `process_put_list_attribute` for a JSON-array-valued attribute (add and remove individual items). Use for `loyjoy:knowledgeExcludedSources`, `loyjoy:aiBlockWords`, `loyjoy:locales`, `loyjoy:liveUserIds` and similar list attributes. Never reserialize the full array through `process_set_attribute` when a delta suffices.
4. `process_set_attribute` for a single scalar attribute value on any element identified by its `id`. Resolve the exact attribute name first — see "Resolve attribute names before writing them".
5. `process_add_subprocess`, `process_add_extension_element`, `process_remove_element`, and `process_move_element` for structural edits. Resolve the exact `subprocess_type` or `element_type` from the XSD (see "Change structure with add, remove, and move"), never guess it. The server generates fresh `id` and `loyjoy:id-src`, enforces parent-child compatibility, and cascades reference cleanup on removal (nulls dangling jump targets, drops orphan DMN entries, deletes unreferenced assets).
6. `process_put_xml` only when none of the above can express the change atomically (large multi-field refactors, migrations).


### Why the ordering is not a style preference

`process_put_xml` advertises "safety validation", and that is true but narrow: the server checks that the document you send is schema-valid and that the revision is current. It cannot check that the document is still *correct*. Everything below passes schema validation and breaks the agent anyway:

- A regenerated or dropped `loyjoy:id-src` breaks analytics and the staging-to-production lineage. Nothing reports it.
- An `id` that changed without its dependents leaves dangling `*BpmnProcessId` / `*BpmnSubProcessId` jump targets and orphaned i18n keys of the form `<slot>/<parent-uuid>`. Only some are model-checked, so the rest surface as a broken conversation in production.
- A removed element leaves behind the jump targets, DMN entries, and assets that `process_remove_element` would have cleaned up.
- A hand-written `*Aes` value destroys a secret irrecoverably.
- A full-document write clobbers any concurrent edit inside the same revision window, where a delta write would have merged.
The narrow tools cannot produce any of these outcomes. That is the entire difference, and it is why an eight-call narrow sequence beats a one-call replacement even though it looks more expensive.


### The full-XML pull

You will feel drawn to `process_put_xml` for a specific reason worth naming: once you have read the whole document, editing it in context feels concrete and verifiable, while narrow tools feel like operating blind on ids you have to look up. That intuition is backwards here. The narrow tools return the previous and new value on every call, so they are the path that gives you verification; the full-document write returns only a revision number and tells you nothing about what you actually changed. If you notice yourself reaching for the full XML because it feels easier to see, that is the moment to grep instead.


## Consult templates as reference

Templates are read-only scaffolds that show how a use case is expressed in BPMN XML (live chat, advent calendar, quiz, raffle, data collection, and so on). Consult them when the user asks for a new agent, a new module, or a pattern the current process does not yet contain. Skip them when the target process already contains the pattern being edited.

1. For a keyword-shaped lookup, prefer `templates_search(locale, pattern)`. The Java regex is matched against `title`, `description`, `header.title`, `tags`, `highlights`, FAQ questions and answers, and `content_markdown`; the response contains full matching template objects plus `total_matches`. Use it when the user says something like "Adventskalender-Template" or "raffle chatbot".
2. When you need the whole catalogue, call `templates_list` with the required `locale` (`de` or `en`). The response can be large; filter mentally by title and tags before reading further.
3. Call `template_get_xml` with the chosen `template_id` to retrieve the full BPMN XML.
4. Read the template XML to learn which subProcess `loyjoy:type` values, attributes, i18n keys, `loyjoy:dataCollectionQuestion` shapes, and jump-reference patterns implement the use case.
5. Use the template as a structural reference only. Never call `process_put_xml` with a template's XML: every copied element needs a fresh `id`, a fresh `loyjoy:id-src`, and every dependent i18n key of the form `<slot>/<parent-uuid>` and every UUID reference (`*BpmnProcessId`, `*BpmnSubProcessId`) must be regenerated to match the target process.
6. Never publish a template and never edit it through any `process_*` write tool; templates are not staging processes.


## Create a new agent

1. Call `process_create(name, default_locale, folder?)` to create an empty staging process. The server generates the process id and returns it. The new process has no welcome message, no AI agent, no default sub-processes — it is unseeded.
2. Fill in subprocesses with `process_add_subprocess` (starting from the returned `process_id` as the parent for top-level subprocesses) and nested extension elements with `process_add_extension_element`. Consult `templates_search` (or `templates_list` + `template_get_xml`) first if the user wants a use-case-shaped scaffold rather than a truly blank agent.
3. Configure attributes and texts with `process_set_attribute`, `process_put_list_attribute`, `process_put_i18n`, and `process_put_instruction`.
4. Fill the agent branding from the user's prompt whenever it is clear enough (for example brand name, tone, colors, greeting style, or similar brand cues). If the prompt does not contain enough information to choose sensible branding, ask the user for the missing branding details before configuring it.


## Inspect an agent

1. Call `processes_list` to resolve the requested agent to a process ID. Ask the user when multiple processes plausibly match.
2. `process_get_xml_grep` with a Java regex is the default read for everything: a specific i18n key, an attribute name, a sub-process id, a referenced UUID, or just orienting yourself in the process structure. Use `context_before` and `context_after` (up to 5 each) to see the surrounding element. Two or three greps almost always beat one full read, and they leave you with the element ids you need for the write anyway.
3. `process_get_xml` returns the full document and both `xml` and `revision`. Reach for it when you genuinely need the whole picture at once: an audit, a structural comparison, or a migration you are about to write through `process_put_xml`. Do not use it as a warm-up before an ordinary edit. Beyond the context cost, holding the full document makes local editing feel like the natural next step and quietly steers the whole task toward full-document replacement.
4. Inspect the existing XML for the relevant module before proposing a change.
5. Call `process_get_xml_schema` whenever the change is non-trivial — adding a module or sub-process, seeding a new `dataCollectionQuestion`, wiring a new `bpmnSubProcessCondition`, or touching any attribute you have not read before. The schema is the source of truth for element names, attribute names, cardinalities, and enum-typed attributes (`SubProcessTypeEnum`, `DataCollectionQuestionTypeEnum`, `InstructionType`, `MappingType`, `ToolTypeEnum`, etc.); never invent schema fields or guess enum values. Enum entries may carry `xs:documentation xml:lang="de"|"en"` annotations — use them to map user-facing names (e.g. the customer says "Fortfahren-Modul" → look for `xml:lang="de"` labels and pick the matching `xs:enumeration value`).
6. For targeted schema lookups (a single attribute name, one enum, one attribute group), prefer `process_get_xml_schema_grep` with a Java regex over downloading the ~3400-line full schema. Use `context_before` / `context_after` (up to 5 each) to see the surrounding `xs:enumeration`, `xs:attributeGroup`, or `xs:complexType` block.


## Resolve attribute names before writing them

`process_set_attribute`, `process_put_list_attribute`, and the `initial_attrs` map of `process_add_extension_element` all take the attribute name as a free-text string. A wrong name is either rejected or written as a second, ignored attribute that looks correct in a diff — so never guess a name, never reconstruct one from a similar attribute seen earlier, and never settle an uncertainty by picking the more plausible-looking of two candidates.

The moment you catch yourself weighing two spellings — `loyjoy:dtstart` versus `dtstart`, `loyjoy:aiBlockWords` versus `loyjoy:aiBlockwords` — treat that hesitation as the trigger to look the name up. A targeted grep costs a few hundred tokens; a wrong write costs a damaged staging process and a confused user.

Resolution order:

1. `process_get_xml_grep(process_id, pattern)` — if the element already carries the attribute in this process, the XML shows the exact name in use, prefix included. Cheapest and most reliable, and it confirms the element `id` at the same time.
2. `process_get_xml_schema_grep(pattern)` — the authoritative answer for attributes the process does not carry yet. Grep for the bare name, case-insensitively, with context: `(?i)dtstart` plus `context_before: 3` returns the `xs:attribute` line together with the enclosing `xs:attributeGroup`, which also reveals which element the attribute belongs to.
3. `process_get_xml_schema()` — the full ~3400-line schema, only when targeted greps come back empty and you genuinely need to browse. It burns a lot of context, so treat it as the last resort and mention to the user that you fell back to it.
**Prefix rule.** The XSD never prints the `loyjoy:` prefix; it encodes it in `form`. `form="qualified"` means the attribute lives in the LoyJoy extension namespace and must be passed prefixed (`loyjoy:dtstart`). BPMN core attributes such as `name` are unqualified and are passed bare.
Example: `(?i)dtstart` returns

```xml
<xs:attributeGroup name="VEventAttributesGroup">
  ...
  <xs:attribute name="dtstart" type="xs:dateTime" form="qualified"/>
```

so the correct call is `process_set_attribute(name="loyjoy:dtstart", ...)` on a `vevent` element.

Read two more things out of the same match while you are there: the declared type (`process_set_attribute` takes a string, so format the value to match `xs:dateTime`, `xs:int`, `xs:boolean`), and whether the attribute is list-valued — if it is, use `process_put_list_attribute` instead.

## Edit an agent with narrow tools

1. Locate the target element and its `id` with `process_get_xml_grep` or a focused read.
2. Call the narrow tool that matches the change (`process_put_instruction`, `process_put_i18n`, `process_put_list_attribute`, `process_set_attribute`).
3. Report the returned `previous_*` and `new_*` values so the user can verify the change. This return payload is the main reason narrow tools are easier to work with than a full write: you get a precise before/after per call instead of a revision number.
4. After a sequence of several writes, call `process_diff` to show the accumulated change between the published and staging revision. It defaults to comparing the latest two revisions and takes explicit revisions as optional arguments.
5. Never invoke `process_publish` unless the user explicitly asked for it.
## Change structure with add, remove, and move

Structural edits use dedicated add tools for BPMN subprocesses and extension elements, plus generic remove and move tools.

Before assembling any new module, sub-process, `dataCollectionQuestion`, `bpmnSubProcessCondition`, `mapping`, `widget`, or other extension element, always call `process_get_xml_schema` (or `process_get_xml_schema_grep` for a targeted lookup) and read the relevant `xs:attributeGroup` and `xs:complexType` for the element you intend to create. Every attribute you set through `initial_attrs`, `process_set_attribute`, or `process_put_list_attribute` must appear in the schema; if it does not, do not send it. Consult a matching template with `templates_search` (or `templates_list` + `template_get_xml`) in addition to the schema when the user wants a use-case-shaped scaffold — the schema tells you what is possible, the template shows how a working example uses it.

1. `process_add_subprocess(process_id, parent_id, subprocess_type, position?)` — creates a BPMN subprocess flow element under a process or subprocess. `subprocess_type` is required and must be an exact `SubProcessTypeEnum` value. Resolve it with `process_get_xml_schema_grep(pattern="SubProcessTypeEnum", context_after=5)` and continue through the enumeration; never guess it from a label or memory. Use the process ID as `parent_id` for a top-level subprocess.
2. `process_add_extension_element(process_id, parent_id, element_type, position?, initial_attrs?)` — creates a LoyJoy extension element under the given parent. `element_type` is the **camelCase** local name declared in the XSD (e.g. `dataCollectionQuestion`, `bpmnSubProcessCondition`, `widgetGroup`, `vEvent`). It cannot create subprocesses. Resolve valid keys from `ExtensionElementsType`: every `loyjoy:<name>` ref inside its `xs:choice` is a valid `element_type`, stripped of the `loyjoy:` prefix. `initial_attrs` is a string map; the server rejects protected keys (`id`, `loyjoy:id-src`, audit metadata, `*Aes`, process identity). After the add, use `process_put_i18n`, `process_put_instruction`, or `process_set_attribute` to fill in text and remaining configuration.
3. `process_remove_element(process_id, element_id)` — deletes an element. The server cascades reference cleanup: nulls jump targets on Process, SubProcess, ListElement, ScannerCategory and SnapshotCategory that pointed at a removed SubProcess; drops orphan `DmnEntry` rows; deletes unreferenced `Asset` files. It refuses to remove the `Process`, `Definitions`, or `ExtensionElements` containers.
4. `process_move_element(process_id, element_id, new_parent_id?, new_position?)` — reorder within the current parent (omit `new_parent_id`) or re-parent (provide `new_parent_id`). The element keeps its `id`, so cross-references stay valid. Refuses to move a container element and refuses to move an element into its own subtree.


## Edit an agent with raw XML

Before following these steps, answer one question: which specific narrow tool fails to express this change, and why? A change that touches one element always has a narrow tool. If the honest answer is that a narrow call was rejected, fix the call rather than routing around it; the rejection is the server protecting the process. Valid reasons to be here are a refactor across many elements, a migration, or a documented gap in the tool surface. If you cannot name the reason, go back.

1. Modify the XML locally without changing the original revision.
2. Make the smallest change that satisfies the request.
3. Preserve unrelated elements, IDs, namespaces, process metadata, and unknown configuration.
4. Keep the process ID unchanged and the process version set to `staging`.
5. Never regenerate `id` or `loyjoy:id-src` values on existing elements. `id-src` is opaque lineage; changing it breaks analytics and the staging-to-production link.
6. When an element's `id` must change, update every dependent reference: `loyjoy:i18n` keys of the form `<slot>/<parent-uuid>`, and every attribute whose name ends in `BpmnProcessId`, `BpmnSubProcessId`, or is otherwise a UUID reference (for example `loyjoy:openingHoursOpenJumpBpmnSubProcessId`, `loyjoy:liveExitJumpAutoBpmnSubProcessId`, `loyjoy:jumpDecision1..7BpmnSubProcessId`). Only some are model-checked; dangling references may not surface until runtime.
7. Never alter an attribute whose name ends in `Aes`. Use a dedicated non-XML tool for secret changes when one exists; otherwise explain that the secret cannot be changed through raw XML editing.
8. Summarize the intended changes before saving when they are broad, ambiguous, or potentially disruptive.
9. Call `process_put_xml` with the original revision.
10. Retain the new revision returned by `process_put_xml`.


## Handle revision conflicts

If any tool reports that staging changed:

1. Do not retry with the old XML.
2. Call `process_get_xml` again.
3. Reapply only the requested changes to the latest XML.
Never resolve a conflict by replacing the latest document wholesale.


## Publish an agent

Publishing changes production behavior. Call `process_publish` only when the user explicitly asks to publish or explicitly approves the reviewed staged changes.

Before publishing:

1. Ensure the revision is the latest revision returned after saving.
2. Give a concise summary of what will enter production.
3. Use a meaningful publication comment describing the change.
Do not interpret a request to edit, update, configure, or fix an agent as permission to publish it.


## Read-only requests

For inspection, explanation, review, or comparison requests, do not call `process_create`, `process_put_xml`, `process_put_instruction`, `process_put_i18n`, `process_put_list_attribute`, `process_set_attribute`, `process_add_subprocess`, `process_add_extension_element`, `process_remove_element`, `process_move_element`, or `process_publish`. Use `processes_list`, `search`, `process_get_xml_grep`, `process_get_xml`, `process_diff`, `process_get_xml_schema_grep`, `process_get_xml_schema`, `templates_search`, `templates_list`, `template_get_xml`, `views_list`, `view_get`, `view_get_xml`, and `analytics_process_get` as needed. `process_diff` is the right tool for "what changed", "what is not live yet", and "compare staging to production" questions.


## Report the outcome

State:

- Which process and modules changed, and which tool performed the change.
- Whether changes are only staged or have been published.
- The resulting staging revision after a write, or the previous and new value returned by a narrow tool.
If you have not read [references/examples.md](references/examples.md) yet in this task, read it before the next write. It shows the call sequence for each common change.
