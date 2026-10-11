# LoyJoy headless interaction patterns

Every pattern below shows the same underlying shape: locate the element, then change exactly that element with the narrowest tool that fits. The full-XML path appears once, at the end, for the one case where nothing narrower works.

All calls carry the `tenant_id` confirmed with `list_tenants` at the start of the task; it is left out below for brevity. Request bodies go into the argument `body`, responses arrive in `data`.


## Change an AI agent instruction

User request: "Make the support agent answer more concisely."

1. `bpmn_processes_get` to resolve the agent to a process id.
2. `bpmn_process_xml_get(id=process_id, grep="loyjoy:instruction", context=3)` to find the instruction elements and their ids. Do not download the full XML for this.
3. `bpmn_process_element_get(process_id, element_id=instruction_id, depth=0)` to read the current `text` and `type` (`custom`, `basis`, `context`, `answer_language`, ...) and the `revision`. Ask the user if several plausible candidates come back.
4. `bpmn_process_element_attributes_patch(process_id, element_id=instruction_id, dry_run=true, body={"name":"text","value":"..."})`. Instruction attributes are unqualified, so use `text`, not `loyjoy:text`. Check that `data.diff` changes exactly the `text` attribute of this instruction.
5. The same call without `dry_run` and with `expected_revision=<revision>`.
6. `issues_summary_by_bpmn_process_get(id=process_id)` after this completed change. Report blocking issues and relevant warnings, including any `LOCALE_NOT_MAINTAINED` issues.
7. Report `data.result.previous_value` and `data.result.new_value` so the user can verify, and state that the change is staged only.

The instruction body is the whole payload here, so one write does the entire job. Reading and rewriting the surrounding XML would add risk without adding anything.


## Change a single scalar attribute

User request: "Set the chat widget width to 480."

1. `bpmn_process_xml_get(id=process_id, grep="(?i)widgetChatWidth", context=2)`. A hit gives you both the exact attribute name with its prefix and the `id` of the element carrying it.
2. If the process does not carry the attribute yet, `bpmn_process_xml_schema_get(grep="(?i)widgetChatWidth", context=3)`. The `form="qualified"` marker tells you to pass it as `loyjoy:widgetChatWidth`; the declared type tells you how to format the value.
3. `bpmn_process_element_get(process_id, element_id, depth=0)` for the `revision`.
4. `bpmn_process_element_attributes_patch(process_id, element_id, dry_run=true, body={"name":"loyjoy:widgetChatWidth","value":"480"})`, check that `data.diff` shows exactly `loyjoy:widgetChatWidth="480"`, then the same call without `dry_run` and with `expected_revision`.
5. `issues_summary_by_bpmn_process_get(id=process_id)` after this completed change. Inspect any `LOCALE_NOT_MAINTAINED` issues even though this was a scalar change.
6. Report previous and new value together with relevant model-checking issues.


## Clear a localized text

User request: "Remove the English subtitle but keep the other languages."

1. `bpmn_process_xml_get(id=process_id, grep="loyjoy:locales|<the-i18n-key>", context=2)` to confirm that `en` is configured and to read the exact i18n `key`.
2. Explain that clearing only `en` will make this i18n entry incomplete while English remains a configured process locale. If that is what the user intends, call `i18n_by_key_put(bpmn_process_id=process_id, key="<the-i18n-key>", locale="en", body={"value":{"en":""}})`. Empty and whitespace-only texts are accepted; they do not delete the i18n element or other locale values.
3. `bpmn_process_element_get(process_id, element_id=<i18n-element-id>)` and confirm that only the `en` text is empty.
4. `issues_summary_by_bpmn_process_get(id=process_id)` and confirm that the cleared multilingual element produces a `LOCALE_NOT_MAINTAINED` issue for the affected entity.
5. Use `bpmn_process_element_delete` instead, after confirmation, only when the user wants to delete the entire localized entry in every language.


## Add an item to a list attribute

User request: "Add 'gewinnspiel' to the blocked words."

1. `bpmn_process_xml_get(id=process_id, grep="aiBlockWords", context=2)` to get the element id and see the current array.
2. `bpmn_process_element_attributes_patch(process_id, element_id, dry_run=true, body={"name":"loyjoy:aiBlockWords","add":["gewinnspiel"]})`, check in `data.diff` that only `loyjoy:aiBlockWords` changes, then the same call without `dry_run` and with `expected_revision` from `bpmn_process_element_get`.
3. `issues_summary_by_bpmn_process_get(id=process_id)` after this completed change, including review of locale-related warnings.

