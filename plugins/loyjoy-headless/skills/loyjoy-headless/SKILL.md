---
name: loyjoy-headless
description: Inspect, edit, compare, and publish LoyJoy agent configurations through the LoyJoy Manager MCP server. Use this skill whenever a LoyJoy agent, process, module, or BPMN process XML is involved in any way, including changing an instruction or prompt, adding or removing a module or subprocess, adjusting knowledge configuration, tools, widget or branding settings, locales, comparing staging against production, or publishing an agent. Trigger it on German phrasing too, such as "Agent anpassen", "Prozess ändern", "Modul hinzufügen", "Instruction umschreiben", "Staging veröffentlichen", "Template ansehen", or a bare process id or agent name plus a change request. Use it even when the user only wants to look at an agent, and even when the request sounds like a one-line tweak, because the tool choice and the tenant check matter more than the size of the change.
---

# Manage LoyJoy agents through MCP

Treat the staging BPMN XML as the complete agent configuration and the source of truth. Read it with targeted greps and change it with narrow, semantic tools. Full-document replacement is the exception, not the default.

Read [references/examples.md](references/examples.md) before your first write in a task. It walks through the common changes call by call, including which lookup precedes which write.


## How the MCP server works

The LoyJoy Manager MCP server (`/mcp`) derives its tools from the REST API of the manager. Every tool is one REST operation, and its name is the operation id in snake_case (`bpmn_process_get`, `bpmn_process_element_attributes_patch`, ...). Four rules follow from that:

1. **`tenant_id` is required on every tool except `list_tenants`.** The server has no "active tenant"; one login can reach several tenants. Pass the confirmed `tenant_id` on every call (see the next section).
2. **Path and query parameters are top-level arguments, a JSON request body goes into the argument `body`.** Example: `bpmn_process_element_attributes_patch(tenant_id, process_id, element_id, body={"name":"loyjoy:widgetChatWidth","value":"480"})`.
3. **Every successful response is `{ "data": ..., "tenant_id": ... }`.** Read the payload from `data`.
4. **A failed call reports `HTTP <status> for <method> <path> in tenant <id>: <body>`.** Validation errors are problem+json and end with `issues=[...]`; every issue carries `element_id`, `attribute`, `severity`, `message`, and `hint`. Report them to the user in plain words and fix the cause; do not route around a rejection.

The tool list is not filtered by role. Access is enforced by each operation: an `HTTP 403` means the login lacks the role for that operation (`OWNER`, `EDITOR`, `PROCESSES_EDITOR`, `PROCESSES_VIEWER`, `ANALYTICS_VIEWER`, `REVISION`, ...). Do not work around it with a broader tool; report it and ask the user to check the role of the login, so they can decide whether to grant the role or run the task with a different account.


## Confirm the tenant first

Every later call operates against the tenant you pass as `tenant_id`. A wrong tenant means inspecting, editing, or publishing the wrong customer's configuration, so confirm the tenant before doing anything else. Run this gate once at the start of a task.

1. Call `list_tenants`. It returns `tenant_id`, `name`, and a `description` with the user's roles for every reachable tenant.
2. If exactly one tenant is returned, show its name and roles. If several are returned, show them and let the user choose. Use a clickable button for the confirmation or the choice.
3. Proceed only after explicit confirmation. If the user does not confirm, stop and ask them to fix the login before continuing.
4. Keep the confirmed `tenant_id` for the whole task and pass it on every call. Never switch to another `tenant_id` mid-task without a new confirmation.

Do not skip this gate and do not treat an unrelated instruction as confirmation.


## Guard rails the server enforces

Writes on a staging process go through server-side guards. Use them deliberately:

