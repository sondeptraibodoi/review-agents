# TuLN's Agent Instructions

These are common instructions for TuLN's agents across all scenarios.

## General Guidelines

- Never use the em dash character.
- Use the plain dash character instead.
- In git commit messages, NEVER auto-add your agent name as co-author.
- Never manually modify CHANGELOG.md files or any files that are marked as auto-generated.
- When writing or substantially editing long Markdown files, put each full sentence on its own line.
- Preserve normal Markdown structure, but avoid wrapping multiple sentences onto one physical line.
- When making technical decisions, do not give much weight to development cost.
- Prioritize simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user would experience it as possible.
- When end-to-end testing a product, be picky about the UI you see and be obsessed with pixel perfection.
- If something clearly looks off, even if it is not directly related to what you are doing, try to get it fixed along with your changes.
- Apply that same high standard to engineering excellence: lint, test failures, and test flakiness.
- If you see one, fix it.

## Resource-safe builds

- Finish coding and relevant tests or E2E before running the production build; do not rebuild after every small edit.
- On an 8 GB WSL2 environment, `nx run-many` is allowed, but run one build task at a time with `--parallel=1` and limit Node.js with `NODE_OPTIONS=--max-old-space-size=4096`.

## TuLN's Opinions

When a task would benefit from TuLN's viewpoints, load the installed `tuln-opinions` skill.

## Python tools

Before using Python or managing Python dependencies, load the installed `python-tools` skill.

## Lavish visual planning and review

Load the installed `lavish` skill for complex plans or visual artifacts that benefit from visual review, but not for factual answers, simple explanations, or small code edits.

## Browser E2E and Chrome debugging

Load the installed `chrome-devtools-axi` skill for frontend, UI, or E2E work requiring a real browser to reproduce user flows and inspect the UI, console, network, viewports, or screenshots; skip it when HTTP or static source inspection is sufficient.
