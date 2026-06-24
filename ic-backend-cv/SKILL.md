---
name: ic-backend-cv
description: Review, revise, compress, and version Chinese CV/resume content for digital IC backend roles. Use when working on semiconductor CVs that mention Netlist-to-GDSII, PnR, STA, DRC/LVS, IR Drop, PG connectivity, Power Plan/Power Planning, ASIC tapeout, chip testing, EDA tools, internship/project sections, paper results, or when the user asks to make CV wording accurate, concise, professional, realistic, consistently formatted, or commit large CV revisions.
---

# IC Backend CV

Use this skill to edit or review Chinese resumes for digital IC backend design roles. Keep the document truthful, compact, technically precise, and easy for an interviewer to scan.

## Workflow

1. Read the current resume source before changing text. Also inspect build files when page count or output location matters.
2. Identify the target version: one-page CV, two-page CV, or full resume. Preserve the current branch/version intent.
3. Prioritize content by role fit. For digital backend roles, give space first to internship, backend projects, tapeout/testing, physical implementation, verification closure, and papers. Compress awards and organization sections before compressing core backend experience.
4. Check every factual claim against user-provided context and the current file. Do not invent metrics, tools, signoff results, tapeout status, author order, patent status, or ownership level.
5. After substantial edits, build the PDF, verify the page count, then report what changed and whether the PDF compiled.

## Content Weight

- One-page CV: keep education, concise skills, internship, selected backend projects, papers, and a compact summary. Remove or omit awards and organization experience unless the user asks otherwise.
- Two-page CV: keep richer project detail and may include awards/organization experience, but do not let them crowd out internship, project, or paper sections.
- Skills section: keep it short. Use it as an index of capabilities, not a second project section.
- Project section: prefer concrete backend work, constraints, debug actions, and measurable outcomes over generic adjectives.
- Personal summary: summarize direction and proof points. Avoid personality-only claims such as hardworking, serious, passionate, or strong learning ability unless tied to evidence.

## Wording Rules

- Be concise, factual, and interview-defensible.
- Avoid unsupported or inflated wording: 精通, 大幅提升, 显著优化, 流片级交付, 完美解决, 全面负责全芯片, 业内领先.
- Use ownership carefully:
  - Use 合作项目 for shared chips or papers.
  - Use 主导 only for the part the user actually led.
  - Use 独立完成 only for personal projects or independently owned work.
- For cooperation projects, do not imply sole full-chip responsibility. Prefer 参与, 负责, 主导某模块/某阶段.
- Keep STAR-like logic but avoid bulky STAR labels in the final resume: background/problem -> action -> result.
- Prefer strong verbs with concrete objects: 搭建 flow, 配置约束, 完成 PnR, 定位短路/开路, 修复 PG connectivity, 推动 GDSII 交付.

## Terminology

Use these forms consistently unless the user or project source requires otherwise:

- `Netlist-to-GDSII`
- `GDSII 交付`
- `PnR`
- `STA`
- `CTS`
- `DRC/LVS`
- `IR Drop`
- `PG connectivity`
- `Power Plan` or `Power Planning`
- `AON/PSO 双电源域`, not 双电压域 unless the design truly has different voltage levels
- `Via Ladder`
- `RedHawk`
- `MMMC`
- `uncertainty`
- `Floorplan`
- `Macro`
- `netlist` for generic netlists, `Netlist-to-GDSII` for the full flow
- Use SI spacing in metrics: `200 MHz`, `6.7 ms`, `12.74 mW`, `20.8 ns`
- Use consistent date format: `YYYY.MM - YYYY.MM`

When describing Via Ladder, connect it to lowering PG-network resistance/impedance and improving vertical power delivery under advanced-process interconnect/via resistance. Do not imply it is used only because a design has multiple power domains.

For DRC/LVS debug, prefer precise issue classes: 短路、开路、器件/端口不匹配、PG connectivity. Avoid vague phrases like 连接问题 unless space is extremely tight.

## Project Pattern

For each project, use either one compact bullet or two bullets depending on page budget.

One-bullet pattern:
`项目类型。工艺/平台 + 角色 + 完成范围；关键问题 + 方法 + 结果。`

Two-bullet pattern:
1. `项目类型。项目背景 + 工艺/平台 + 角色 + 完成范围。`
2. `关键问题/亮点 + 解决方法 + 指标或验证结果。`

Good backend details include flow setup, MMMC/uncertainty, floorplan, power planning, PnR, CTS, STA, DRC/LVS, RedHawk IR Drop, PG connectivity, macro placement, pin/interface coordination, and GDSII delivery.

## Paper And Result Claims

- Preserve author order and contribution marks exactly as confirmed by the user.
- If space is tight, list the first three authors plus `et al.` while keeping the user's name bold and preserving equal-contribution markers.
- Use `accepted` only when the user confirms acceptance. Do not add conference or journal names unless provided.
- Do not convert paper results into project metrics unless the project text already supports that relationship.

## Build And Versioning

- For small wording edits, compile if the change can affect page count. Tell the user the change is uncommitted unless they asked for a commit.
- For large CV content revisions, run `make -B`, confirm the PDF compiles and the intended page count holds, then commit and push when requested or when the user explicitly instructed this workflow.
- Keep generated root PDFs synchronized with source when the repo convention is to store the built PDF.
- Do not modify unrelated branches or files. If the worktree already has unrelated user changes, preserve them and mention them when relevant.