1. **`dry_run=true`** on the process writes (`bpmn_process_elements_post`, `bpmn_process_element_attributes_patch`, `bpmn_process_element_delete`, `bpmn_process_element_move_post`, `bpmn_process_xml_put`) stores nothing and returns `diff` (staging against the result), `roundtrip` (the XML round trip of the result, with `is_identical`), `issues`, and `is_valid` (model check of the result). Preview every structural write and every XML replacement this way first, and read `diff` line by line: it is the only place that shows exactly which attribute names and values the write will store.
2. **`expected_revision`** on the same writes makes the server refuse the write with `HTTP 409` if staging changed since you read it. Take the value from the `revision` of `bpmn_process_element_get` or of the previous write's response, and pass it on every real (non-dry-run) write. On a 409, re-read and re-plan; never retry blindly.
3. **Protected attributes** are rejected: `id`, `loyjoy:id-src`, `loyjoy:createdAt`, `loyjoy:updatedAt`, `loyjoy:updatedBy`, `loyjoy:version`, `loyjoy:versionComment`, `loyjoy:versionCreatedBy`, `loyjoy:versionIsProd`, `loyjoy:locked`, and every attribute ending in `Aes`. `bpmn_process_xml_put` rejects changes to them as well.
4. **Locked processes** ("centrally managed by LoyJoy Customer Success Management") cannot be written. They can still be read.
5. **Publishing** is refused with `HTTP 409` while the model check reports issues of severity CRITICAL or higher. There is no override through MCP: fix the issues, or tell the user to publish from the Manager UI.


## Check for unpublished staged changes before editing

Before the first write in any edit task, confirm that staging is in sync with production. Any pre-existing diff will silently ride along with your changes when the process is next published, so surface it and let the user decide.

1. Call `bpmn_processes_versions_diff_get(tenant_id, bpmn_process_id)` without `left_version` or `right_version`. The defaults (`left_version=prod`, `right_version=staging`) compare production against staging and reveal any changes not yet published.
2. If `data.is_identical` is true, continue with the edit task.
3. If the diff shows changes:
   1. Summarize the pending changes to the user.
   2. Ask with a clickable button (yes/no) whether to publish these pending changes first, before your own edits begin.
   3. If the user confirms, call `bpmn_process_publish_post(tenant_id, body={"bpmn_process_id": ..., "comment": "..."})` with a meaningful comment describing the pending changes, then continue with the edit task.
   4. If the user declines, continue with the edit task without publishing.

Skip this gate on read-only requests (inspection, comparison, explanation) — those don't add to what would ship on the next publish.


## Choose the smallest tool

Pick the first tool in this list that can express the change:

1. `bpmn_process_element_attributes_patch` with `body={"name":"text","value":"..."}` for the text of an existing AI agent instruction. Create a new instruction with `bpmn_process_elements_post(body={"parent_id":..., "element_type":"instruction", "initial_attrs":{"type":"custom","text":"..."}})` after resolving the allowed instruction attributes and enum values from the schema.
2. `i18n_by_key_put(tenant_id, bpmn_process_id, key, locale, body={"value":{"<locale>":"..."}})` for a single-locale text of a `loyjoy:i18n` element, addressed by its i18n `key`. Only the locale named in `locale` is written, taken from `value`; the other locales stay untouched. The same call also adds a new localized text: if no i18n element with this key exists yet, the server creates it under the element whose id is the `<parent-id>` part of the key `<slot>/<parent-id>`. Call it once per configured locale. Do not try to create i18n elements with `bpmn_process_elements_post`; the server refuses `element_type="i18n"`. Empty and whitespace-only texts are allowed; they do not remove the i18n element or its other locales.
3. `bpmn_process_element_attributes_patch` with `body={"name":..., "add":[...], "remove":[...]}` for a JSON-array-valued attribute. Use for `loyjoy:knowledgeExcludedSources`, `loyjoy:aiBlockWords`, `loyjoy:locales`, `loyjoy:liveUserIds` and similar list attributes. Never reserialize the full array through `value` when a delta suffices.
4. `bpmn_process_element_attributes_patch` with `body={"name":..., "value":"..."}` for a single scalar attribute on any element identified by its `id`. Resolve the exact attribute name first — see "Resolve attribute names before writing them". A blank `value` removes the attribute.
5. `flow_element_add_post`, `bpmn_process_elements_post`, `bpmn_process_element_delete`, and `bpmn_process_element_move_post` for structural edits. Resolve the exact subprocess `type` or `element_type` from the XSD (see "Change structure with add, remove, and move"), never guess it. The server generates fresh `id`s, enforces parent-child compatibility, and cascades reference cleanup on removal (nulls dangling jump targets, drops orphan DMN entries, deletes unreferenced assets).
6. `bpmn_process_xml_put` only when none of the above can express the change atomically (large multi-field refactors, migrations).