Send the delta, not the rebuilt array. If two edits race, a delta merges and a full reserialization silently drops the other edit.


## Add a module (subprocess)

User request: "Add a live chat handover to the service agent."

1. Resolve the enum value by searching backwards from the label the user used, not by paging through the enumeration. `SubProcessTypeEnum` has well over a hundred entries and the context of a grep caps at 5 lines, so scanning it is slow. Instead grep the annotation and let the context reveal the constant:
   `bpmn_process_xml_schema_get(grep="xml:lang=\"de\">Live-Chat<", context=3)`
   returns the enclosing `<xs:enumeration value="LIVE_SUBPROCESS">` in one call. Use `xml:lang="en"` for English labels. Confirmed mappings from this pattern: "Live-Chat" is `LIVE_SUBPROCESS`, "AI-Agent" is `AI_AGENT_SUBPROCESS`, "AI-Wissen" is `AI_KNOWLEDGE_SUBPROCESS`, "Formular" is `FORM_SUBPROCESS`. If the label is a guess, try a looser pattern such as `(?i)xml:lang="de">[^<]*kalender` before falling back to reading the enumeration. Never infer the constant from the label yourself: the naming is not mechanical.
2. `bpmn_process_xml_get(id=process_id, grep="subProcess", context=1)` to decide where it belongs and to get the `parent_id`. Use the process id as parent for a top-level subprocess.
3. `flow_element_add_post(bpmn_process_id=process_id, body={"tag":"subProcess","type":"LIVE_SUBPROCESS","parent_id":<parent-id>,"index":<position>})`. The server generates the element identity and enforces parent-child compatibility; `data` is the new subprocess id.
4. `bpmn_process_element_get(process_id, element_id=<returned-subprocess-id>)` to confirm the new module, its `loyjoy:type`, and its parent.
5. Fill in scalar configuration on the returned id with `bpmn_process_element_attributes_patch`. Add a new instruction with `bpmn_process_elements_post(process_id, body={"parent_id":<returned-subprocess-id>,"element_type":"instruction","initial_attrs":{"type":"custom","text":"..."}})`. Create localized text with `i18n_by_key_put(bpmn_process_id=process_id, key="<slot>/<returned-subprocess-id>", locale, body={"value":{"<locale>":"..."}})` for each configured locale; the server creates the i18n element under the module. Resolve every attribute, enum, and i18n key first.
6. Preview each patch and elements write in step 5 with `dry_run=true` and check its `data.diff`; after each `i18n_by_key_put`, read the element with `bpmn_process_element_get`. Do not start the next write until the previous one is verified.
7. After the module and all its child elements are complete, call `issues_summary_by_bpmn_process_get(id=process_id)` once and inspect `LOCALE_NOT_MAINTAINED` issues.
8. Report which module and child elements were added, any locale-related or other model-checking issues, and that the changes are staged.

This is five to eight calls where the full-XML route is one. That is the point: each of those calls is either a read that cannot break anything or a write the server validates against the schema and the surrounding graph. Hand-assembling the same subprocess in raw XML means generating your own UUIDs and wiring your own i18n keys, and a mistake there surfaces at runtime in production, not in the response you get back.


## Add a nested extension element

User request: "Add a question for the email address to the data collection module."

1. `bpmn_process_xml_schema_get(grep="ExtensionElementsType", context=5)` to confirm `dataCollectionQuestion` is a valid `element_type` under the intended parent. The key is the camelCase local name without the `loyjoy:` prefix.
2. `bpmn_process_xml_schema_get(grep="DataCollectionQuestionTypeEnum", context=5)` for the question type, and the matching `xs:attributeGroup` for the attributes you plan to seed.
3. `bpmn_process_xml_get(id=process_id, grep="loyjoy:locales|dataCollectionQuestion", context=3)` to read every configured locale, locate the parent element id, and see how existing questions in this process are shaped.
4. `bpmn_process_elements_post(process_id, dry_run=true, body={"parent_id":<parent-id>,"element_type":"dataCollectionQuestion","initial_attrs":{...}})` with only attributes you verified in the schema. Check every attribute name in `data.diff` against the schema, then repeat without `dry_run` and with `expected_revision`. Retain the returned `element_id` of the question.
5. Resolve the correct i18n slot/key from the schema and a working template.
6. Call `i18n_by_key_put(bpmn_process_id=process_id, key="<slot>/<question-id>", locale, body={"value":{"<locale>":"..."}})` once for every locale configured on the process. The first call creates the i18n element under the question; `bpmn_process_elements_post` refuses `element_type="i18n"`. Read the question with `bpmn_process_element_get(depth=1)` afterwards and confirm the i18n child and its texts.
7. After the question and all localized texts are complete, call `issues_summary_by_bpmn_process_get(id=process_id)` once. Resolve any `LOCALE_NOT_MAINTAINED` issue affecting the new i18n entry.


