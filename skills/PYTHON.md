# Global Python Policy

OS: Windows
Default shell: CMD

Use this Python environment by default:

```text
U:\runtime\python\.venv
```

Preferred interpreter:

```text
U:\runtime\python\.venv\Scripts\python.exe
```

Rules:

* Never install packages into global/system Python.
* Before `pip install/uninstall/upgrade`, verify the active Python environment.
* Prefer:
  `U:\runtime\python\.venv\Scripts\python.exe -m pip ...`
* Reuse the existing `.venv`; do not create new environments unless required.
* Before installing anything, check if it is already installed.
* Prefer standard library and existing packages.
* Do not mass-upgrade packages.
* Do not use `pip install --user`.
* Do not automatically download large packages, browsers, AI models, CUDA, Torch, TensorFlow, etc.
* Any download over ~100 MB requires my approval.
* For Playwright, install only the required browser, not all browsers.
* Minimize disk usage, caches, duplicate environments, models, and dependencies.
* Use CMD commands (`dir`, `where`) instead of Linux commands unless another shell is confirmed.