### Why the ordering is not a style preference

`bpmn_process_xml_put` validates the document against the XSD and rejects changes to protected attributes. It cannot check that the document is still *correct*. Everything below passes those checks and breaks the agent anyway:

- An `id` that changed without its dependents leaves dangling `*BpmnProcessId` / `*BpmnSubProcessId` jump targets and orphaned i18n keys of the form `<slot>/<parent-uuid>`. Only some are model-checked, so the rest surface as a broken conversation in production.
- A removed element leaves behind the jump targets, DMN entries, and assets that `bpmn_process_element_delete` would have cleaned up.
- A full-document write can clobber concurrent edits, where a narrow delta write would usually preserve unrelated changes.

The narrow tools cannot produce any of these outcomes. That is the entire difference, and it is why an eight-call narrow sequence beats a one-call replacement even though it looks more expensive.


### The full-XML pull

You will feel drawn to `bpmn_process_xml_put` for a specific reason worth naming: once you have read the whole document, editing it in context feels concrete and verifiable, while narrow tools feel like operating blind on ids you have to look up. That intuition is backwards here. Attribute and list writes return `previous_value` and `new_value`, structural writes return the affected element id, and `bpmn_process_element_get` shows any element with its children on demand. A full-document write only confirms that the XML was saved. If you notice yourself reaching for the full XML because it feels easier to see, that is the moment to grep or read the element instead.


## Consult templates as reference

Templates are read-only scaffolds that show how a use case is expressed in BPMN XML (live chat, advent calendar, quiz, raffle, data collection, and so on). Consult them when the user asks for a new agent, a new module, or a pattern the current process does not yet contain. Skip them when the target process already contains the pattern being edited.

1. For a keyword-shaped lookup, call `templates_get(tenant_id, locale, q)` with a Java regex in `q`. It is matched against titles, descriptions, tags, highlights, FAQ questions and answers, and template content; the response contains the full matching template objects plus `total_matches`. Use it when the user says something like "Adventskalender-Template" or "raffle chatbot".
2. `templates_xml_grep_get(tenant_id, locale, grep, context?)` is the cross-template XML grep. It loads the BPMN XML of every template for the locale and greps each with the Java regex; every match is annotated with `template_id` and `template_title`. Reach for it in one specific situation: **you are about to add a subprocess, an extension element, an attribute, or another XML construct to a process and you do not know what a well-formed working example of that construct looks like.** The schema tells you which attributes are allowed; this tool shows how a real template wires them up — which attributes tend to be set together, which sibling elements typically appear, how `loyjoy:i18n` keys are named, which jump-reference attributes point where. Do not use it when a description keyword would do (use `templates_get` with `q`), when the target template is already known (use `template_xml_get` with `grep` on that id), when the schema alone answers the question, or as an exploratory browse of the catalogue (use `templates_get` without `q`). Because it loads every template's XML on every call, treat it as expensive: one gate before you write, not a search habit. Use a specific regex naming the element or attribute you are about to write (`loyjoy:dataCollectionQuestion[^>]*type="email"`), keep `context` at 3–5, and stop after a single well-scoped call. Pick one template as your reference and pattern the new elements after it rather than reading every match.
3. When you need the whole catalogue, call `templates_get(tenant_id, locale)` without `q` (`locale` is `de` or `en`). The response can be large; filter by title and tags before reading further.
4. Call `template_xml_get(tenant_id, template_id)` for the full BPMN XML of the chosen template, or add `grep` and `context` for a targeted read.
5. Read the template XML to learn which subProcess `loyjoy:type` values, attributes, i18n keys, `loyjoy:dataCollectionQuestion` shapes, and jump-reference patterns implement the use case.
6. Use the template as a structural reference only. Never call `bpmn_process_xml_put` with a template's XML: every copied element needs a fresh `id`, and every dependent i18n key of the form `<slot>/<parent-uuid>` and every UUID reference (`*BpmnProcessId`, `*BpmnSubProcessId`) must be regenerated to match the target process.
7. Never publish a template and never edit it through any process write tool; templates are not staging processes.