## Create a phone agent

User request: "Erstelle einen Phone Agent für uns."

A phone agent is a process with two hard invariants: `loyjoy:type="phone_agent"` on the `Process`, and exactly one `AI_AGENT_SUBPROCESS` module inside it. Create the module explicitly so the process is complete after your last write and the seeded instructions and tools land in the same task.

1. `bpmn_process_create_post(body={"name":..., "default_locale":..., "folder":...})` — returns the new process in `data`; its `id` is the `process_id`. The process is empty: no type, no modules.
2. `bpmn_process_element_get(process_id, element_id=process_id, depth=0)` for the `revision` and the initial attributes.
3. `bpmn_process_element_attributes_patch(process_id, element_id=process_id, dry_run=true, body={"name":"loyjoy:type","value":"phone_agent"})` on the `Process` element, then without `dry_run`. The valid enum values are `ai_agent`, `chat_agent`, `phone_agent`; anything else silently produces a broken agent. If unsure, verify with `bpmn_process_xml_schema_get(grep="phone_agent", context=3)`. Check in `data.diff` that exactly `loyjoy:type="phone_agent"` is added.
4. `flow_element_add_post(bpmn_process_id=process_id, body={"tag":"subProcess","type":"AI_AGENT_SUBPROCESS","parent_id":process_id,"index":0})`. Exactly one. Retain the returned AI agent subprocess id.
5. `bpmn_process_element_get(process_id, element_id=<ai-agent-subprocess-id>)` to confirm the module before adding its children.
6. Resolve `InstructionAttributesGroup` and the relevant `InstructionTypeEnum` entry from the schema. Create the custom instruction with `bpmn_process_elements_post(process_id, body={"parent_id":<ai-agent-subprocess-id>,"element_type":"instruction","initial_attrs":{"type":"custom","text":"<instruction>"}})`, previewed with `dry_run` first. Consult the loyjoy-phone-agent-builder skill for the actual prompt content.
7. Add every required AI tool with `bpmn_process_elements_post(body={..., "element_type":"tool", ...})`, using the schema and a matching template to resolve its attributes and any nested mappings. Preview every tool or mapping write with `dry_run`.
8. Configure branding and other scalar settings with `bpmn_process_element_attributes_patch`. For every localized text, call `i18n_by_key_put` with its correct template-derived key `<slot>/<parent-id>` once per configured locale and read the parent with `bpmn_process_element_get` afterwards.
9. Grep for `AI_AGENT_SUBPROCESS` and confirm that exactly one exists. Then call `issues_summary_by_bpmn_process_get(id=process_id)` once for the completed agent, inspect `LOCALE_NOT_MAINTAINED` issues, and follow with `bpmn_processes_versions_diff_get(bpmn_process_id=process_id)`. Report the process id, AI agent subprocess id, created instruction/tool/i18n ids, locale-related and other model-checking issues, and that the changes are staged only.

Do not add a second `AI_AGENT_SUBPROCESS`. If one already exists (either because the server seeded one between your writes or because you accidentally added it twice), the singleton invariant is violated and the assure service will not repair it — remove the extra one with `bpmn_process_element_delete`. Grep for `AI_AGENT_SUBPROCESS` after the add if you are not sure.


## Reorder or re-parent instead of rewriting

User request: "Move the FAQ module above the product finder."

