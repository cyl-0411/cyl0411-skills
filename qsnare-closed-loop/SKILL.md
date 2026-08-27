---
name: qsnare-closed-loop
description: Run Q-SNARE/Q-Whisperer evaluation through metrics, QEC simulation, PyMatching decoding, feedback, cleanup, and git handoff. Use for closed-loop LER validation or iteration acceptance.
---

# Q-SNARE Closed Loop

## Overview

Use the actual QEC decoding outcome as the primary success signal. Classification AP/F1 is useful for diagnosis, but a model is only effective when model-adjusted PyMatching improves logical error rate versus raw PyMatching.

## Workflow

1. Inspect the current state before running anything expensive:
   - `git status --short`
   - latest `model/figures/experiment_comparison.csv`
   - latest `model/figures/<experiment>/baseline_comparison.json`
   - latest `model/figures/<experiment>/selective_operating_point*.json`
   - latest `simulation/results/**/feedback.json`, `summary.json`, `gated_validation_summary.csv`, or `gated_validation_summary.md`

2. Run commands from the Q-Whisperer repository root. Resolve `<QSNARE_PYTHON>`
   once: prefer `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on
   POSIX, and require `"<QSNARE_PYTHON>" -X utf8 -c "import torch, stim, pymatching"`
   to pass. Do not fall back to an unrelated system Python. For the current
   accepted baseline, prefer the runtime-gated validation CLI:

```powershell
"<QSNARE_PYTHON>" -X utf8 -m simulation.run_gated_policy_validation `
  --policy-manifest simulation/policies/runtime_gated_v2.yaml `
  --policy-mode gated `
  --instances 2 `
  --shots-per-instance 100 `
  --device auto
```

3. Scale accepted-policy validation only after the smoke test passes:
   - Single-seed 100k: add `--seed 7101 --instances 100 --shots-per-instance 1000 --output-root simulation/results/gated_policy_validation_full`.
   - The manifest defines scenarios `x50`, `x100`, `x300`, `x1000`, and `x50-x1000`; keep paired raw-versus-adjusted samples.
   - Use `"<QSNARE_PYTHON>" -X utf8 -m simulation.run_closed_loop_workflow` only for historical or experimental single-model scans.

4. Treat the repository's `simulation/` package as QEC-SIM unless the user provides an external simulator path. It uses Stim for detector sampling and PyMatching for decoding.

## Success Criteria

- Primary: `LER(noisy_model_adjusted_pm) < LER(noisy_raw_pm)`.
- Strong success: model-adjusted LER improves raw PM by at least 10% and the difference is larger than about two combined standard errors.
- "Correctness improves" means logical success rate increases; report both success rate and LER, but make LER the decision metric.
- If AP/F1 is high but QEC LER regresses, do not call the model good. Tune policy mapping, action threshold, and decoder hotspot multiplier first.

## Resource Policy

- Use GPU for training and model inference when CUDA is available.
- Use CPU workers conservatively for data loading and simulation orchestration; do not saturate all cores by default.
- Keep GPU memory headroom. If CUDA OOM occurs, reduce batch size and retry before changing model code.
- For large QEC runs, increase `instances` and `shots-per-instance` gradually. Avoid holding all detector samples in memory.

## Logs and Artifacts

- Prefer structured small artifacts: `feedback.json`, `feedback.md`, `summary.json`, `instances.csv`.
- Compress workflow logs to `run.log.gz` and delete raw `run.log`.
- Keep only recent workflow run directories for the same experiment unless the user asks to preserve a run.
- Do not delete historical training logs or checkpoints unless the user explicitly requests cleanup or passes a cleanup flag.

## Git Handoff

- Commit code changes after tests pass.
- Push model-iteration results only when the closed-loop QEC result meets the strong success criterion.
- Stage only files related to the current workflow; avoid mixing unrelated dirty worktree changes into the commit.