## Create a new agent

1. Call `bpmn_process_create_post(tenant_id, body={"name":..., "default_locale":..., "folder":...})` to create an empty staging process. The server generates the process id and returns the process in `data` (`data.id`). The new process has no welcome message, no AI agent, no default subprocesses — it is unseeded.
2. Fill in subprocesses with `flow_element_add_post` (with the process id as `parent_id` for top-level subprocesses) and nested extension elements with `bpmn_process_elements_post`. Consult `templates_get` first if the user wants a use-case-shaped scaffold rather than a truly blank agent.
3. Configure scalar and list attributes with `bpmn_process_element_attributes_patch`. Create instructions with `bpmn_process_elements_post(body={"parent_id":..., "element_type":"instruction", "initial_attrs":{"type":"custom","text":"..."}})`. Read the process's configured `loyjoy:locales` before creating text. Create each required localized text with `i18n_by_key_put` and its schema- and template-derived `key` `<slot>/<parent-id>`, once per configured locale.
4. Fill the agent branding from the user's prompt whenever it is clear enough (for example brand name, tone, colors, greeting style, or similar brand cues). If the prompt does not contain enough information to choose sensible branding, ask the user for the missing branding details before configuring it.


## Inspect an agent

1. Call `bpmn_processes_get(tenant_id)` to resolve the requested agent to a process id. Ask the user when multiple processes plausibly match. `search_get(tenant_id, q)` finds processes, home views, catalogs, articles, and flow elements by text when the name is vague.
2. `bpmn_process_xml_get(tenant_id, id, grep, context?)` with a Java regex is the default read for everything: a specific i18n key, an attribute name, a subprocess id, a referenced UUID, or just orienting yourself in the process structure. It returns `matches` (`line_number`, `line`, `context_before`, `context_after`), `total_matching_lines`, and `truncated`. Use `context` (up to 5) to see the surrounding element. Two or three greps almost always beat one full read, and they leave you with the element ids you need for the write anyway.
3. `bpmn_process_element_get(tenant_id, process_id, element_id, depth?)` returns one element with its `tag`, `attributes`, `text`, and children up to `depth` levels (default 1, `0` for the element only), plus the `revision` for `expected_revision`. Encrypted `*Aes` values are masked. Use it once you know an element id and need its exact attributes or children; add `format=xml` for the XML snippet or `version=prod` to read production.
4. `bpmn_process_xml_get(tenant_id, id)` without `grep` returns the full staging XML. Reach for it when you genuinely need the whole picture at once: an audit, a structural comparison, or a migration you are about to write through `bpmn_process_xml_put`. Do not use it as a warm-up before an ordinary edit. Beyond the context cost, holding the full document makes local editing feel like the natural next step and quietly steers the whole task toward full-document replacement.
5. Inspect the existing XML for the relevant module before proposing a change.
6. Call `bpmn_process_xml_schema_get(tenant_id, grep, context?)` whenever the change is non-trivial — adding a module or subprocess, seeding a new `dataCollectionQuestion`, wiring a new `bpmnSubProcessCondition`, or touching any attribute you have not read before. The schema is the source of truth for element names, attribute names, cardinalities, and enum-typed attributes (`SubProcessTypeEnum`, `DataCollectionQuestionTypeEnum`, `InstructionType`, `MappingType`, `ToolTypeEnum`, etc.); never invent schema fields or guess enum values. Enum entries may carry `xs:documentation xml:lang="de"|"en"` annotations — use them to map user-facing names (e.g. the customer says "Fortfahren-Modul" → look for `xml:lang="de"` labels and pick the matching `xs:enumeration value`). Without `grep` it returns the full ~3400-line schema; prefer a targeted `grep`.
7. Home views: `home_views_get`, `home_view_get`, and `home_view_xml_get(tenant_id, id, grep?, context?)`. Analytics: `bpmn_process_analysis_get(tenant_id, id, recursive=true, start-date?, end-date?)` for the process and all its subprocesses.


## Resolve attribute names before writing them

`bpmn_process_element_attributes_patch` and the `initial_attrs` map of `bpmn_process_elements_post` take the attribute name as a free-text string. A wrong name is either rejected or written as a second, ignored attribute that looks correct in a diff — so never guess a name, never reconstruct one from a similar attribute seen earlier, and never settle an uncertainty by picking the more plausible-looking of two candidates.

