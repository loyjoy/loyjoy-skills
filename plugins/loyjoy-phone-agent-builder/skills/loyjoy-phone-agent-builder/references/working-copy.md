# The session working file: iterate on the file, not in the chat

Reference for `loyjoy-phone-agent-builder`. Read when drafting or iterating a custom block, and before writing a block to the platform. Section names referenced without a file belong to `SKILL.md`.

## Why a file

Reprinting the full custom block in the chat on every iteration wastes the conversation, invites drift between rounds, and makes a revert impossible. During a job the block is therefore a file, the single source of truth. Every change is a line-scoped edit to that file. The block is never reprinted in the chat while iterating, and the user is never shown a diff; the handover is the file itself, or the platform write from it.

## Materialization

- Session-local directory, scratch only: `<session-workdir>/.loyjoy-work/<tenant>-<agent>/`. Never committed, never published, never shipped as-is.
- `custom.txt` — the current custom block. Connected mode: from `process_get_xml_grep`. Advisory mode: from the user-provided text.
- `standard.txt` — the extracted LoyJoy standard voice prompt, as the checker reference (see Den Standard-Prompt lesen in `SKILL.md`).
- Materialize both before the first draft or edit (Order of operations in `SKILL.md`).

## Iteration loop

1. Snapshot the file before each decision point: `custom.r00.txt`, `custom.r01.txt`, … Snapshots are copies, never edited.
2. Edit `custom.txt` line by line, one logical change per round.
3. Run `scripts/prompt_check.py custom.txt --standard standard.txt` on every round. Findings name file lines and sections; fix them at those lines. A round ends only when `duplicate`, `standard`, and `topics` report no ERROR; accepted WARNs are named in the round report.
4. Report the round in the chat in one or two sentences: what changed and why, what was removed. No block text, no diff.
5. Revert means copying the affected lines back from a snapshot with an edit. No git.

## Handover

After approval, by size of the change:

- **Small change** (one line, one wording): state the changed line and a one-clause confirmation. No file handover.
- **Large or structural change**: hand over the complete final file (e.g. as `custom_final.txt`), or, in Connected mode, write directly from the file content with `process_set_attribute(process_id, element_id, name="text", value=<complete content of custom.txt>)`, then round-trip check, `process_model_check`, `process_diff`.

Every write, to the platform or to the customer, uses the complete file content. Never write a subset of the file.

## Customer delivery

Unchanged (see `references/debugging-and-delivery.md`). The `.txt` attachment for customers is produced from the final working file; the delivery checklist applies in full.
