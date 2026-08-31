---
name: chrome-devtools-axi
description: Run real-browser E2E tests and Chrome debugging with the installed Chrome DevTools AXI CLI for UI flows, rendering, console errors, network failures, screenshots, and performance inspection.
---

# Chrome DevTools AXI Route

Use the public `chrome-devtools-axi` CLI installed by the global setup tool.

This skill provides stable routing and verification requirements while the CLI remains the current source of command guidance.

## Load this skill when

- A frontend or full-stack change must be verified through the interface an end user sees.

- The task requires clicking, typing, navigation, authentication, responsive layout checks, or other browser interaction.

- The task involves browser console errors, failed network requests, DOM state, screenshots, Lighthouse, or performance debugging.

- The user explicitly asks for Chrome testing, E2E testing, browser automation, Chrome DevTools, or `chrome-devtools-axi`.

## Do not load this skill when

- A simple HTTP request, API call, or static source inspection completely answers the task.

- The user requested analysis only and did not authorize running the application or interacting with an external environment.

## Workflow

1. Reproduce a bug through the closest available end-user flow before changing code.

2. Run `command -v chrome-devtools-axi` and stop with a clear setup error if the installed command is unavailable.

3. Run `chrome-devtools-axi --help` and the relevant command help before testing so the installed CLI remains the command source of truth.

4. Start the application through its documented development or test command and open its real URL in Chrome.

5. Take an initial snapshot, perform the user flow, and verify visible state after every material interaction.

6. Inspect the browser console and network activity for errors, failed requests, incorrect payloads, and unexpected redirects.

7. Test every relevant desktop and mobile viewport and capture a screenshot when visual behavior or evidence matters.

8. Treat clipping, overlap, broken spacing, unreadable text, missing states, and inconsistent responsive behavior as failures rather than cosmetic noise.

9. Re-run the complete affected flow after a fix and report the tested URL, viewport, actions, console result, network result, and screenshot path.

10. Stop only the Chrome DevTools AXI session started for the current task and leave unrelated browser sessions untouched.

Prefer the installed `chrome-devtools-axi` command and do not download another copy with `npx -y` when that command is available.
