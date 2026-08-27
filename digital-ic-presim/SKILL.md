---
name: digital-ic-presim
description: Build, run, and review reproducible RTL pre-simulation testbenches, logs, and waveforms for Verilog/SystemVerilog, SoC/IP smoke tests, or VCS/WSL flows; use wave-mcp for focused FST/VCD signal tracing.
---

# Digital IC Pre-Simulation

## Quick Start

1. Identify the DUT, the interface under test, and the smallest hierarchy that covers the real logic path.
2. Read the RTL before writing the test: ports, reset polarity, clocks, config macros, CDCs, hard-coded includes, and existing wrappers.
3. Define pass/fail criteria before coding the TB. Prefer self-checking tests with `[PASS]` and `[FAIL]` logs.
4. Build a focused TB with explicit clocks/resets, protocol tasks, timeout protection, FSDB dumping when needed, and a summary file.
5. Run compile and sim from the intended EDA environment, then report logs, waveform path, checks passed, checks failed, and next debug signals.

## RTL Inspection Checklist

- Confirm clock domains, reset polarity, reset synchronizers, scan/test-mode pins, and pad wrappers.
- Trace the tested signal path through wrappers until it reaches the implementation module.
- Check all `include` paths and macros. If RTL has machine-specific absolute includes, use a generated simulation mirror or symlink instead of editing source RTL.
- List only the files required for the target smoke test before broadening to full-SoC simulation.
- Note tie-offs in wrappers, especially JTAG TRST, boot-mode pins, QSPI/UART pins, AXI ready/valid defaults, and test-mode overrides.

## Testbench Rules

- Keep TB readable: one task per protocol action, named localparams for opcodes/addresses/expected values, and no unexplained magic numbers.
- Drive clocks and resets explicitly. Release reset only after all passive inputs have known values.
- Encode protocol transactions LSB/MSB order exactly as the RTL expects, and comment non-obvious sampling edges.
- Every test must have a global timeout and transaction-level timeout where a handshake can hang.
- Check for X/Z before comparing important observed values.
- Use `$fatal` on checker failures so CI or scripts return nonzero.
- Log all checks as `[PASS] name` or `[FAIL] name: got=... expected=...`.

## Simulation Directory Layout

- For each DUT or interface-level simulation, create a dedicated directory under `sim/<dut>/`.
- Use lowercase, stable DUT names, for example `sim/jtag/`, `sim/uart/`, `sim/axi_full2lite/`, or `sim/e203_debug/`.
- Match the existing `sim/jtag/` structure unless the user asks otherwise:

```text
sim/<dut>/
  Makefile
  README.md
  filelist.f
  tb_<dut>_smoke.sv
  out/                  # generated logs, build output, FSDB
```

- Put DUT-specific TBs, filelists, and run automation in `sim/<dut>/`; do not place one-off scripts in the repo root.
- Keep generated artifacts under `sim/<dut>/out/`; clean tool scratch directories such as `csrc/` and `ucli.key` from the same Makefile.
- Standard Makefile targets should be only `clean`, `compile`, `run`, and `wave` unless the user asks for more.
- Keep Makefiles and TB code concise: prefer clear variables, short helper blocks, and no redundant targets.
- Prefer FSDB for Verdi waveform review. Use `make -C sim/<dut> compile` for RTL compile-only checks, `make -C sim/<dut> run` for simulation plus FSDB generation, and `make -C sim/<dut> wave` for Verdi source/waveform review.

## VCS/WSL Flow

- Resolve both the project root and WSL distribution at runtime. Never reuse a
  personal `/mnt/c/Users/...` path from an example. Use an explicit distro from
  task context or `IC_EDA_WSL_DISTRO`; if neither exists, stop and list the
  available distros instead of assuming a username, drive, or distro. Translate
  the actual Windows path with `wslpath`, then use WSL's `--cd`/`--exec` arguments
  so spaces in either path do not pass through a shell command string:

```powershell
$projectRoot = (Resolve-Path -LiteralPath '<PROJECT_ROOT>').Path
$wslDistro = if ($env:IC_EDA_WSL_DISTRO) { $env:IC_EDA_WSL_DISTRO } else { '<WSL_DISTRO>' }
if ($wslDistro -eq '<WSL_DISTRO>') { throw 'Set IC_EDA_WSL_DISTRO or supply the task distro.' }
wsl.exe --distribution $wslDistro --exec true
if ($LASTEXITCODE -ne 0) {
    wsl.exe --list --quiet
    throw "WSL distro is unavailable: $wslDistro"
}
$wslInput = $projectRoot.Replace('\', '\\') # survive wsl.exe argument parsing
$wslRoot = (wsl.exe --distribution $wslDistro -- wslpath -a -- $wslInput).Trim()
if (-not $wslRoot) { throw "wslpath could not translate: $projectRoot" }
wsl.exe --distribution $wslDistro --cd $wslRoot --exec make -C 'sim/<dut>' compile
```

The same resolved `$wslDistro` and `$wslRoot` must be reused for `run` and
`wave`; do not resolve them independently in later commands.

- Standard Makefile behavior:
  - `make -C sim/<dut> compile` checks/activates license, compiles RTL/TB, and prepares Verdi source data.
  - `make -C sim/<dut> run` runs simulation and writes FSDB.
  - `make -C sim/<dut> wave` opens the existing FSDB in Verdi with source loaded.
  - `OUT_DIR=...` selects the output directory.
  - Save `compile.log`, `sim.log`, `summary.txt`, generated filelist, and FSDB under the output directory.

## Result Review

- First report whether compile passed, sim passed, and how many self-checks passed.
- If failed, include the failing checker, actual/expected values, last transaction, and the smallest waveform scope to inspect next.
- Preserve generated artifacts under `sim/.../out/` or another ignored output directory; do not modify golden RTL to make a simulation compile unless the user explicitly asks for a source fix.