The moment you catch yourself weighing two spellings — `loyjoy:dtstart` versus `dtstart`, `loyjoy:aiBlockWords` versus `loyjoy:aiBlockwords` — treat that hesitation as the trigger to look the name up. A targeted grep costs a few hundred tokens; a wrong write costs a damaged staging process and a confused user.

Resolution order:

1. `bpmn_process_element_get(tenant_id, process_id, element_id, depth=0)` or `bpmn_process_xml_get(tenant_id, id, grep)` — if the element already carries the attribute in this process, it shows the exact name in use, prefix included. Cheapest and most reliable, and it confirms the element `id` at the same time.
2. `bpmn_process_xml_schema_get(tenant_id, grep, context)` — the authoritative answer for attributes the process does not carry yet. Grep for the bare name, case-insensitively, with context: `grep="(?i)dtstart"` plus `context=3` returns the `xs:attribute` line together with the enclosing `xs:attributeGroup`, which also reveals which element the attribute belongs to.
3. `bpmn_process_xml_schema_get(tenant_id)` without `grep` — the full schema, only when targeted greps come back empty and you genuinely need to browse. It burns a lot of context, so treat it as the last resort and mention to the user that you fell back to it.

**Prefix rule.** The XSD never prints the `loyjoy:` prefix; it encodes it in `form`. `form="qualified"` means the attribute lives in the LoyJoy extension namespace and must be passed prefixed (`loyjoy:dtstart`). BPMN core attributes such as `name` are unqualified and are passed bare.

Example: `grep="(?i)dtstart"` returns

```xml
<xs:attributeGroup name="VEventAttributesGroup">
  ...
  <xs:attribute name="dtstart" type="xs:dateTime" form="qualified"/>
```

so the correct call is `bpmn_process_element_attributes_patch(..., body={"name":"loyjoy:dtstart","value":"..."})` on a `vEvent` element.

Read two more things out of the same match while you are there: the declared type (the value is a string, so format it to match `xs:dateTime`, `xs:int`, `xs:boolean`), and whether the attribute is list-valued — if it is, use `add`/`remove` instead of `value`.


## Edit an agent with narrow tools

1. Locate the target element and its `id` with `bpmn_process_xml_get(grep)`, then read it with `bpmn_process_element_get` to get its current attributes and the `revision`.
2. Call the narrow tool that matches the change (`bpmn_process_element_attributes_patch` for an instruction `text`, another scalar, or a list delta; `i18n_by_key_put` for a localized text). Use `bpmn_process_elements_post` when the requested instruction does not exist yet; `i18n_by_key_put` creates a missing i18n element itself. Pass `expected_revision` on element writes.
3. Report the returned `previous_value` and `new_value` from `data.result` for attribute and list writes. `previous_value` is omitted when the attribute had no value before. For a newly added element, report its returned `element_id` and the verified initial attributes.
4. Verify the write as described in "Verify every write" before the next write, so a wrong attribute name is caught while you still remember what you sent.
5. After all related text writes are complete, call `issues_summary_by_bpmn_process_get(tenant_id, id)`. Inspect `LOCALE_NOT_MAINTAINED` issues for affected i18n elements and resolve language gaps introduced by the task. Do not silently invent translations for pre-existing findings; report those separately to the user. Do not treat `is_valid=true` as a runtime or content-quality test; non-blocking locale issues may still be present in `issues`.
6. Call `bpmn_processes_versions_diff_get(tenant_id, bpmn_process_id)` again with default versions. Summarize the resulting diff to the user so they can see exactly what will enter production if published — this is the final review artefact and the natural bookend to the pre-edit diff check.
7. Never invoke `bpmn_process_publish_post` unless the user explicitly asked for it.


## Change structure with add, remove, and move

Structural edits use the flow-element add tool for BPMN subprocesses, the elements tools for extension elements, and generic delete and move tools.

