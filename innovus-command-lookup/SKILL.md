---
name: innovus-command-lookup
description: Look up Cadence Innovus command usage from a local Innovus Text Command Reference, especially when the user asks how to use Innovus commands, options, examples, command order, or related PnR flow commands. This is a pure command lookup skill — syntax, options, and usage examples only, not for diagnosing concrete errors or design problems (use digital-ic-backend-debug for those). Use when files such as innovus_manual.txt, innovus命令手册.pdf, or docs/innovus_flow_commands are available or when the user asks to search the Innovus command manual.
---

# Innovus Command Lookup

## Workflow

1. Confirm the working directory and locate the manual assets.
   - Prefer `innovus_manual.txt` for exact command extraction.
   - Use `docs/innovus_flow_commands/*.md` for flow context and practical grouping.
   - Treat the PDF as source of truth only when text extraction or Markdown notes are insufficient.

2. For each requested command, first search exact matches.
   - Run `rg -n "^commandName$|commandName" innovus_manual.txt docs/innovus_flow_commands` from the project directory.
   - If a command name is ambiguous or misspelled, show likely candidates and ask only if guessing would be risky.

3. Extract the command entry.
   - If the repo has `tools/extract_innovus_command.py`, use it:

```powershell
python tools\extract_innovus_command.py innovus_manual.txt <command>
```

   - Otherwise use this skill's helper:

```powershell
python C:\Users\CYL04\.codex\skills\innovus-command-lookup\scripts\lookup_innovus_command.py . <command>
```

4. Read the relevant flow note when available.
   - `01_design_setup_and_data_io.md`: init, import/export, LEF/DEF/netlist, save/restore.
   - `02_floorplan_and_partition.md`: floorplan, regions, blockages, PG pins, partitions.
   - `03_power_planning_and_pg_routing.md`: global nets, rings, stripes, sroute, low power.
   - `04_placement_and_prects_opt.md`: placement, filler/endcap/tap, scan reorder, pre-CTS opt.
   - `05_cts_and_clock_optimization.md`: CCOpt/CTS, skew groups, route types.
   - `06_routing_and_postroute_opt.md`: NanoRoute, routeDesign, post-route opt.
   - `07_rc_timing_signoff_and_verification.md`: RC, timing, signoff, verification.
   - `08_eco.md`: ECO placement/routing/netlist edits.
   - `09_non_flow_domains_and_utilities.md`: GUI, general utilities, rail, fill, mixed signal.
   - `10_common_commands_detailed_options.md`: common option quick reference.

## Answer Format

Summarize in Chinese unless the user asks otherwise. Keep the answer practical:

- 命令作用
- 基本语法
- 关键参数
- 常用写法
- 使用阶段 / 前置条件
- 注意事项 / 容易踩坑
- 相关命令

For several commands, use one compact section per command and finish with a short suggested command sequence when useful.

## Rules

- Prefer the local manual over memory.
- Do not paste long copyrighted manual passages. Quote only short fragments when necessary, and otherwise paraphrase.
- Mention the source file used, such as `innovus_manual.txt` or a file under `docs/innovus_flow_commands`.
- Preserve exact option names and Tcl command spelling.
- If default values matter, verify them from the extracted manual entry.
- If a command is version-sensitive, state that the available local manual is Innovus Text Command Reference 17.11.
