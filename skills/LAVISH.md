---
name: lavish
description: Create and review rich HTML artifacts with the installed Lavish AXI CLI when a complex plan, comparison, diagram, UI proposal, report, or other visual explanation is clearer than prose.
---

# Lavish AXI Route

Use the public `lavish-axi` CLI installed by the global setup tool.

This skill provides stable routing conditions while the CLI remains the current source of command and design guidance.

## Load this skill when

- A complex implementation or refactoring plan benefits from interactive review.

- A comparison, architecture, dependency flow, timeline, table, code review, report, or diagram is easier to understand visually.

- The user asks for a prototype, visual proposal, or annotatable HTML artifact.

- The user explicitly mentions `lavish`, `lavish-axi`, or requests an interactive HTML review loop.

## Do not load this skill when

- A short factual answer, small code edit, or simple explanation is clearer as plain text.

- The task only needs a browser test of an existing application.

- The output would expose company information through public sharing.

## Workflow

1. Run `command -v lavish-axi` and stop with a clear setup error if the installed command is unavailable.

2. Run `lavish-axi --help` before using the tool so the installed CLI remains the command source of truth.

3. Run `lavish-axi design` and every relevant `lavish-axi playbook <id>` before authoring a substantial artifact.

4. Store generated review artifacts under the current workspace in `.lavish/` unless the project defines another artifact directory.

5. Open the artifact with `lavish-axi <html-file>` and keep `lavish-axi poll <html-file>` attached to the active agent turn while waiting for feedback.

6. Apply the feedback, update the artifact, and continue polling until the user ends the review or the agreed review is complete.

7. End an agent-owned session with `lavish-axi end <html-file>` and stop the server when it is no longer needed.

Never run `lavish-axi share` unless the user explicitly requests publication and confirms that company policy permits the selected visibility.

Prefer the installed `lavish-axi` command and do not download another copy with `npx -y` when that command is available.
