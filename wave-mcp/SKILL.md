---
name: wave-mcp
description: Debug Verilog/SystemVerilog designs with the wave-mcp MCP server using FST/VCD waveform queries, RTL hierarchy and connectivity analysis, driver/fan-in inspection, value tracing, and X-state root-cause tracing. Use for RTL waveform debugging, pre-simulation static analysis, or diagnosing a failing simulation. Do not use for analog waveforms or FSDB-only inputs.
metadata:
  version: "0.1.0"
  upstream: "Tencent/wave-mcp@0.1.1"
---

# Wave MCP

Use the `wave-mcp` MCP server as the analysis backend. It runs in the `IC-EDA`
WSL distribution and sees Linux paths, even when Codex itself is running on
Windows.

## Availability and paths

- Confirm the `wave-mcp` MCP tools are available before beginning. If they are
  missing immediately after installation, ask the user to restart Codex; do not
  pretend to have queried a waveform. For repair or upgrade work, read
  [references/setup.md](references/setup.md).
- Convert Windows paths such as `E:\project\dump.fst` to WSL paths such as
  `/mnt/e/project/dump.fst` before passing them to MCP tools. Use `wslpath -a`
  when the mapping is not obvious.
- Audit filelists before use. Resolve relative entries from the same base used
  by the simulator, follow nested `-f`/`-F` entries, and translate Windows
  absolute paths inside filelists and `+incdir+` options. Never rewrite the
  user's original filelist merely to make it work in WSL. If normalization is
  needed, create a derived copy under the session `out_dir` and report it.
- Keep generated session data in a scoped project directory, normally
  `<project>/.wave-mcp/sessions/<name>`, unless the user specifies another
  location. Reuse the same `out_dir` when upgrading a static session with a
  waveform.

## Choose the session type

- With RTL but no waveform, call `open_static_session`. Hierarchy, declarations,
  connectivity, drivers, loads, and fan-in/fan-out remain available.
- With `.fst` or `.vcd`, call `prepare_session`. Pass the same top, filelist,
  include directories, and defines used by the simulator. FST is read directly;
  VCD requires `vcd2fst` and is converted first.
- FSDB is not supported. Ask for FST/VCD output or an explicit conversion path.
- wave-mcp consumes simulation results; it does not compile RTL or run a
  simulator. Do not start a separate simulation unless the user requests it.

Treat a top inferred from a signal path as a candidate until hierarchy and
session metadata confirm it. When compile defines, include directories, or
filelist semantics are unavailable, ask for them or limit the result to FST
observations.

After opening a session, inspect `session_info`, waveform time range/timescale,
`netlist_health`, and definition coverage. Value queries can still be reliable
when netlist elaboration is degraded, but driver, connectivity, and trace
conclusions require a healthy netlist. Report missing compilation inputs first.
Create a derived session configuration when possible; modify project files only
with explicit user authorization.

## Analysis workflow

Start narrow and follow evidence:

1. Establish the failing assertion, output, expected value, and relevant time
   window. Read the waveform timescale and range, convert the user's time unit
   to the tool's accepted representation, and record that conversion. Inspect a
   window spanning the event and several relevant clock cycles when known.
2. Use hierarchy and signal discovery tools to resolve exact full paths rather
   than guessing names.
3. Query the failing signal at the event and in a small surrounding range.
4. Inspect static drivers and contributors. Use active-driver analysis when a
   waveform and healthy netlist are available.
5. Use `trace_value` for an incorrect known value or `trace_x` for an X state,
   then inspect the reported RTL locations and control conditions.
6. Correlate the result with nearby clocks, resets, enables, handshakes, state,
   and data signals. Expand the time window only when the local evidence is
   insufficient.

Prefer bounded queries (`signal_value_at` or `signal_values_in_range`) over
dumping an entire long waveform. Summarize the causal chain with exact signal
paths, times, values, and source locations.

## Evidence limits

- `trace_x` is approximate; verify its candidate root cause against drivers,
  guards, and values before calling it definitive.
- Distinguish an FST observation from a static-netlist inference.
- Report degraded elaboration, missing waveform data, truncated queries, or
  unresolved hierarchy explicitly.
- Do not claim that absence from a limited time window proves a signal never
  changed.

Upstream documentation: https://github.com/Tencent/wave-mcp
