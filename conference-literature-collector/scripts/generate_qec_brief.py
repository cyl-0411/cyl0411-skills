from pathlib import Path
import csv, json

ROOT = Path(r'C:\Users\CYL04\Desktop\ASP_DAC_2026')
meta = json.loads((ROOT / 'metadata' / 'aspdac2026_papers.json').read_text(encoding='utf-8'))
related = json.loads((ROOT / 'metadata' / 'related_work.json').read_text(encoding='utf-8'))
download_rows = list(csv.DictReader((ROOT / 'logs' / 'download_report.csv').open(encoding='utf-8-sig')))
ieee_rows = list(csv.DictReader((ROOT / 'logs' / 'ieee_browser_download_report.csv').open(encoding='utf-8-sig')))

meta_by_id = {r['session_paper_id']: r for r in meta}
download_by_id = {r['session_paper_id']: r for r in download_rows if r['collection'] == 'aspdac2026'}
related_by_arxiv = {r['arxiv_id']: r for r in related}

main_ids = ['1D-1', '1D-2', '1D-3', '1D-4', '2C-4']
related_ids = [
    '2001.06598v1',
    '2108.06569v1',
    '2103.14209v1',
    '2208.05758v2',
    '2305.08307v1',
    '2603.22149v2',
    '2603.16203v1',
    '2605.09142v1',
]

main_notes = {
    '1D-1': {
        'summary': '摘要聚焦 CSS 码的容错态制备自动化。核心论点不是提出新解码器，而是把过去高度依赖人工构造的 logical-state initialization 变成可综合、可优化、可复用的 CAD 流。',
        'innovation': '把 fault-tolerant state preparation 作为设计自动化问题来做，并落到 MQT-QECC 工具链，直接服务于大码距 CSS/QEC 工作流。',
        'compare': '相比 1D-2/1D-3 这类“解码阶段”工作，1D-1 更靠前端，解决的是 logical state 生成而非 syndrome decoding；和 2C-4 的资源优化相比，它更接近 workload 生成器。',
        'sim': '对 simulator 的价值在于提供更真实的 logical-state initialization workload。若做端到端 FTQC 仿真，态制备延迟、门数和 ancilla 需求应被纳入前端输入模型。',
        'class': 'state preparation / CAD'
    },
    '1D-2': {
        'summary': '摘要抓住了一个很硬的系统约束：UF decoder 虽然低时延，但硬件效率往往不理想。论文的重点是通过通用硬件架构优化，让 UF 在可扩展性与资源开销之间更平衡。',
        'innovation': '把 Union-Find 从“算法可行”推进到“硬件上更可部署”，创新点在 pipeline、存储组织和面向大规模 topological code 的可扩展架构化实现。',
        'compare': '与 Fusion Blossom / Sparse Blossom 的 MWPM 路线相比，1D-2 明显偏低时延、较低复杂度；和 LILLIPUT 一样都走实时解码，但 1D-2 更强调通用可扩展架构而不是 LUT 近似。',
        'sim': '应作为 simulator 的一级 baseline。需要支持 UF decoder 的 latency、memory footprint、bandwidth 和 deadline miss 建模，并允许和 MWPM / neural decoder 做统一比较。',
        'class': 'decoder microarchitecture'
    },
    '1D-3': {
        'summary': '摘要强调 advanced QEC architectures 带来的解码复杂度上升，并把 RL 作为应对复杂 syndrome 结构与真实噪声特征的学习型策略。它的价值不在“更快硬件”，而在“更灵活的策略搜索”。',
        'innovation': '把 hybrid / multi-agent RL 引入 advanced QEC 与 qLDPC 解码，试图学习传统 hand-crafted decoder 不容易表达的决策策略。',
        'compare': '和 1D-2、DART-Q、低时延 GNN accelerator 这类系统/架构工作相比，1D-3 更偏 decoder policy；与 NEO-QEC 的神经增强思路相近，但 1D-3 更强调 RL 对复杂码结构的适应。',
        'sim': 'simulator 需要支持 learned decoder plugin、训练/推理分离、以及 accuracy-latency tradeoff。特别是 advanced QEC/qLDPC 场景里，不能只保留 surface-code decoder 接口。',
        'class': 'learned decoder'
    },
    '1D-4': {
        'summary': '摘要本质上在讨论 instruction set、硬件原语与 QEC 成本之间的耦合。它不是直接做 decoder，但指出 gate set 与控制抽象会反馈到 stabilizer measurement、qLDPC 远程交互和整体 FTQC 成本。',
        'innovation': '把 quantum ISA 与 QEC/architecture co-design 放到一个框架里讨论，尤其强调非常规 two-qubit instruction 对容错实现边界的影响。',
        'compare': '与 2C-4 这种只看 T-depth 的局部优化不同，1D-4 讨论的是更上层的 ISA 决策如何改变底层 QEC 代价；和 1D-1/1D-2 相比，它更像系统抽象层面的接口论文。',
        'sim': '对 simulator 的最大启发是：要把“workload 层门集”与“底层容错实现成本”连起来。不同 ISA 可能改变 syndrome 触发频率、远程交互密度与 magic-state 压力。',
        'class': 'ISA / system interface'
    },
    '2C-4': {
        'summary': '摘要把 T-depth reduction 直接和 magic-state distillation 开销挂钩。核心不是解码，而是通过搜索优化减少 fault-tolerant 工作负载的时空资源占用。',
        'innovation': '将 T-depth reduction 表述成搜索问题，并用遗传算法在非凸搜索空间中近似最优层合并模式。',
        'compare': '和 1D-2/1D-3 这种 decoder-centric 论文不同，2C-4 更接近“上游 workload shaping”。它与 1D-4 一样会影响 QEC 代价，但切入点是 compilation/resource optimization 而非 ISA。',
        'sim': '适合放进 simulator 的 workload preprocessing 层。若要评估 QEC 系统总成本，T-depth、T-count 和 magic-state demand 应与 decoder latency 一起进入端到端指标。',
        'class': 'FT workload optimization'
    },
}

