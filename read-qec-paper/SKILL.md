---
name: read-qec-paper
description: 阅读单篇量子纠错（QEC）论文并提取解码算法、LER、复杂度、硬件平台/工艺、资源、功耗、频率、延迟、吞吐和噪声模型，输出结构化 Markdown 指标笔记。全文双语翻译或通读改用 nature-reader。
---

# Read QEC Paper

## Overview

阅读单篇 QEC 论文并输出结构化中文 Markdown 笔记。优先提取算法表现、复杂度、硬件代价、噪声模型与实验条件，避免只写泛泛的“背景介绍”。
先抽取证据，再组织结论。任何指标都要尽量绑定原文条件，例如码距 `d`、物理错误率 `p`、轮数、噪声类型、芯片工艺、是否为综合/后仿/实测。
最终Markdown 必须先给出一段“摘要概述（Abstract Summary）”，用3-6 句概括论文想解决的问题、核心方法、主要结果和意义，然后再进入后续分析章节。
## Workflow

### 1. 先判断论文重心
先快速判断这篇论文更偏向哪一类，再调整阅读重心：

- 解码算法论文：优先看 LER、复杂度、与基线比较、泛化能力、实时性。- 硬件实现论文：优先看平台、工艺、资源、存储、频率、功耗、延迟、面积、吞吐。- 噪声模型或仿真论文：优先看噪声来源、构建假设、相关性、适用码族、评估口径。- 协同设计论文：同时覆盖算法与硬件，不要只总结其中一侧。
### 2. 用“证据优先”的顺序阅读

按下面顺序找信息，减少遗漏：

1. 标题、摘要、引言：确定论文目标、对象码族、主要贡献。2. 方法部分：确认算法类型、核心机制、理论复杂度、硬件结构。3. 实验部分：提取LER、延迟、资源、功耗、频率、吞吐、对比基线。4. 噪声模型与设置：记录错误类型、相关性、测量轮数、参数范围。5. 结论与局限：总结优势，也写明适用边界或未覆盖情形。
开始正式写作前，先基于摘要和引言写一节“摘要概述”，不要把这节写成逐条抄录摘要，而要压缩成结构化中文总结。
如果论文是硬件论文，额外优先搜索这些关键词：`FPGA`、`ASIC`、`CMOS`、`FDSOI`、`LUT`、`BRAM`、`DSP`、`SRAM`、`latency`、`throughput`、`power`、`frequency`、`area`。
如果论文是算法论文，额外优先搜索这些关键词：`LER`、`logical error rate`、`complexity`、`runtime`、`scaling`、`threshold`、`decoder`、`baseline`。
如果论文涉及噪声模型，额外优先搜索这些关键词：`phenomenological`、`circuit-level`、`depolarizing`、`biased noise`、`correlated`、`measurement error`、`erasure`、`leakage`、`cross-talk`。
## Mandatory Extraction Items

### 基本信息

至少记录：
- 论文标题
- 摘要概述：用 3-6 句总结论文问题、方法、主要结果、结论- 作者或团队（若容易获取）- 年份、会议或期刊（若文中可得）- 目标码族或任务，例如 surface code、color code、honeycomb code
- 论文类型：算法、硬件、协同设计、噪声建模
### 算法维度

重点提取：
- 解码算法名称与类别，例如 MWPM、UF、神经网络、Transformer、局部启发式、混合解码- Weight Type：只按下面规则填写：如果原文明确说支持weighted edges，记为`Arbitrary`；否则记为`N/M`
- 论文报告的LER 或等价逻辑错误性能
- LER 对应的实验条件：`d`、`p`、测量轮数、噪声模型、是否memory experiment
- 理论复杂度：时间复杂度、空间复杂度；若没有严格公式，写清经验复杂度或扩展趋势- 实际运行性能：延迟、吞吐、是否满足实时解码- 核心优势：准确率、速度、可扩展性、泛化性、硬件友好性、资源节省等
- 基线比较对象和提升幅度
不要孤立地写一个LER 数字。必须说明它是在什么条件下得到的。
### 硬件维度

只要论文涉及实现或硬件映射，就重点提取：

- 实现平台：FPGA、ASIC、CPU、GPU、TPU，或 cryogenic / room-temperature 场景
- 若为 ASIC，记录工艺节点、工艺类型、温区、是否后仿或实测
- 若为 FPGA，记录器件型号与资源类型
- 存储与资源消耗：LUT、FF、BRAM、DSP、SRAM、寄存器、片上缓存、模型参数量
- 面积或芯片面积- 功耗或能耗- 时钟频率
- 工作温度，例如room temperature、K、mK、cryogenic；若论文未说明，填`N/M`
- 延迟、吞吐、每轮解码时间、是否满足1 us 级实时约束
如果论文只说“硬件友好”但不给数字，要明确写`N/M`，不要自行推断具体资源功耗。
### 噪声模型维度

