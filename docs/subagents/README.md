# Geo-lab Subagent Runbook

This folder contains a concrete parallel execution packet for Codex app.

## Why this is structured this way

The current repository is a dirty worktree with many uncommitted changes. That makes immediate `git worktree` fan-out risky, because new worktrees would start from the last commit and miss the current state.

For the current sprint, use:

- the same workspace
- one agent per file ownership zone
- one integrator agent at the end

After the current state is committed cleanly, you can move to separate branches/worktrees.

## Agent roster

1. `01_qa_baseline.md`
2. `02_product_shell.md`
3. `03_lab_education.md`
4. `04_research_workflow.md`
5. `05_integrator.md`

## Launch order

1. Start the `QA Baseline` agent first.
2. Start `Product Shell`, `Lab Education`, and `Research Workflow` in parallel.
3. Start `Integrator` only after the other three agents have produced results.

## Hard ownership boundaries

### QA Baseline
- Owns `tests/`
- Owns `tests/e2e/`
- Owns `playwright.config.js`
- Owns `run_geo_lab.ps1`
- May patch app files only if a test-blocking bug cannot be isolated elsewhere

### Product Shell
- Owns `app/home_view.py`
- Owns `pages/1_📖_Gallery.py`
- Owns `pages/2_🗺️_Overview.py`
- Owns `assets/style.css`
- Must not modify `pages/3_🧪_Lab.py`
- Must not modify `pages/4_🔬_Research.py`

### Lab Education
- Owns `pages/3_🧪_Lab.py`
- Owns `app/utils/lab_model.py`
- Owns `app/utils/mode_helpers.py`
- Owns Lab-related code in `app/components/animation_renderer.py`
- Must not modify `pages/1_📖_Gallery.py`
- Must not modify `pages/4_🔬_Research.py`

### Research Workflow
- Owns `pages/4_🔬_Research.py`
- Owns `app/utils/research_compare.py`
- Owns `engine/analysis.py`
- May use `engine/dem_io.py` if required
- Must not modify `pages/1_📖_Gallery.py`
- Must not modify `pages/3_🧪_Lab.py`

### Integrator
- Merges results
- Resolves collisions
- Runs full verification

## Shared success criteria

- Teacher can reach a usable example flow quickly.
- Student can understand a landform change sequence without external explanation.
- Research user can compare DEMs, interpret the result, and export a usable summary.
- No known `session_state` or widget timing regressions are introduced.

## Standard verification

### Python tests

```powershell
C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".\.venv\Scripts\python.exe -m pytest -q tests"
```

### Playwright example

```powershell
cmd /c npx playwright test tests/e2e/gallery_showcase.spec.js --config=playwright.config.js --project=chromium
```

## Reporting format for each agent

Each agent should report in this order:

1. What changed
2. Files touched
3. Verification run
4. Remaining risk
