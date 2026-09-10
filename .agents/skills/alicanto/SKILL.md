---
name: alicanto
description: >
  Developer workflow skill for Alicanto AI Tools (alicanto) integrating GSD (Get Shit Done) Core.
  Auto-activates CaveMem memory management, GSD Spec-Driven planning (.planning/),
  Supply-Chain Package Gate, Context Rot monitoring, and forge CLI integration.
  Triggers automatically when working in any directory under /home/esfingex/workspace/
  or /home/esfingex/Github/ or when user mentions CaveMem, forge, RTK, or alicanto.
---

# alicanto — GSD-Enabled AI Developer Workflow & Automation

This skill establishes the mandatory development workflow, planning standards, and safety gates for all projects connected to the Alicanto AI Tools suite.

---

## GSD SPEC-DRIVEN PLANNING WORKFLOW (.planning/)

Every project connected via `forge` maintains its lifecycle and roadmap inside the `.planning/` directory using these four files:
- **`PROJECT.md`**: Definitive system architecture, folder layouts, and global constants.
- **`ROADMAP.md`**: Project phases numbered sequentially (e.g., Phase 1.0, 1.1) with milestone-level checklists.
- **`STATE.md`**: Registry of Architecture Decision Records (ADRs), active blockers, and active phase status.
- **`continue-here.md`**: Precise handoff note for context continuation.

### Wave Execution Protocol:
1. **Start Wave (`wave-start`)**: Before modifying any code, start a new wave specifying the atomic objectives:
   ```bash
   rtk forge wave-start "<wave_name>"
   ```
   This creates a spec template under `.planning/waves/wave_XXX_<name>.md`. You must list the requirements, task checklist, and verification plan there before writing any code.
2. **Close Wave (`wave-close`)**: Once all tasks in the wave spec are complete:
   ```bash
   rtk forge wave-close
   ```
   This will automatically trigger the project's test suite, import draft ADRs from the wave spec into `STATE.md`, stage all modifications, and create a git commit using the Conventional Commits specification.

---
## SUPPLY-CHAIN LEGITIMACY GATE (Anti-Hallucination)

To protect the system against hallucinated or malicious packages (slopsquatting):
- **Verification Rule**: Before proposing or executing any package installation or dependency addition command, you **MUST** run a legitimacy check using the package registry search/query command corresponding to the active project's language (e.g. `rtk npm view <package>` for Node.js, `rtk pip index versions <package>` for Python, `rtk cargo search <package>` for Rust, etc.).
- **Fallback [ASSUMED]**: If the package cannot be fully verified, flag it as `[ASSUMED]` in your plan and inject a mandatory human verification step (`checkpoint:human-verify`) before executing any terminal commands that install or execute it.

---

## CONTEXT ROT BARRIER (Context Window Management)

When working in long developer chats, context degradation (rot) can lead to code corruption or loss of requirements.
- **Monitoring**: Actively monitor the conversation size. If you detect that the context window is near saturation (e.g., more than 35 messages/turns or close to token limit limits):
  1. Run `rtk forge check-rot` to inspect active session steps count and get warnings.
  2. If warnings are present, **stop execution immediately**. Do not attempt new complex modifications.
  3. Write a detailed handoff note in `.planning/continue-here.md` summarizing the exact state, what files are dirty, and the next immediate step.
  4. Proactively ask the user to clear the session (e.g., using `/clear`) so the next model instance starts fresh and imports the context via `continue-here.md`.

---

## NO EMOJIS OR ICONS IN PLANNING DOCUMENTS

To optimize token efficiency and prevent visual noise/pollution in LLM context inputs:
- **Rule**: Do not write emojis, icons, or visual symbols in planning, roadmap, or state documents (`PROJECT.md`, `ROADMAP.md`, `STATE.md`, `continue-here.md`, and wave specs). Keep headers, lists, and text purely text-based, plain, and concise.

---

## CAVEMEM INTEGRATION (BCF & Search)

### Phase 1: Search Before Action
Before writing any code or proposing an implementation plan, you **MUST** perform a semantic search in the local project's CaveMem database to check for existing gotchas, conventions, or rules.
- **CLI Command**:
  ```bash
  rtk cavemem query "<search keywords or error message>"
  ```
- **REST API Endpoint** (silent background query):
  ```bash
  GET http://127.0.0.1:3000/api/search?project=<project_name>&q=<search_query>&limit=5
  ```

### Phase 2: Save on Resolution (Bilingual Caveman Format)
When you successfully solve a critical issue, bypass a compiler/runtime bug, or establish a key architectural decision, you **MUST** save this knowledge to the project's CaveMem database.
- **Entry Structure (BCF)**:
  - **`[EN]` Block**: Extremely compressed "caveman-style" English (no pronouns, auxiliary verbs, articles, or pleasantries) to minimize token consumption during future AI scans.
  - **`[ES]` Block**: Natural, clear, and complete Spanish for human reference and the local EJS dashboard interface.
- **CLI Command** (Always save via CLI):
  ```bash
  cavemem add <category> "[EN] <compressed english> [ES] <clear spanish>" -t "tag1,tag2"
  ```
  *Categories*: Default allowed categories are `gotcha`, `rule`, `flow`, `config`, `dependency`. Custom categories can be dynamically created per project from the Configuración dashboard tab and are persisted in the SQLite `categories` table.

---

## LOCAL MULTI-AGENT ORCHESTRATION (MoA Playground)

Projects can utilize the local Mixture-of-Agents (MoA) playground on the **Agentes MOA** dashboard tab.
- **Supervisor-Worker Loop**: Connects local models via Ollama to orchestrate subtask execution:
  1. **Supervisor**: Generates programming and testing subtasks.
  2. **Worker Programmer**: Implements code or layout.
  3. **Worker Tester**: Formulates unit tests and verification steps.
  4. **Architect**: Synthesizes and checks quality of final outputs.
- **Execution Endpoint**: Runs locally via `POST /api/orchestrator/run`.

---

## RTK (Rust Token Killer) — Mandatory Command Prefix

To minimize token usage and accelerate model response times, you **MUST** prefix all terminal/shell commands with `rtk`.
- **Correct**:
  ```bash
  rtk git status
  rtk find . -name "*.py"
  ```
- **Incorrect**:
  ```bash
  git status
  ```
*Exception: Interactive commands (e.g., launching GUI apps).*
