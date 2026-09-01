# LoyJoy headless interaction patterns

Every pattern below shows the same underlying shape: locate the element, then change exactly that element with the narrowest tool that fits. The full-XML path appears once, at the end, for the one case where nothing narrower works.


## Change an AI agent instruction

User request: "Make the support agent answer more concisely."

1. `processes_list` to resolve the agent to a process id.
2. `process_get_xml_grep(process_id, pattern="loyjoy:instruction", context_before=1, context_after=3)` to find the instruction elements and their ids. Do not download the full XML for this.
3. Read the matched instruction `text` and `type` (`custom`, `basis`, `context`, `answer_language`, ...) to confirm you have the right one. Ask the user if several plausible candidates come back.
4. `process_set_attribute(process_id, element_id=instruction_id, name="text", value="...")` with the revised text. Instruction attributes are unqualified, so use `text`, not `loyjoy:text`.
5. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
6. `process_model_check(process_id)` after this completed change. Report blocking issues and relevant warnings, including any `LOCALE_NOT_MAINTAINED` issues.
8. Report the returned previous and new text so the user can verify, and state that the change is staged only.
The instruction body is the whole payload here, so one call does the entire job. Reading and rewriting the surrounding XML would add risk without adding anything.

## Change a single scalar attribute

User request: "Set the chat widget width to 480."

1. `process_get_xml_grep(process_id, pattern="(?i)widgetChatWidth", context_before=2)`. A hit gives you both the exact attribute name with its prefix and the `id` of the element carrying it.
2. If the process does not carry the attribute yet, `process_get_xml_schema_grep(pattern="(?i)widgetChatWidth", context_before=3)`. The `form="qualified"` marker tells you to pass it as `loyjoy:widgetChatWidth`; the declared type tells you how to format the value.
3. `process_set_attribute(process_id, element_id, name="loyjoy:widgetChatWidth", value="480")`.
4. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
5. `process_model_check(process_id)` after this completed change. Inspect any `LOCALE_NOT_MAINTAINED` issues even though this was a scalar change.
6. Report previous and new value together with relevant model-checking issues.


## Clear a localized text

User request: "Remove the English subtitle but keep the other languages."

1. `process_get_xml_grep(process_id, pattern="loyjoy:locales|<the-i18n-key>", context_before=2)` to confirm that `en` is configured and locate the exact i18n element id.
2. Explain that clearing only `en` will make this i18n entry incomplete while English remains a configured process locale. If that is what the user intends, call `process_put_i18n(process_id, i18n_id, locale="en", text="")`. Empty and whitespace-only text values are accepted and returned as `new_text=""`; they do not delete the i18n element or other locale values.
3. `process_staging_xml_roundtrip_diff(process_id)` and require `is_identical=true`.
4. `process_model_check(process_id)` and confirm that the cleared multilingual element produces a `LOCALE_NOT_MAINTAINED` issue for the affected entity.
5. Use `process_remove_element` instead, after confirmation, only when the user wants to delete the entire localized entry in every language.


## Add an item to a list attribute

User request: "Add 'gewinnspiel' to the blocked words."

1. `process_get_xml_grep(process_id, pattern="aiBlockWords", context_before=2)` to get the element id and see the current array.
2. `process_put_list_attribute(process_id, element_id, name="loyjoy:aiBlockWords", add=["gewinnspiel"])`.
3. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
4. `process_model_check(process_id)` after this completed change, including review of locale-related warnings.
Send the delta, not the rebuilt array. If two edits race, a delta merges and a full reserialization silently drops the other edit.


## Add a module (subprocess)

User request: "Add a live chat handover to the service agent."

1. Resolve the enum value by searching backwards from the label the user used, not by paging through the enumeration. `SubProcessTypeEnum` has well over a hundred entries and the context window of a grep caps at 5 lines each way, so scanning it is slow. Instead grep the annotation and let `context_before` reveal the constant:
   `process_get_xml_schema_grep(pattern="xml:lang=\"de\">Live-Chat<", context_before=3)`
   returns the enclosing `<xs:enumeration value="LIVE_SUBPROCESS">` in one call. Use `xml:lang="en"` for English labels. Confirmed mappings from this pattern: "Live-Chat" is `LIVE_SUBPROCESS`, "AI-Agent" is `AI_AGENT_SUBPROCESS`, "AI-Wissen" is `AI_KNOWLEDGE_SUBPROCESS`, "Formular" is `FORM_SUBPROCESS`. If the label is a guess, try a looser pattern such as `(?i)xml:lang="de">[^<]*kalender` before falling back to reading the enumeration. Never infer the constant from the label yourself: the naming is not mechanical.