related_notes = {
    '2001.06598v1': {
        'focus': 'decoder microarchitecture',
        'summary': '摘要直接把 decoder 放进 fault-tolerant control loop，看的是“错误累积前能否解完码”以及相应硬件资源。它是非常标准的实时 decoder 架构论文。',
        'innovation': '把 surface-code decoding 具体映射成可扩展微架构，强调 latency/resource 协同优化。',
        'compare': '与 1D-2 高度同类，可作为更早期的架构 baseline；1D-2 可以视为在更具体 UF decoder 路线上的 ASP-DAC 对应点。',
        'sim': '应作为 architecture-level baseline，尤其适合验证 queueing、memory 和 throughput 模型。',
        'class': 'decoder microarchitecture'
    },
    '2108.06569v1': {
        'focus': 'lookup-table decoder',
        'summary': '摘要抓住近端 QEC 的一个常见折中：软件 decoder 太慢、全精确硬件 decoder 太重，于是用 LUT 做低时延近似。',
        'innovation': '用 lightweight LUT decoder 把 feedback latency 压低到更接近可在线部署的水平。',
        'compare': '相比 MWPM/Fusion Blossom，LILLIPUT 更像近似、轻量、面向近期系统；和 1D-2 相比，1D-2 更偏可扩展硬件通路，LILLIPUT 更偏固定结构低时延。',
        'sim': '适合作为“低时延、低精度”角落点，帮助评估 accuracy-latency-frontier。',
        'class': 'low-latency decoder'
    },
    '2103.14209v1': {
        'focus': 'cryogenic / superconducting decoder',
        'summary': '摘要把 power budget 和 online decoding 放在一起讨论，目标是面向超导量子计算机的低功耗在线 QEC。',
        'innovation': '把 surface-code 在线纠错与 SFQ/superconducting hardware implementation 绑定，强调冷环境约束。',
        'compare': '和 1D-2 的常规数字硬件视角不同，QECOOL 更强调整个控制电子学部署环境；与 NEO-QEC 相比，它更偏规则化在线 decoder，而非 NN 增强。',
        'sim': '若 simulator 要服务 cryogenic 控制系统评估，需要把功耗、物理部署层级和 feedback path 纳入模型。',
        'class': 'online decoder system'
    },
    '2208.05758v2': {
        'focus': 'neural decoder enhancement',
        'summary': '摘要认为 practical QC 既要低时延也要高精度，因此提出 NN 增强的 online surface-code decoder。',
        'innovation': '把 neural enhancement 融入在线超导 decoder，使精度改进不脱离实时控制场景。',
        'compare': '和 1D-3 一样都属于 learned decoder 路线，但 NEO-QEC 更贴近 surface-code 在线部署；1D-3 则更偏 advanced QEC/qLDPC 的泛化。',
        'sim': '适合作为 learned decoder baseline，重点看 NN inference cost 与逻辑纠错收益的平衡。',
        'class': 'learned online decoder'
    },
    '2305.08307v1': {
        'focus': 'fast MWPM',
        'summary': '摘要的核心是让 MWPM 不再成为吞吐瓶颈，通过更接近线性的处理复杂度来追上硬件测量速率。',
        'innovation': '设计 fast/parallel blossom 变体，显著降低 MWPM 在 QEC 实际负载下的处理延迟。',
        'compare': '相比 Sparse Blossom 更强调并行工程实现；相比 1D-2 的 UF 路线，它代表高精度但更复杂的匹配派。',
        'sim': '必须作为高精度 decoder baseline 纳入，用于和 UF/LUT/NN 做统一延迟与正确率比较。',
        'class': 'high-accuracy decoder'
    },
    '2603.22149v2': {
        'focus': 'GNN accelerator',
        'summary': '摘要把 decoding bottleneck 直接交给 GNN accelerator 解决，目标是用专用硬件托住 learned decoder 的时延。',
        'innovation': '不是单纯提出 GNN decoder，而是为 QEC GNN inference 做低时延硬件加速器。',
        'compare': '和 NEO-QEC 一样都用学习方法，但这篇更偏 accelerator architecture；和 1D-3 相比，也更偏部署实现而不是 RL 策略本身。',
        'sim': 'simulator 应支持 learned decoder 的 hardware target，不然无法公平比较“算法准确率提升”与“推理时延开销”。',
        'class': 'learned decoder accelerator'
    },
    '2603.16203v1': {
        'focus': 'integrated QEC system',
        'summary': '摘要明确指出只看 decoder 不够，QEC 的最终表现取决于控制、通信、解码和它们的集成。',
        'innovation': '提供开源、全集成、sub-microsecond feedback latency 的系统级原型，把 decoder 放回完整工程栈。',
        'compare': '这是和“QEC simulator 设计”最贴近的一篇，因为它把 subsystem integration 放到第一位；比单一 decoder 论文更接近 end-to-end system benchmark。',
        'sim': '它几乎定义了 simulator 的目标轮廓：不仅要模拟 decoder，还要模拟 communication path、feedback deadline 和 subsystem composition。',
        'class': 'end-to-end QEC system'
    },
    '2605.09142v1': {
        'focus': 'deadline-aware qLDPC decoding',
        'summary': '摘要最有价值的地方是把 qLDPC decoding 从“能不能纠对”扩展到“能不能在 deadline 内纠对”。',
        'innovation': '把 arrival, queueing, service, completion 等系统概念显式引入 real-time qLDPC decoding。',
        'compare': '与 1D-3 都面向 advanced QEC / qLDPC，但 DART-Q 更系统、更工程；和 1D-2 相比，它不是单一 decoder 电路，而是 deadline-driven framework。',
        'sim': '这是 QEC simulator 里最该复刻的工作之一。需要显式建模队列、窗口、内存压力、miss deadline rate 与 logical error rate 的耦合。',
        'class': 'deadline-driven framework'
    },
}