Before assembling any new module, subprocess, `dataCollectionQuestion`, `bpmnSubProcessCondition`, `mapping`, `widget`, or other extension element, always call `bpmn_process_xml_schema_get` with a targeted `grep` and read the relevant `xs:attributeGroup` and `xs:complexType` for the element you intend to create. Every attribute you set through `initial_attrs` or `bpmn_process_element_attributes_patch` must appear in the schema; if it does not, do not send it. Consult a matching template with `templates_get` in addition to the schema when the user wants a use-case-shaped scaffold — the schema tells you what is possible, the template shows how a working example uses it.

1. `flow_element_add_post(tenant_id, bpmn_process_id, body={"tag":"subProcess", "type":"<SubProcessTypeEnum value>", "parent_id":..., "index":<position>})` — creates a BPMN subprocess under a process or subprocess and returns the new subprocess id in `data`. `type` must be an exact `SubProcessTypeEnum` value; resolve it with `bpmn_process_xml_schema_get(grep=...)` (see the examples), never guess it from a label or memory. `index` is required: `0` puts it first, a large number appends it. Use the process id as `parent_id` for a top-level subprocess. This tool has no `dry_run`; check the round trip right after it.
2. `bpmn_process_elements_post(tenant_id, process_id, body={"parent_id":..., "element_type":..., "position":?, "initial_attrs":{...}})` — creates a LoyJoy extension element under the given parent. `parent_id` is required and must be inside `body`; passed as a top-level argument it is not forwarded and the call fails. `element_type` is the **camelCase** local name declared in the XSD (e.g. `dataCollectionQuestion`, `bpmnSubProcessCondition`, `instruction`, `widgetGroup`, `vEvent`). It cannot create subprocesses, and it refuses `i18n` (use `i18n_by_key_put`). Resolve valid keys from `ExtensionElementsType`: every `loyjoy:<name>` ref inside its `xs:choice` is a valid `element_type`, stripped of the `loyjoy:` prefix. `initial_attrs` is a string map; protected attributes are rejected. Put instruction `type` and `text` into `initial_attrs`, or change an existing instruction's `text` later with `bpmn_process_element_attributes_patch`. For localized text, call `i18n_by_key_put` with the key `<slot>/<new-element-id>` once per locale.
3. `bpmn_process_element_delete(tenant_id, process_id, element_id)` — deletes an element. The server cascades reference cleanup: nulls jump targets on Process, SubProcess, ListElement, ScannerCategory and SnapshotCategory that pointed at a removed SubProcess; drops orphan `DmnEntry` rows; deletes unreferenced `Asset` files. With `dry_run=true` nothing is deleted, not even asset files. It refuses to remove the `Process`, `Definitions`, or `ExtensionElements` containers.
4. `bpmn_process_element_move_post(tenant_id, process_id, element_id, body={"new_parent_id":?, "position":?})` — reorder within the current parent (omit `new_parent_id`) or re-parent (provide `new_parent_id`). The element keeps its `id`, so cross-references stay valid. Refuses to move a container element and refuses to move an element into its own subtree.

Preview every structural write with `dry_run=true` first and read `data.diff`, `data.roundtrip.is_identical`, and `data.issues`. Only then repeat the same call without `dry_run` and with `expected_revision`. Structural writes are the class of change most likely to smuggle in an invented attribute — an unknown `initial_attrs` key, a hand-picked enum spelling, a misspelled attribute set through the follow-up patch. After the complete structural change is assembled, call `issues_summary_by_bpmn_process_get` once. Details in "Verify every write".


## Edit an agent with raw XML

Before following these steps, answer one question: which specific narrow tool fails to express this change, and why? A change that touches one element always has a narrow tool. If the honest answer is that a narrow call was rejected, fix the call rather than routing around it; the rejection is the server protecting the process. Valid reasons to be here are a refactor across many elements, a migration, or a documented gap in the tool surface. If you cannot name the reason, go back.

