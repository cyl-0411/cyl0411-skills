# Tag Routing

Use this file to choose search filters and query expansions for digital backend debug. Treat these as hints, not fixed taxonomy.

## Tool Tags

| User signal | Add tags or filters |
| --- | --- |
| Innovus, encounter, dbGet, ccopt, NanoRoute | `innovus`, `Tool-Usage`, likely `PnR` |
| ICC2, ICC, Fusion Compiler | `icc2`, `Tool-Usage`, likely `PnR` |
| PrimeTime, PT, DMSA, timing ECO | `primetime`, `timing`, `STA`, `sta-signoff` |
| StarRC, SPEF, QRC, extraction | `starrc`, `Extraction`, `extraction` |
| Calibre, DRC, LVS, RVE, SVRF | `calibre`, `physical-verification`, `DRC`, `LVS` |
| RedHawk, IR drop, EM, ploc, APL | `redhawk`, `ir-em`, `IR-EM`, `Power` |
| Tempus | `tempus`, `timing`, `STA` |

## Symptom To Search Hints

| Symptom | Query additions |
| --- | --- |
| setup violation | `setup`, `timing`, `sta-signoff`, `PrimeTime`, `group path` |
| hold violation | `hold`, `timing`, `lockup`, `DMSA`, `ECO` |
| transition violation | `max transition`, `DRV`, `driver`, `upsize`, `buffer` |
| postCTS timing worse | `postCTS`, `CTS`, `clock skew`, `latency`, `clock-tree` |
| no clock tree or CTS failed | `CTS`, `ccopt`, `IMPCCOPT`, `clock tree`, `sink type` |
| route short/open | `route`, `short`, `ecoRoute`, `Calibre`, `DRC`, `physical-verification` |
| DRC rule | Exact rule code plus `Calibre DRC`, `DRC修复`, relevant layer/via |
| LVS mismatch/open/short | `LVS`, `Calibre`, `v2lvs`, `netlist`, `hcell` |
| congestion/hotspot | `congestion`, `placement`, `route`, `overflow`, `hotspot` |
| IR drop/EM | `RedHawk`, `IR drop`, `dynamic`, `static`, `ploc`, `power network` |
| PG floating/no power | `PG pin`, `floating`, `derive pg`, `globalNetConnect`, `RedHawk` |
| ECO after timing/route | `ECO`, `ecoRoute`, `post-mask`, `freeze layer`, `spare cell` |
| script/Tcl problem | `tcl`, command name, tool tag |

## Flow Stage Tags

Use these with `--flow-stage` when known:

- `design-import`
- `floorplan`
- `powerplan`
- `placement`
- `cts`
- `route`
- `chipfinish`
- `extraction`
- `sta-signoff`
- `physical-verification`
- `eco`
- `tool-scripting`
- `lab-flow`
- `low-power`
- `formal`
- `general`

## Knowledge Area Tags

Use these with `--knowledge-area` when known:

- `Clock`
- `DRC`
- `ECO`
- `Extraction`
- `Formal`
- `IR-EM`
- `LEF-DEF-GDS`
- `Liberty`
- `LVS`
- `PnR`
- `Power`
- `Reference`
- `SDC`
- `STA`
- `Tcl-Scripting`
- `Tool-Usage`
- `UPF`
- `Interview`