matrix_rows = [
    ('1D-2', 'Union-Find decoder', 'decoder microarchitecture', 'latency/resource', 'direct baseline'),
    ('1D-3', 'RL-based decoder', 'algorithm / learned decoder', 'accuracy vs inference cost', 'advanced-code plug-in'),
    ('1D-4', 'Quantum ISA/QEC co-design', 'system interface', 'workload-to-QEC cost', 'front-end cost model'),
    ('2C-4', 'T-depth reduction', 'workload optimization', 'magic-state / FT overhead', 'preprocessing stage'),
    ('2001.06598v1', 'Surface-code decoder microarchitecture', 'decoder architecture', 'throughput/latency', 'architecture baseline'),
    ('2108.06569v1', 'LUT decoder', 'low-latency decoder', 'speed/accuracy tradeoff', 'fast approximate baseline'),
    ('2103.14209v1', 'QECOOL', 'online superconducting decoder', 'power + online feedback', 'cryogenic deployment model'),
    ('2208.05758v2', 'NEO-QEC', 'learned online decoder', 'accuracy + latency', 'NN decoder baseline'),
    ('2305.08307v1', 'Fusion Blossom', 'MWPM decoder', 'accuracy + throughput', 'high-accuracy baseline'),
    ('2603.22149v2', 'GNN accelerator', 'accelerator architecture', 'inference latency', 'learned hardware target'),
    ('2603.16203v1', 'Integrated QEC system', 'end-to-end system', 'subsystem integration', 'system benchmark anchor'),
    ('2605.09142v1', 'DART-Q', 'deadline-driven qLDPC framework', 'deadline/memory/load', 'queueing-aware simulator core'),
]