1. Fetch the current staging XML with `bpmn_process_xml_get(tenant_id, id)` and modify it locally.
2. Make the smallest change that satisfies the request.
3. Preserve unrelated elements, IDs, namespaces, process metadata, and unknown configuration.
4. Keep the process id unchanged and the process version set to `staging`.
5. Never regenerate `id` or `loyjoy:id-src` values on existing elements. `id-src` is opaque lineage.
6. When an element's `id` must change, update every dependent reference: `loyjoy:i18n` keys of the form `<slot>/<parent-uuid>`, and every attribute whose name ends in `BpmnProcessId`, `BpmnSubProcessId`, or is otherwise a UUID reference (for example `loyjoy:openingHoursOpenJumpBpmnSubProcessId`, `loyjoy:liveExitJumpAutoBpmnSubProcessId`, `loyjoy:jumpDecision1..7BpmnSubProcessId`). Only some are model-checked; dangling references may not surface until runtime.
7. Never alter an attribute whose name ends in `Aes` or another protected attribute; the server rejects the write. Explain that a secret cannot be changed through raw XML editing.
8. Summarize the intended changes before saving when they are broad, ambiguous, or potentially disruptive.
9. Call `bpmn_process_xml_put(tenant_id, id, dry_run=true, body={"xml":"..."})` and review `data.diff`, `data.roundtrip`, and `data.issues`. Check every changed line in `data.diff` against the names you resolved; invented attribute names are not rejected and appear there as written. If `data.roundtrip.is_identical` is false, treat lines removed on the `staging` side as elements the BPMN model does not know and fix them before writing.
10. Call `bpmn_process_xml_put(tenant_id, id, body={"xml":"..."})` without `dry_run`. The response returns the new `revision`.
11. Call `issues_summary_by_bpmn_process_get(tenant_id, id)` and inspect its locale-related issues before reviewing or publishing the change.


## Verify every write

The server does **not** reject or drop invented attribute names. The XSD allows foreign attributes (`xs:anyAttribute processContents="lax"`) and the BPMN deserializer copies every attribute verbatim, because older processes carry legacy attributes that must survive. A misspelled name like `loyjoy:random_enable` (correct: `loyjoy:randomEnable`) or `loyjoy:dtStart` (correct: `loyjoy:dtstart`) is stored as written and only surfaces at runtime, when the agent ignores it. No server-side check catches this, including the XML round trip.

The protection against wrong attribute names is therefore on your side:

1. **Before the write:** resolve every attribute name, enum value, and element type as described in "Resolve attribute names before writing them". This is the step that prevents the mistake.
2. **During the dry run:** read `data.diff`. Every added or changed line must carry exactly the attribute name you resolved, with the expected value. A name that is not character-for-character the resolved one is a mistake, even if the write would be accepted.
3. **After writes without `dry_run`** (`flow_element_add_post`, `i18n_by_key_put`): read the affected element with `bpmn_process_element_get` and compare its attributes and texts with what you intended.

The XML round trip (`data.roundtrip` in a dry run, or `bpmn_process_xml_roundtrip_diff_get(tenant_id, id)`) is still useful for one thing: XML elements the BPMN model does not know can be dropped on deserialization, which matters mainly for `bpmn_process_xml_put`. Require `is_identical=true` before a real `bpmn_process_xml_put`. When it reports removed lines (only on the `staging` side), treat them as elements you invented or misspelled and fix them before writing; added lines (only on the `staging_roundtrip` side) are usually serializer artefacts such as attribute order or whitespace.

`is_identical=true` does not mean that attribute names are correct, nor that the process is structurally or semantically valid. Do not use it as a general "does the process look ok" probe.


## Model-check the completed staging change

Call `issues_summary_by_bpmn_process_get(tenant_id, id)` after a related set of writes is complete, not after every intermediate write. Multi-step construction commonly has temporarily incomplete states, so model-checking each step produces noise rather than useful guidance.

- `is_valid=true` means there are no CRITICAL or BLOCKER model-checking issues.
- `blocking_count` counts CRITICAL and BLOCKER issues. Publishing is refused while this is greater than zero.
- `warning_count` counts all non-blocking model-checking issues. Summarize relevant warnings for the user, but do not call them runtime failures.
- `issues` contains the model-checking findings and their affected entity ids.

`issues_by_bpmn_process_get` returns only the bare issue list; prefer the summary. Model checking does not prove that the agent answers correctly or that its content meets the user's intent. It complements the round trip check; it does not replace it.

To try the agent's answer to a single message, `completion_eval_message_post(tenant_id, body={"process_id":..., "text":"...", "locale":"de"})` sends it to the process's AI agent and returns the response. Use it sparingly; every call runs the language model.


