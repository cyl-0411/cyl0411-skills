# QEC Screening

Use this reference to identify quantum and QEC-related papers for simulator or decoder architecture research.

## Keyword Tiers

Core QEC:

- `quantum error correction`
- `QEC`
- `surface code`
- `qLDPC`
- `fault-tolerant quantum`
- `syndrome`
- `decoder`
- `logical error rate`

Adjacent but useful:

- `quantum circuit simulation`
- `quantum routing`
- `oracle synthesis`
- `measurement of quantum circuits`
- `single-flux quantum`
- `trapped-ion quantum`
- `cryogenic control`

Non-core quantum:

- quantum-inspired optimization
- quantum device modeling without error correction
- circuit synthesis without fault-tolerance or syndrome processing

## Relevance Labels

Use these labels in reports:

- `QEC-core`: directly about QEC decoding, syndrome processing, fault-tolerant architecture, resource estimation, or QEC simulation.
- `QEC-adjacent`: useful for compiler, routing, control hardware, or quantum circuit simulation, but not a decoder/simulator paper.
- `Quantum-non-QEC`: quantum paper with limited direct value for QEC simulator design.
- `Not-quantum`: false positive.

## Report Fields

For each candidate, include:

- paper ID and title
- DOI
- full-text status
- one-paragraph content summary
- innovation point
- comparison with similar work
- value for QEC simulator design

Mark missing full text explicitly as `未获取全文，仅基于摘要/元数据总结`.

## Simulator-Oriented Analysis

When the user's target is a QEC decoder or architecture simulator, emphasize:

- syndrome stream format and timing assumptions
- decoder latency and throughput
- code family and distance scalability
- noise model and logical error metric
- hardware resource model
- integration point for decoder plugins
- whether the paper can serve as a system-level benchmark