brief_path = ROOT / 'reports' / 'qec_paper_briefs.md'
summary_path = ROOT / 'reports' / 'SUMMARY.md'

lines = []
lines.append('# QEC Paper Briefs and Comparison')
lines.append('')
lines.append('## Summary')
lines.append('')
lines.append('- Scope: ASP-DAC 2026 mainline QEC/FTQC papers (`1D-1`, `1D-2`, `1D-3`, `1D-4`, `2C-4`) plus 8 closest decoder/simulator related works.')
lines.append('- Evidence policy: ASP-DAC entries are mainly based on official abstracts and downloaded IEEE PDFs when available; related works are based on arXiv abstracts and downloaded PDFs.')
lines.append('- Reading stance: this is a fast research brief for simulator design, so emphasis is on problem framing, innovation type, deployment assumptions, and comparison axes instead of full theorem/implementation reconstruction.')
lines.append('')
lines.append('## Corpus Status')
lines.append('')
lines.append('- ASP-DAC IEEE PDFs downloaded: 212/212')
lines.append('- Related-work open PDFs downloaded: 13/13')
lines.append('- Total PDFs in `papers/`: 227 (including 2 earlier open-access duplicates for ASP-DAC papers)')
lines.append('- Mainline QEC availability: `1D-2`, `1D-3`, `1D-4`, `2C-4` have local PDFs; `1D-1` remains abstract-only.')
lines.append('')
lines.append('## ASP-DAC Mainline Briefs')
lines.append('')

for sid in main_ids:
    r = meta_by_id[sid]
    d = download_by_id[sid]
    n = main_notes[sid]
    lines.append(f"### {sid} - {r['title']}")
    lines.append('')
    lines.append(f"- Status: `{d['download_status']}`{f" ({d['pdf_path']})" if d.get('pdf_path') else ''}")
    lines.append(f"- Category: {n['class']}")
    lines.append(f"- Abstract readout: {n['summary']}")
    lines.append(f"- Innovation: {n['innovation']}")
    lines.append(f"- Compared with similar work: {n['compare']}")
    lines.append(f"- Simulator takeaway: {n['sim']}")
    lines.append('')

lines.append('## Closest Related Work Briefs')
lines.append('')

for rid in related_ids:
    r = related_by_arxiv[rid]
    n = related_notes[rid]
    pdf_name = None
    for p in (ROOT / 'papers').glob(f"related__*{rid.split('v')[0].replace('.', '-')}*.pdf"):
        pdf_name = str(p.relative_to(ROOT)).replace('\\', '/')
        break
    lines.append(f"### {r['title']}")
    lines.append('')
    lines.append(f"- Source: `arXiv:{rid}`{f' ({pdf_name})' if pdf_name else ''}")
    lines.append(f"- Category: {n['class']}")
    lines.append(f"- Abstract readout: {n['summary']}")
    lines.append(f"- Innovation: {n['innovation']}")
    lines.append(f"- Compared with ASP-DAC anchors: {n['compare']}")
    lines.append(f"- Simulator takeaway: {n['sim']}")
    lines.append('')

lines.append('## Comparison Matrix')
lines.append('')
lines.append('| Work | Main method | Layer | Primary metric pressure | Best use in simulator |')
lines.append('|---|---|---|---|---|')
for key, method, layer, metric, use in matrix_rows:
    title = meta_by_id[key]['title'] if key in meta_by_id else related_by_arxiv[key]['title']
    short = key if key in meta_by_id else title
    lines.append(f'| {short} | {method} | {layer} | {metric} | {use} |')