## Keep every configured language complete

Before changing or adding localized text, use `bpmn_process_xml_get(tenant_id, id, grep="loyjoy:locales", context=1)` to read the exact locales configured on the process. If the attribute is absent, inspect `loyjoy:defaultLocale` and the process XML before writing; do not assume that only `de` and `en` exist.

For every i18n text affected by the request:

1. Locate the existing i18n element and its `key`, or derive the key `<slot>/<parent-id>` for a new text from the schema and a working template.
2. Provide a non-blank value for every configured process locale with `i18n_by_key_put`. If the user supplied wording for only one locale and translating it requires judgment, ask for the missing translations instead of publishing a partially translated element.
3. Run `issues_summary_by_bpmn_process_get(tenant_id, id)` after the related text writes and inspect every `LOCALE_NOT_MAINTAINED` issue. Use the affected entity ids and `bpmn_process_element_get` to identify the missing localized values.
4. If locale-related issues are unrelated to the current task, report their entity ids. Do not broaden a narrow user request by inventing or overwriting unrelated translations.

To set an intentionally empty localized text, call `i18n_by_key_put(..., locale="<locale>", body={"value":{"<locale>":""}})`. For a multilingual entry that still contains text in another locale, model checking reports `LOCALE_NOT_MAINTAINED`; explain the finding and do not publish unless the empty text is intentional and explicitly approved.

For non-i18n scalar text attributes, including an instruction's `text`, a blank `value` in `bpmn_process_element_attributes_patch` removes the attribute. If the user wants to delete the whole instruction or i18n entry rather than only clear its text, use `bpmn_process_element_delete` after confirmation.


## Publish an agent

Publishing changes production behavior. Call `bpmn_process_publish_post` only when the user explicitly asks to publish or explicitly approves the reviewed staged changes.

Before publishing:

1. Make sure every write of the task was verified as described in "Verify every write".
2. Call `issues_summary_by_bpmn_process_get(tenant_id, id)`, require `blocking_count=0`, and review every `LOCALE_NOT_MAINTAINED` issue unless the user has explicitly approved the affected localized values.
3. Call `bpmn_processes_versions_diff_get(tenant_id, bpmn_process_id)` and verify that staging contains only the changes the user intends to publish.
4. Give a concise summary of what will enter production.
5. Call `bpmn_process_publish_post(tenant_id, body={"bpmn_process_id": ..., "comment": "..."})` with a meaningful publication comment describing the change.

If the server answers `HTTP 409` with critical model-checking issues, the publish did not happen. Show the issues, fix them, and check again. There is no way to skip the check through MCP; if the user insists on publishing despite the issues, tell them to publish from the Manager UI.

Do not interpret a request to edit, update, configure, or fix an agent as permission to publish it.


## Read-only requests

For inspection, explanation, review, or comparison requests, do not call any write tool (`bpmn_process_create_post`, `bpmn_process_xml_put`, `i18n_by_key_put`, `bpmn_process_element_attributes_patch`, `flow_element_add_post`, `bpmn_process_elements_post`, `bpmn_process_element_delete`, `bpmn_process_element_move_post`, `bpmn_process_publish_post`). Use `bpmn_processes_get`, `search_get`, `bpmn_process_xml_get`, `bpmn_process_element_get`, `bpmn_processes_versions_diff_get`, `bpmn_process_xml_schema_get`, `bpmn_process_xml_roundtrip_diff_get`, `issues_summary_by_bpmn_process_get`, `templates_get`, `template_xml_get`, `templates_xml_grep_get`, `home_views_get`, `home_view_get`, `home_view_xml_get`, and `bpmn_process_analysis_get` as needed. `bpmn_processes_versions_diff_get` is the right tool for "what changed", "what is not live yet", and "compare staging to production" questions.


## Report the outcome

State:

- Which tenant, process, and modules changed, and which tool performed the change.
- Whether changes are only staged or have been published.
- The `previous_value` and `new_value` returned by an attribute or list write, or the returned element id for a structural add.

If you have not read [references/examples.md](references/examples.md) yet in this task, read it before the next write. It shows the call sequence for each common change.