1. `bpmn_process_xml_get(id=process_id, grep="subProcess", context=1)` to get both element ids and the current order.
2. `bpmn_process_element_move_post(process_id, element_id, dry_run=true, body={"position":<n>})`, omitting `new_parent_id` for a reorder within the same parent. Check `data.diff`, then repeat without `dry_run` and with `expected_revision`.
3. `issues_summary_by_bpmn_process_get(id=process_id)` after the completed move, including review of locale-related warnings.

The element keeps its `id`, so every jump reference and i18n key stays valid. Rewriting the XML to reorder children is the classic case where references break silently.


## Remove a module

User request: "Delete the raffle module."

1. Locate the element id with `bpmn_process_xml_get(grep=...)`.
2. `bpmn_process_element_delete(process_id, element_id, dry_run=true)` and use `data.diff` to show the user exactly what will disappear, including the cascaded reference cleanup. Ask for confirmation before deleting. The dry run deletes nothing, not even asset files.
3. `bpmn_process_element_delete(process_id, element_id, expected_revision=<revision>)`. The server nulls jump targets that pointed at it, drops orphan DMN entries, and deletes unreferenced assets.
4. `issues_summary_by_bpmn_process_get(id=process_id)` after the completed removal and reference cleanup, including review of locale-related warnings.

Removing the same element from raw XML leaves all of that behind as dangling references.


## Verify a set of changes before publishing

1. `bpmn_processes_versions_diff_get(bpmn_process_id=process_id)` to see the structured diff between the published and staging versions. The default comparison is `prod` against `staging`.
2. Make sure every write of the task was verified (dry-run diff or `bpmn_process_element_get`, and `is_identical=true` for an XML replacement).
3. `issues_summary_by_bpmn_process_get(id=process_id)`, require `blocking_count=0`, and review every `LOCALE_NOT_MAINTAINED` issue unless the user explicitly approves the affected localized values.
4. Walk the diff and non-blocking model-checking issues with the user and confirm the diff contains only intended changes.
5. Publish only if the user explicitly asks: `bpmn_process_publish_post(body={"bpmn_process_id":process_id,"comment":"..."})` with a comment describing the change. An `HTTP 409` with critical issues means nothing was published.


## The one case for full-XML replacement

User request: "Rename our old variable keys across all 40 modules to the new naming scheme."

A change is a candidate for `bpmn_process_xml_put` when it touches many elements at once and no sequence of narrow calls expresses it atomically. Even then:

1. `bpmn_process_xml_get(id=process_id)` and retain the complete current staging XML.
2. Apply the smallest possible edit locally. Keep every `id` and `loyjoy:id-src`, every namespace, every attribute you did not come to change.
3. Leave `*Aes` and other protected attributes untouched; the server rejects changes to them.
4. Summarize the intended changes to the user before saving.
5. `bpmn_process_xml_put(id=process_id, dry_run=true, body={"xml":"..."})`. Check `data.diff` for anything outside the intended scope and for misspelled attribute names, and require `data.roundtrip.is_identical=true`.
6. `bpmn_process_xml_put(id=process_id, body={"xml":"..."})` without `dry_run`.
7. `issues_summary_by_bpmn_process_get(id=process_id)` after the complete XML change and inspect locale-related warnings.
8. `bpmn_processes_versions_diff_get(bpmn_process_id=process_id)` afterwards to confirm nothing outside the intended scope moved.

If you find yourself on this path for a change that touches one element, you took a wrong turn several steps ago. Go back and find the narrow tool.


## Ambiguous agent name

If `bpmn_processes_get` returns multiple plausible agents, present their names and ids and ask which one to modify. Do not infer from ordering. `search_get(q=...)` helps when the user only remembers a module or text.


## Rejected write

If a write is rejected, read the `issues` of the error: `attribute`, `message`, and `hint` name the cause. A rejected attribute name is wrong, not the tool. Resolve it with `bpmn_process_xml_schema_get(grep=...)` and retry. Do not fall back to `bpmn_process_xml_put` to route around the rejection: the rejection is the server protecting the process, and raw XML is guarded by the same checks.

An `HTTP 409` "Staging process has changed" means somebody else wrote in between. Re-read the element, re-plan the change on the current state, and write again with the new `revision`.


## Encrypted configuration

If a requested change affects an attribute ending in `Aes`, do not edit its ciphertext; every write tool rejects it. Read operations mask the value. If no dedicated tool accepts the clear value and encrypts it server-side, leave the attribute unchanged and explain which capability is missing; the user can set the secret in the Manager UI.
