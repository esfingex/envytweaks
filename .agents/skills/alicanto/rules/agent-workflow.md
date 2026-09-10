# Agent Workflow Guidelines for [Project Name]

This workspace requires a strict local-first, python-centric development lifecycle. Any AI agent working on this repository **MUST** adhere to the following workflow rules.

---

## 1. Phase 1: Query CaveMem Before Coding
Before proposing any code modification, refactoring, or bug fix, you **MUST** run a semantic query in CaveMem to retrieve existing project gotchas, conventions, and context:
```bash
rtk cavemem query "<task keywords or error messages>"
```

---

## 2. Phase 2: Follow the GSD Wave Planning Pattern
We track all feature sets and refactoring waves inside the `.planning/` folder:
1. **Start a Wave**: Start a new development phase before writing code:
   ```bash
   rtk forge wave-start "<wave_name_objective>"
   ```
2. **Define Tasks**: Edit the generated `.planning/waves/wave_XXX_<safe_name>.md` file to list the wave's objective, task list checklist, and verification checklist.
3. **Keep Planning Up to Date**: Update `.planning/PROJECT.md`, `ROADMAP.md`, `STATE.md`, and `continue-here.md` as milestones progress.
4. **Close a Wave**: When you complete the task list and verification plans:
   ```bash
   rtk forge wave-close
   ```
   This runs local validation tests, audits tasks, extracts Architecture Decision Records (ADRs) to `STATE.md`, and commits changes to Git.

---

## 3. Phase 3: Python-Centric Playwright Testing
We avoid Node.js for browser automation, prioritizing Python and `unittest` + `playwright`.
* **Playwright Launch**: In test suites, support multiple browsers using the `BROWSER` env var. For Vivaldi, launch it as a CDP subprocess on port 9222:
  ```python
  # In tests/test_ui.py
  # Connects over CDP if BROWSER=vivaldi, otherwise launches Chromium/Chrome/Firefox/WebKit
  ```
* **Execution**: Execute browser tests inside the project virtual environment `.venv`:
  ```bash
  BROWSER=vivaldi HEADLESS=true ./.venv/bin/python3 -m unittest discover -s tests
  ```

---

## 4. Phase 4: Save to CaveMem (Bilingual Caveman Format - BCF)
Upon resolving a gotcha, establishing a convention, or completing a wave, you **MUST** document it in the project's CaveMem database.
* **Format**:
  - **`[EN]`**: Highly compressed English in "caveman" style (omitting articles, pronouns, auxiliaries) to save LLM context tokens.
  - **`[ES]`**: Full natural Spanish for developer quick reference and the web panel.
* **Categories**: `gotcha`, `rule`, `flow`, `config`, `dependency`.
* **Command**:
  ```bash
  rtk cavemem add <category> "[EN] compressed english fact... [ES] descripción en español..." -t "[Project Name],<tags>"
  ```

---

## 5. RTK (Rust Token Killer) Prefix
To prevent token bloat, **ALL** system execution commands run in the terminal **MUST** be prefixed with `rtk` (unless running interactive binaries or virtual environment activation):
```bash
rtk git status
```
```bash
rtk git diff
```
```bash
rtk cavemem query ...
```