lines.append('')
lines.append('## Innovation Themes and Same-Class Comparison')
lines.append('')
lines.append('- `1D-2` vs MWPM family (`Fusion Blossom`, `Sparse Blossom`): `1D-2` favors lower-latency and more hardware-friendly decoding, while MWPM variants usually buy higher decoding quality at the cost of more complicated data structures and matching logic.')
lines.append('- `1D-3` vs learned decoders (`NEO-QEC`, `Low Latency GNN Accelerator`): all three use learning, but `1D-3` is the most algorithm-policy oriented, `NEO-QEC` is online-surface-code oriented, and the GNN accelerator is deployment-architecture oriented.')
lines.append('- `1D-4` vs `2C-4`: both influence QEC cost indirectly. `1D-4` changes the system abstraction and gate semantics; `2C-4` reduces the FT workload after the abstraction is fixed.')
lines.append('- `2603.16203` vs `2605.09142`: both move beyond single-decoder benchmarking. The former is subsystem integration centric; the latter is queueing/deadline centric, especially important for qLDPC.')
lines.append('- `LILLIPUT` / `QECOOL` / `NEO-QEC`: these are valuable because they span an interpretable design triangle of low latency, cryogenic deployability, and learned enhancement.')
lines.append('')
lines.append('## What This Means for a QEC Simulator')
lines.append('')
lines.append('- The simulator should not stop at error-rate evaluation. It should model the full classical control loop: syndrome arrival, batching/windowing, decode service time, correction dispatch, and deadline misses.')
lines.append('- Decoder plug-ins should cover at least four families: `UF`, `MWPM`, `learned decoder`, and `qLDPC/deadline-aware framework`.')
lines.append('- Workload preprocessing matters. `1D-1`, `1D-4`, and `2C-4` show that state preparation, ISA choice, and T-depth optimization all reshape the downstream QEC burden before decoding even starts.')
lines.append('- A useful comparison output is not just logical error rate. It should report `latency`, `p99 latency`, `memory footprint`, `deadline miss rate`, `throughput per logical qubit`, and `resource-normalized logical performance`.')
lines.append('- The most distinctive research gap is system normalization: many papers report decoder quality or latency in incomparable settings. A simulator can create value by putting workload, noise model, timing budget, and hardware target into one reproducible evaluation harness.')
lines.append('')
lines.append('## Suggested Immediate Baselines')
lines.append('')
lines.append('- Architecture baseline: `1D-2` + `2001.06598v1`')
lines.append('- High-accuracy baseline: `Fusion Blossom`')
lines.append('- Learned decoder baseline: `1D-3` + `NEO-QEC`')
lines.append('- System-level baseline: `2603.16203v1` + `2605.09142v1`')
lines.append('- FT workload shaping baseline: `1D-1` + `2C-4` + `1D-4`')
brief_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

quantum_count = sum(1 for r in meta if r.get('is_quantum_candidate'))
primary_qec = sum(1 for r in meta if r.get('qec_relevance') == 'primary_qec')
related_count = len(related)
ieee_ok = sum(1 for r in ieee_rows if r['download_status'] == 'downloaded_ieee_xplore')
related_pdf_count = len([p for p in (ROOT / 'papers').glob('related__*.pdf')])
total_pdf_count = len(list((ROOT / 'papers').glob('*.pdf')))
summary = f'''# ASP-DAC 2026 QEC Literature Collection Summary

## Status

- Metadata collection complete.
- ASP-DAC 2026 IEEE papers downloaded through local authenticated browser access.
- QEC briefing report generated for ASP-DAC mainline papers and closest decoder/simulator related work.

## Statistics

- Official program records parsed: 234
- Records matched to DBLP proceedings DOI/page metadata: 212
- Strict quantum candidates: {quantum_count}
- Primary QEC/FTQC candidates: {primary_qec}
- ASP-DAC IEEE PDFs downloaded: {ieee_ok}
- Related-work open PDFs downloaded: {related_pdf_count}
- Total local PDFs in `papers/`: {total_pdf_count}

## File Inventory

- `metadata/aspdac2026_papers.json` and `.csv`: official program records merged with DBLP DOI/page metadata.
- `metadata/dblp_records.json`: parsed DBLP proceedings records.
- `metadata/related_work.json`: arXiv metadata for QEC simulator related work.
- `logs/download_report.csv`: merged per-item full-text status.
- `logs/ieee_browser_download_report.csv`: browser-driven IEEE download status.
- `reports/quantum_candidates.md`: ASP-DAC 2026 quantum/QEC screening report.
- `reports/qec_simulator_related_work.md`: related-work matrix and simulator design implications.
- `reports/qec_paper_briefs.md`: abstract-driven QEC brief, innovation summary, and same-class comparison.
- `papers/`: downloaded IEEE and open-access PDFs.

## Access Note

- ASP-DAC official program metadata still includes items without DOI or downloadable proceedings files; those remain abstract-only.
- The current local collection contains all 212 DOI-backed ASP-DAC 2026 IEEE papers plus 13 related open-access PDFs.
'''
summary_path.write_text(summary, encoding='utf-8')
print('wrote', brief_path)
print('wrote', summary_path)
