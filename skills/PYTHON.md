---
name: python-tools
description: Apply TuLN's Python runtime and dependency policy before using Python or changing Python dependencies on macOS, Windows, WSL2, or Linux.
---

# Global Python Policy

Determine the active operating system, shell, project environment, and interpreter before running Python or managing dependencies.

## macOS, WSL2, and Linux

Use an existing project environment when the project defines one.

For the setup utility in this repository, use a native `python3` interpreter version 3.10 or newer and the Python standard library only.

On macOS, use the existing project environment when available, or a Homebrew Python when the system interpreter is too old.

Do not call a Windows Python interpreter through `/mnt/c`, `/mnt/u`, or another mounted Windows drive for a WSL2 workflow.

Do not install packages into the system Python.

Do not use `pip install --user`.

If a project genuinely requires dependencies, inspect its documented environment and package manager before installing anything.

Do not create a new virtual environment when a suitable project environment already exists.

## Native Windows

The default shell is CMD unless another shell is confirmed.

Use this Python environment by default:

```text
U:\runtime\python\.venv
```

Use this interpreter:

```text
U:\runtime\python\.venv\Scripts\python.exe
```

Before any `pip install`, `pip uninstall`, or `pip upgrade`, verify that this environment or the repository-designated environment is active.

Prefer commands in this form:

```text
U:\runtime\python\.venv\Scripts\python.exe -m pip ...
```

Use CMD commands such as `dir` and `where` unless another shell is confirmed.

## Rules for every environment

- Never install packages into global or system Python.
- Check whether a dependency is already installed before adding it.
- Prefer Python standard library and existing dependencies.
- Reuse the repository-designated environment.
- Do not mass-upgrade packages.
- Do not automatically download large packages, browsers, AI models, CUDA, Torch, TensorFlow, or similar artifacts.
- Any download over approximately 100 MB requires user approval.
- For Playwright, install only the required browser.
- Minimize disk usage, caches, duplicate environments, models, and dependencies.