只要论文提到噪声、仿真设置或实验设置，就提取：
- 噪声模型名称，例如phenomenological、circuit-level、SI1000、biased noise
- 错误来源：数据比特、辅助比特、测量、重置、单比特门、双比特门、泄漏、擦除等
- 是否考虑时空相关、hook error、测量错误、边界效应- 参数范围，例如`p in [0.001, 0.03]`
- 噪声模型与实验平台或码族的匹配关系
如果噪声模型是论文贡献的一部分，要单独说明它如何构建、与现有模型相比多覆盖了什么现象。
## Writing Rules

- 用中文写正文，保留原始英文术语与缩写。- 不要编造未出现的指标。缺失时写`N/M`。- 数字优先保留原始单位，不要擅自换算后丢掉原单位。- 结论必须尽量附带条件，不要把特定 `d`、`p` 下的结果写成普适结论。- 若论文同时给出理论值、仿真值、综合结果、后仿结果、实测结果，要标明来源。- 如果论文存在明显局限，例如只支持现象级噪声、只在小码距验证、只给平均复杂度、不含功耗实测，要写出来。
## Output Structure

按下面结构输出；如果某一节完全不适用，可以简写，但不要删除总结表：

1. `# 论文标题`
2. `## 0. 摘要概述`
3. `## 1. 研究背景与动机`
4. `## 2. 核心创新点`
5. `## 3. 具体实现方法与架构`
6. `## 4. 详细性能评估`
7. `## 5. 噪声模型与实验设置`
8. `## 6. 优势、局限与适用边界`
9. `## 7. 综合性能总结表` 或后续扩展分析节

如果论文几乎不涉及噪声模型，可以在第 5 节写明“论文未详细展开噪声模型，仅说明为……”，不要整节留空。
“摘要概述”必须放在所有分析章节之前，不能省略。
## Summary Table Requirements

在文件末尾必须放一个“论文指标表”，固定使用下面这11 个字段作为列；不存在时写 `N/M`：
| Implementation | Algorithm | Distance | Weight Type | Memory | LER | Decode time | Frequency | Power | Temperature | Noise Model |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
|  |  |  |  |  |  |  |  |  |  |  |

字段含义按下面口径统一：
- `Implementation`：实现平台或工艺，例如`Xilinx VCU129 FPGA`、`22nm FDSOI ASIC`、`GPU inference only`、`N/M`
- `Algorithm`：解码算法或模型名称，例如`Distributed Union-Find`、`MWPM`、`ViT + SoftMoE`
- `Distance`：论文给出结果所对应的码距，例如 `d=17`、`d=21`、`L=4,6,8`
- `Weight Type`：如果原文明确说支持 weighted edges，写 `Arbitrary`；否则写 `N/M`
- `Memory`：存储或硬件资源，例如`89.8万LUT + 23.8万FF`、`BRAM 12`、`SRAM 64 KB`、`参数量7.9M`
- `LER`：逻辑错误率，尽量带条件- `Decode time`：解码时间，尽量写成 `xx ns/round`、`xx us/cycle`
- `Frequency`：工作频率或时钟，未给出则写 `N/M`
- `Power`：功耗或能耗，未给出则写`N/M`
- `Temperature`：工作温度，例如 `room temperature`、`4 K`、`mK`、`N/M`
- `Noise Model`：如果文中说明了所用噪声模型，就写入，例如 `phenomenological`、`circuit-level`、`SI1000`、`depolarizing`；否则写 `N/M`

如果一篇文章同时报告多个配置，例如现象级和电路级、FPGA 和ASIC、不同码距或不同温区，可以在表格中使用多行，而不是把所有配置挤在同一个单元格里。
除了这张固定指标表，可以在前文继续保留一张更自由的总结表，但不能省略这张固定字段表。
## References

需要现成写作骨架时，读取[references/output-template.md](references/output-template.md)。
需要逐项核对是否漏掉关键指标时，读取 [references/extraction-checklist.md](references/extraction-checklist.md)。

## SI1000 Extraction Note

- If a paper uses the `SI1000` noise model, explicitly extract the global base-rate definition and the per-operation scaling ratios instead of recording only one `p`.
- For `A fault-tolerant honeycomb memory` Table 2, the base rate `p` scales as:
  - `CZ`: `p`
  - `1q Clifford`: `p/10`
  - `Reset / InitZ`: `2p`
  - `Measurement / MZ`: `5p`
  - `Idle`: `p/10`
  - `ResonatorIdle` or idle during measurement/reset windows: `2p`
- When reading or summarizing code, make it explicit whether a local variable such as `pos` corresponds to the SI1000 base rate or to one of the derived channel rates.