2. `process_get_xml_grep(process_id, pattern="subProcess", context_before=1)` to decide where it belongs and to get the `parent_id`. Use the process id as parent for a top-level subprocess.
3. `process_add_subprocess(process_id, parent_id, subprocess_type="LIVE_SUBPROCESS", position=?)`. The server generates the element identity and enforces parent-child compatibility.
4. `process_staging_xml_roundtrip_diff(process_id)`. Do not configure the module until it returns `is_identical=true`.
5. Fill in scalar configuration on the returned id with `process_set_attribute`. Add a new instruction with `process_add_extension_element(process_id, parent_id=<returned-subprocess-id>, element_type="instruction", initial_attrs={"type":"custom","text":"..."})`. Create localized text as an `i18n` child with the correct template-derived `key`, then pass the returned i18n id to `process_put_i18n` for each configured locale. Resolve every attribute, enum, and i18n key first.
6. Call `process_staging_xml_roundtrip_diff(process_id)` immediately after each individual write in step 5 and do not start the next write until it returns `is_identical=true`.
7. After the module and all its child elements are complete, call `process_model_check(process_id)` once and inspect `LOCALE_NOT_MAINTAINED` issues.
8. Report which module and child elements were added, any locale-related or other model-checking issues, and that the changes are staged.
This is five to eight calls where the full-XML route is one. That is the point: each of those calls is either a read that cannot break anything or a write the server validates against the schema and the surrounding graph. Hand-assembling the same subprocess in raw XML means generating your own UUIDs and wiring your own i18n keys, and a mistake there surfaces at runtime in production, not in the response you get back.


## Add a nested extension element

User request: "Add a question for the email address to the data collection module."

1. `process_get_xml_schema_grep(pattern="ExtensionElementsType", context_after=5)` to confirm `dataCollectionQuestion` is a valid `element_type` under the intended parent. The key is the camelCase local name without the `loyjoy:` prefix.
2. `process_get_xml_schema_grep(pattern="DataCollectionQuestionTypeEnum", context_after=5)` for the question type, and the matching `xs:attributeGroup` for the attributes you plan to seed.
3. `process_get_xml_grep(process_id, pattern="loyjoy:locales|dataCollectionQuestion", context_before=3)` to read every configured locale, locate the parent element id, and see how existing questions in this process are shaped.
4. `process_add_extension_element(process_id, parent_id, element_type="dataCollectionQuestion", initial_attrs={...})` with only attributes you verified in the schema. Retain the returned question id.
5. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
6. Resolve the correct i18n slot/key from the schema and a working template. Create the localized text element with `process_add_extension_element(process_id, parent_id=<question-id>, element_type="i18n", initial_attrs={"key":"<slot>/<question-id>"})` and retain the returned i18n id.
7. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
8. Call `process_put_i18n(process_id, i18n_id=<returned-i18n-id>, locale, text)` once for every locale configured on the process, checking with `process_staging_xml_roundtrip_diff(process_id)` immediately after every locale write.
9. After the question and all localized texts are complete, call `process_model_check(process_id)` once. Resolve any `LOCALE_NOT_MAINTAINED` issue affecting the new i18n entry.


## Create a phone agent

User request: "Erstelle einen Phone Agent für uns."

A phone agent is a process with two hard invariants: `loyjoy:type="phone_agent"` on the `Process`, and exactly one `AI_AGENT_SUBPROCESS` module inside it. Do not rely on that timing: create the module explicitly so the process is complete after your last write and the seeded instructions and tools land in the same task.

1. `process_create(name, default_locale, folder?)` — returns the new `process_id`. The process is empty: no type, no modules.
2. `process_staging_xml_roundtrip_diff(process_id)`. Confirm that the newly created empty process round-trips before adding configuration.
3. `process_set_attribute(process_id, element_id=process_id, name="loyjoy:type", value="phone_agent")` on the `Process` element. The valid enum values are `ai_agent`, `chat_agent`, `phone_agent`; anything else silently produces a broken agent. If unsure, verify with `process_get_xml_schema_grep(pattern="phone_agent", context_before=3)`.
4. `process_staging_xml_roundtrip_diff(process_id)`. A `remove` on `loyjoy:type` means the value was rejected. Do not continue until it returns `is_identical=true`.
5. `process_add_subprocess(process_id, parent_id=process_id, subprocess_type="AI_AGENT_SUBPROCESS")`. Exactly one. Retain the returned AI agent subprocess id.
6. `process_staging_xml_roundtrip_diff(process_id)`. Confirm that the module survived deserialization before adding its children.
7. Resolve `InstructionAttributesGroup` and the relevant `InstructionTypeEnum` entry from the schema. Create the custom instruction with `process_add_extension_element(process_id, parent_id=<ai-agent-subprocess-id>, element_type="instruction", initial_attrs={"type":"custom","text":"<instruction>"})`. Consult the loyjoy-phone-agent-builder skill for the actual prompt content.
8. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
9. Add every required AI tool with `process_add_extension_element(element_type="tool", ...)`, using the schema and a matching template to resolve its attributes and any nested mappings. Validate immediately after every tool or mapping write.
10. Configure branding and other scalar settings with `process_set_attribute`. For every localized text, first create an `i18n` child with its correct template-derived key, check its round trip, and then call `process_put_i18n` on the returned i18n id once per configured locale, checking the round trip after every call.
11. Grep for `AI_AGENT_SUBPROCESS` and confirm that exactly one exists. Then call `process_model_check(process_id)` once for the completed agent, inspect `LOCALE_NOT_MAINTAINED` issues, and follow with `process_diff(process_id)`. Report the process id, AI agent subprocess id, created instruction/tool/i18n ids, locale-related and other model-checking issues, and that the changes are staged only.

Do not add a second `AI_AGENT_SUBPROCESS`. If one already exists (either because the server seeded one between your writes or because you accidentally called `process_add_subprocess` twice), the singleton invariant is violated and the assure service will not repair it — you have to remove the extra one with `process_remove_element`. Grep for `AI_AGENT_SUBPROCESS` after the add if you are not sure.


## Reorder or re-parent instead of rewriting

User request: "Move the FAQ module above the product finder."

1. `process_get_xml_grep(process_id, pattern="subProcess", context_before=1)` to get both element ids and the current order.
2. `process_move_element(process_id, element_id, new_position=?)`, omitting `new_parent_id` for a reorder within the same parent.
3. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
4. `process_model_check(process_id)` after the completed move, including review of locale-related warnings.
The element keeps its `id`, so every jump reference and i18n key stays valid. Rewriting the XML to reorder children is the classic case where references break silently.


## Remove a module

User request: "Delete the raffle module."

1. Locate the element id with `process_get_xml_grep`.
2. Summarize to the user what will disappear and ask for confirmation before deleting.
3. `process_remove_element(process_id, element_id)`. The server nulls jump targets that pointed at it, drops orphan DMN entries, and deletes unreferenced assets.
4. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
5. `process_model_check(process_id)` after the completed removal and reference cleanup, including review of locale-related warnings.
Removing the same element from raw XML leaves all of that behind as dangling references.


## Verify a set of changes before publishing

1. `process_diff(process_id)` to see the structured diff between the published and staging versions. The default comparison is `prod` against `staging`.
2. `process_staging_xml_roundtrip_diff(process_id)` and require `is_identical=true` for the latest write.
3. `process_model_check(process_id)`, require `blocking_count=0`, and review every `LOCALE_NOT_MAINTAINED` issue unless the user explicitly approves the affected localized values.
4. Walk the diff and non-blocking model-checking issues with the user and confirm the diff contains only intended changes.
5. Publish only if the user explicitly asks: `process_publish(process_id, comment)` with a comment describing the change.


## The one case for full-XML replacement

User request: "Rename our old variable keys across all 40 modules to the new naming scheme."

A change is a candidate for `process_put_xml` when it touches many elements at once and no sequence of narrow calls expresses it atomically. Even then:

1. `process_get_xml` and retain the complete current staging XML.
2. Apply the smallest possible edit locally. Keep every `id` and `loyjoy:id-src`, every namespace, every attribute you did not come to change.
3. Leave `*Aes` attributes untouched. Their ciphertext cannot be edited meaningfully; if the user wants the secret changed, say so instead of writing something.
4. Summarize the intended changes to the user before saving.
5. `process_put_xml(process_id, xml)` with the complete updated staging XML.
6. `process_staging_xml_roundtrip_diff(process_id)`. Do not continue until it returns `is_identical=true`.
7. `process_model_check(process_id)` after the complete XML change and inspect locale-related warnings.
8. `process_diff` afterwards to confirm nothing outside the intended scope moved.
If you find yourself on this path for a change that touches one element, you took a wrong turn several steps ago. Go back and find the narrow tool.


## Ambiguous agent name

If `processes_list` returns multiple plausible agents, present their names and ids and ask which one to modify. Do not infer from ordering.


## Rejected write

If a narrow tool rejects an attribute name, the name is wrong, not the tool. Resolve it with `process_get_xml_schema_grep` and retry. Do not fall back to `process_put_xml` to route around the rejection: the rejection is the server protecting the process, and raw XML bypasses that protection rather than satisfying it.


## Encrypted configuration

If a requested change affects an attribute ending in `Aes`, do not edit its ciphertext. Look for a dedicated MCP tool that accepts the clear value and encrypts server-side. If none exists, leave the attribute unchanged and explain which capability is missing.
