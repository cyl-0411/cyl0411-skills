import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const DESKTOP = "C:\\Users\\CYL04\\Desktop";
const TARGET_ROOT = path.join(DESKTOP, "ASP-DAC");
const YEARS = [2023, 2024, 2025, 2026];
const SOURCES = Object.fromEntries(YEARS.map((year) => [year, path.join(DESKTOP, `ASP_DAC_${year}`)]));

const QEC_SELECTION = {
  2023: ["3A-4", "8D-4", "8D-1"],
  2024: ["2B-3", "2B-4", "5C-1", "6B-4", "6B-5"],
  2025: ["6C-3", "3D-3", "6C-2"],
  2026: ["1D-1", "1D-2", "1D-3", "1D-4", "2C-4"],
};

const QEC_NOTES = {
  "2023/3A-4": {
    summary:
      "这篇工作聚焦 surface code 的加权迭代贪心译码器，强调真实物理量子比特存在明显的非均匀错误率差异，不能再用理想化的均匀噪声假设来评估译码器。论文把译码算法具体落到硬件系统设计上，关注在严格反馈时限下如何维持纠错质量。",
    innovation:
      "把 non-uniform physical error rate 直接纳入 surface-code 译码硬件设计，是从“算法能跑”推进到“在真实器件统计下能部署”。",
    comparison:
      "相较通用软件译码器或只看平均错误率的硬件实现，这篇更强调面向 surface code 在线反馈场景的延迟与器件非理想性的联合建模。",
    takeaway:
      "适合作为 decoder plugin 与 latency model 的核心参考，尤其适合定义译码器输入统计、每轮服务时间和 deadline miss 对 logical performance 的影响。",
  },
  "2023/8D-4": {
    summary:
      "这篇论文面向 quantum low-density parity-check code 的解码工具链，关注如何把 qLDPC 译码数值实验系统化、可复现化。重点不是单一某个 decoder 电路，而是为不同 qLDPC 译码方法提供统一的软件实验基础设施。",
    innovation:
      "把 qLDPC decoding 从零散算法实验整理成成体系的软件工具，对后续做统一基准和大规模实验非常关键。",
    comparison:
      "与面向 surface code 的专用低时延译码器相比，它更偏通用软件框架；与纯理论 qLDPC 论文相比，它更强调工程可复现性与实验组织。",
    takeaway:
      "非常适合作为仿真器里的 qLDPC decoder backend 参考，让系统能支持多码族、多译码算法和统一实验输入输出。",
  },
  "2023/8D-1": {
    summary:
      "这篇工作研究如何用图划分改进量子线路仿真，目的是缓解大规模量子线路在经典机上仿真时的指数复杂度与低局部性问题。它不直接解决 QEC 控制闭环，但能提升量子线路执行内核的效率。",
    innovation:
      "把图划分用于改进 Hybrid Schrodinger-Feynman 模拟流程，针对量子线路仿真的内存与访存瓶颈给出工程化加速路径。",
    comparison:
      "相较专门做译码器的论文，这篇更接近仿真引擎优化；与一般量子编译论文相比，它直接作用于 classical simulation kernel。",
    takeaway:
      "适合作为 circuit evolution / syndrome generation 层的性能参考，帮助仿真器区分“线路执行瓶颈”和“译码反馈瓶颈”。",
  },
  "2024/2B-3": {
    summary:
      "论文围绕 quantum circuit measurement 的 decision diagram 优化展开，试图降低测量与 classical shadow 等表征方法的表示和计算成本。它更靠近 measurement-side representation，而不是直接做纠错译码。",
    innovation:
      "在量子测量阶段引入更高效的 decision-diagram 组织方式，改善测量相关状态表示的紧凑性和效率。",
    comparison:
      "与 QEC decoder 论文相比，这篇不碰反馈闭环；但和一般量子编译工作相比，它更接近测量与表征开销建模。",
    takeaway:
      "适合作为 syndrome / measurement representation 的参考，让仿真器在测量数据结构层面更贴近真实 workload。",
  },
  "2024/2B-4": {
    summary:
      "CTQr 关注控制与时序感知的 qubit routing，不只满足物理连通性，还把 gate delay 与共享 classical control electronics 的限制一起纳入。对 noisy quantum processor 而言，这会直接影响最终可执行物理线路的时延。",
    innovation:
      "把 qubit routing 与 control constraint、gate timing 联合考虑，使编译结果更接近真实处理器上的执行条件。",
    comparison:
      "相较只最小化 SWAP 数量的 routing 论文，它更系统化地引入控制路径与调度约束；与 decoder 论文相比，它偏前端 workload shaping。",
    takeaway:
      "适合放进仿真器前端，让编译/路由阶段输出的电路天然携带 timing constraint，而不是只给裸电路描述。",
  },
  "2024/5C-1": {
    summary:
      "QcAssert 提出并发断言式的 quantum device testing 框架，目的是在量子线路执行过程中监视设备噪声与容限是否仍满足要求。论文关注的是设备级健康监测与测试，而不是纠错算法本身。",
    innovation:
      "把 concurrent assertion 的思想引入量子设备测试，使噪声异常检测能够与量子线路并行执行。",
    comparison:
      "与译码器论文相比，它并不输出纠错动作；但与一般设备测试工作相比，它更强调在线、并发和和量子线路运行态绑定。",
    takeaway:
      "可作为 simulator 里的 device-health / noise guard 参考模块，帮助定义“噪声超限时系统如何标记结果不可用”。",
  },
  "2024/6B-4": {
    summary:
      "论文研究 single-flux quantum 系统中的多相时钟方法，核心目标是减少 path-balancing 开销，同时保持可部署的超导逻辑映射。它更偏控制电子学和超导逻辑实现层。",
    innovation:
      "把 multiphase path balancing 形式化为可求解的映射问题，让 SFQ 控制系统的时钟组织不再只是手工经验设计。",
    comparison:
      "与直接面向 QEC decoder 的架构论文相比，它更偏底层控制硬件；但正因如此，它提供了 cryogenic control timing 的关键假设来源。",
    takeaway:
      "适合作为控制时钟和低温电子学约束的参考，让仿真器在 classical feedback path 建模时更贴近 SFQ 风格部署。",
  },
  "2024/6B-5": {
    summary:
      "这篇工作系统梳理了 SFQ superconducting circuit 的代数和布尔优化方法，并讨论了满足 path-balancing 与 fanout 约束的技术映射问题。它本质上是超导控制逻辑的综合优化论文。",
    innovation:
      "将 XAG/Boolean optimization 与 SFQ 路径平衡、扇出约束联合考虑，形成完整的超导逻辑综合流程。",
    comparison:
      "与 6B-4 一样更偏控制电子学实现，但它比 6B-4 更聚焦逻辑优化与映射，而不是时钟策略本身。",
    takeaway:
      "可作为仿真器中 control hardware assumption 的补充参考，帮助估计低温控制电路面积、深度和信号复制开销。",
  },
  "2025/6C-3": {
    summary:
      "这篇论文研究 back-end-aware 的 fault-tolerant quantum oracle synthesis，讨论逻辑综合结果如何影响后端容错实现的 T-count、T-depth、qubit 开销等指标。它不是 decoder 论文，但对 fault-tolerant workload 生成非常关键。",
    innovation:
      "首次把 XAG 级综合性质与 FTQC 后端代价直接关联，让上游综合决策能够感知容错执行成本。",
    comparison:
      "相较只做逻辑级综合优化的工作，它更贴近 QEC 成本；相较译码器论文，它位于更前端的 workload generation 层。",
    takeaway:
      "非常适合作为仿真器的 workload preprocessing 参考，用来把前端综合结果映射成后端 QEC 负载与资源估计输入。",
  },
  "2025/3D-3": {
    summary:
      "PIMutation 探索用真实 PIM 架构加速量子线路仿真，针对 state-vector simulation 的高内存占用和低局部性访问问题提出架构级优化。它更像量子线路模拟内核加速论文，而不是纠错系统论文。",
    innovation:
      "把公开可获得的 PIM 平台真正用于量子线路仿真，实现从概念到实际架构映射的第一步。",
    comparison:
      "相较传统 CPU/GPU 量子线路仿真加速，它更强调 memory-near-compute；相较 decoder 论文，它位于仿真引擎层而非 classical control loop。",
    takeaway:
      "适合作为 simulator execution kernel 的性能参考，让系统可以拆分“仿真内核加速”和“译码反馈加速”两类优化收益。",
  },
  "2025/6C-2": {
    summary:
      "论文面向动态可编程中性原子 qubit array 的编译与近最优调度，联合考虑 scheduling、placement 和 routing。虽然不直接研究 QEC，但它说明硬件约束会显著改变最终电路阶段数与 fidelity。",
    innovation:
      "给出带近最优保证的调度/布局/路由联合编译方法，使动态 qubit array 的灵活性真正可用。",
    comparison:
      "与一般 qubit routing 论文相比，它覆盖了更完整的编译链；与 QEC 工作相比，它更靠近硬件约束下的前端物理执行准备。",
    takeaway:
      "可作为 compiler-aware input pipeline 的参考，让仿真器接受的不只是逻辑电路，还包括 placement/routing/schedule 后的硬件态 workload。",
  },
  "2026/1D-1": {
    summary:
      "这篇论文把 fault-tolerant state preparation 视为 design automation 问题，目标是让 CSS 码等 QEC code 的逻辑态制备从手工构造走向自动综合和优化。虽然当前缺少本地全文，但从摘要和元数据看，它明显位于 decoder 之前的 workload 构造层。",
    innovation:
      "把容错逻辑态制备正式纳入 CAD 流，强调 state preparation 也是 FTQC 成本的重要来源。",
    comparison:
      "相较 1D-2/1D-3 这类译码阶段论文，它更偏前端状态初始化；相较单纯综合论文，它直接服务于 QEC workload 建模。",
    takeaway:
      "适合在仿真器中单独建模 initialization workload，把 ancilla 需求、制备延迟和前置资源开销显式接入端到端评估。",
  },
  "2026/1D-2": {
    summary:
      "论文提出 hardware-efficient 的 Union-Find decoder，目标是在 scalable topological code 上实现更可部署的低延迟译码硬件。重点在于资源组织、内存访问和实际可扩展性，而不只是算法正确率。",
    innovation:
      "把 Union-Find 从“算法可行”推进到“硬件上可扩展可部署”，强调低延迟和资源效率的共同优化。",
    comparison:
      "相较 MWPM/Blossom 系译码器，它更偏低复杂度和硬件友好；相较 LUT 或纯学习型方案，它兼顾通用性与实时性。",
    takeaway:
      "这是最适合作为 QEC 仿真器 decoder baseline 的论文之一，尤其适合定义 latency、memory footprint 和 throughput 指标。",
  },
  "2026/1D-3": {
    summary:
      "这篇工作探索用强化学习增强 advanced QEC architecture 的译码，试图让 decoder 在更复杂的 syndrome 结构和噪声模式下自适应优化决策。它体现的是 learned decoder 路线，而不是传统 hand-crafted decoder。",
    innovation:
      "把 RL 直接引入 advanced QEC / qLDPC 类译码，强调策略学习而非固定规则。",
    comparison:
      "相较 1D-2 的硬件友好规则型 decoder，它更偏算法策略；和 GNN/NN 在线 decoder 相比，它的重点是策略搜索能力。",
    takeaway:
      "仿真器应支持 learned decoder plugin，并能比较 inference cost、accuracy 和 deadline compliance 的权衡。",
  },
  "2026/1D-4": {
    summary:
      "Quantum ISA 这篇工作讨论指令集抽象如何影响底层量子硬件与容错实现成本。它不直接设计 decoder，但清楚表明 ISA 决策、门集抽象和控制语义会反馈到后端 QEC 负担。",
    innovation:
      "把 ISA、硬件原语与 QEC cost 放到同一个协同设计框架中讨论，而不是把它们割裂开看。",
    comparison:
      "与 2C-4 一样都影响 FTQC 成本，但 1D-4 更偏系统抽象和接口层；相较 decoder 论文，它位于更上游。",
    takeaway:
      "适合作为 simulator 前端接口设计参考，让输入工作负载不仅是电路，也包含 ISA/primitive 层面的约束。",
  },
  "2026/2C-4": {
    summary:
      "这篇论文通过 evolutionary optimization 做 T-depth reduction，核心目标是降低 fault-tolerant 执行中的 magic-state 与时间开销。它不研究 syndrome decoding，但会显著改变后端 QEC 负担。",
    innovation:
      "把 T-depth reduction 做成系统性的搜索优化问题，在 FTQC workload shaping 上直接产生收益。",
    comparison:
      "相较 1D-2/1D-3 这类 decoder-centric 论文，它更像 workload optimizer；与 1D-4 的 ISA 视角相比，它更偏编译后资源压缩。",
    takeaway:
      "应放进 simulator 的 workload preprocessing 层，把 T-depth、T-count 和 magic-state demand 与 decoder latency 一起纳入总成本模型。",
  },
};

function slugify(value, maxLen = 72) {
  return (value || "paper")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, maxLen)
    .replace(/-$/, "") || "paper";
}

function doiSafe(doi) {
  return String(doi || "")
    .replace(/[^A-Za-z0-9.]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function parseCsv(text) {
  text = text.replace(/^\uFEFF/, "");
  const rows = [];
  let row = [];
  let cur = "";
  let q = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') {
        cur += '"';
        i += 1;
      } else if (c === '"') {
        q = false;
      } else {
        cur += c;
      }
    } else if (c === '"') {
      q = true;
    } else if (c === ",") {
      row.push(cur);
      cur = "";
    } else if (c === "\n") {
      row.push(cur.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      cur = "";
    } else {
      cur += c;
    }
  }
  if (cur.length || row.length) {
    row.push(cur.replace(/\r$/, ""));
    rows.push(row);
  }
  const header = rows.shift() || [];
  return rows
    .filter((r) => r.length && r.some((x) => x))
    .map((r) => Object.fromEntries(header.map((h, i) => [h, r[i] || ""])));
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

async function safeRm(targetPath) {
  if (await exists(targetPath)) {
    await fs.rm(targetPath, { recursive: true, force: true });
  }
}

async function ensureCleanTarget(root) {
  await fs.mkdir(root, { recursive: true });
  for (const name of ["2023", "2024", "2025", "2026", "QEC", "missing_papers.xlsx"]) {
    await safeRm(path.join(root, name));
  }
}

async function listPdfFiles(dirPath, { excludeRelated = false } = {}) {
  const items = await fs.readdir(dirPath, { withFileTypes: true });
  return items
    .filter((item) => item.isFile() && item.name.toLowerCase().endsWith(".pdf"))
    .map((item) => item.name)
    .filter((name) => !(excludeRelated && name.startsWith("related__")))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}

async function copyYearPdfs(year) {
  const srcDir = path.join(SOURCES[year], "papers");
  const dstDir = path.join(TARGET_ROOT, String(year));
  await fs.mkdir(dstDir, { recursive: true });
  const names = await listPdfFiles(srcDir, { excludeRelated: year === 2026 });
  for (const name of names) {
    await fs.copyFile(path.join(srcDir, name), path.join(dstDir, name));
  }
  return names;
}

async function loadMetadata(year) {
  const metaDir = path.join(SOURCES[year], "metadata");
  const files = await fs.readdir(metaDir);
  const paperFile =
    files.find((name) => name.includes(`aspdac${year}`) && name.endsWith("_papers.json")) ||
    files.find((name) => name.endsWith("_papers.json")) ||
    files.find((name) => name.endsWith(".json") && name.includes("papers"));
  if (!paperFile) throw new Error(`metadata json not found for ${year}`);
  return readJson(path.join(metaDir, paperFile));
}

async function loadDownloadRows(year) {
  const csvText = await fs.readFile(path.join(SOURCES[year], "logs", "download_report.csv"), "utf8");
  return parseCsv(csvText);
}

function getPaperIdField(record) {
  if ("paper_id" in record) return "paper_id";
  if ("session_paper_id" in record) return "session_paper_id";
  throw new Error("unknown paper id field");
}

function expectedPdfName(record, idField) {
  const doiPart = doiSafe(record.doi || "");
  const titlePart = slugify(record.title || "paper");
  if (doiPart) return `${record[idField]}__${titlePart}__${doiPart}.pdf`;
  return `${record[idField]}__${titlePart}.pdf`;
}

async function buildYearData(year) {
  const metadata = await loadMetadata(year);
  const logRows = await loadDownloadRows(year);
  const idField = getPaperIdField(metadata[0]);
  const metadataById = new Map(metadata.map((record) => [String(record[idField]), record]));
  const missingRows = [];
  for (const row of logRows) {
    if (String(row.download_status || "").startsWith("downloaded")) continue;
    const paperId = String(row.paper_id || row.session_paper_id || "");
    const record = metadataById.get(paperId) || {};
    const notes =
      row.download_status === "metadata_only_no_doi"
        ? "metadata-only entry; no DOI in current source index"
        : "PDF not downloaded in existing archive";
    missingRows.push({
      paper_id: paperId,
      title: row.title || record.title || "",
      doi: row.doi || record.doi || "",
      source_url: row.source_url || row.doi_url || record.doi_url || record.ee_url || "",
      download_status: row.download_status || "",
      failure_reason: row.failure_reason || "",
      expected_pdf_name: expectedPdfName({ ...record, title: row.title || record.title || "", doi: row.doi || record.doi || "", [idField]: paperId }, idField),
      notes,
    });
  }
  missingRows.sort((a, b) => a.paper_id.localeCompare(b.paper_id, undefined, { numeric: true }));
  const statusBreakdown = {};
  for (const row of missingRows) {
    statusBreakdown[row.download_status] = (statusBreakdown[row.download_status] || 0) + 1;
  }
  return { metadata, idField, missingRows, statusBreakdown };
}

async function buildWorkbook(yearCopies, yearData) {
  const workbook = Workbook.create();
  const overview = workbook.worksheets.add("Overview");
  overview.showGridLines = false;
  overview.freezePanes.freezeRows(1);
  const overviewHeader = [["year", "downloaded_pdf_count", "missing_count", "missing_status_breakdown"]];
  const overviewRows = YEARS.map((year) => [
    year,
    yearCopies[year].length,
    yearData[year].missingRows.length,
    Object.entries(yearData[year].statusBreakdown)
      .map(([k, v]) => `${k}=${v}`)
      .join("; "),
  ]);
  overview.getRange(`A1:D${overviewRows.length + 1}`).values = [...overviewHeader, ...overviewRows];
  overview.getRange("A1:D1").format = {
    fill: "#1F4E78",
    font: { bold: true, color: "#FFFFFF" },
    horizontalAlignment: "Center",
  };
  overview.getRange(`A2:A${overviewRows.length + 1}`).format.horizontalAlignment = "Center";
  overview.getRange(`B2:C${overviewRows.length + 1}`).format.horizontalAlignment = "Right";
  overview.getRange(`A1:D${overviewRows.length + 1}`).format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
  overview.getRange("A:D").format.autofitColumns();

  const columns = [
    "paper_id",
    "title",
    "doi",
    "source_url",
    "download_status",
    "failure_reason",
    "expected_pdf_name",
    "notes",
  ];

  for (const year of YEARS) {
    const sheet = workbook.worksheets.add(String(year));
    sheet.showGridLines = false;
    sheet.freezePanes.freezeRows(1);
    const rows = yearData[year].missingRows.map((row) => columns.map((key) => row[key]));
    const matrix = [columns, ...rows];
    const endRow = Math.max(matrix.length, 2);
    sheet.getRange(`A1:H${endRow}`).values = matrix.length > 0 ? matrix : [columns];
    sheet.getRange("A1:H1").format = {
      fill: "#2F75B5",
      font: { bold: true, color: "#FFFFFF" },
      horizontalAlignment: "Center",
      wrapText: true,
    };
    if (rows.length > 0) {
      sheet.getRange(`A2:A${rows.length + 1}`).format.horizontalAlignment = "Center";
      sheet.getRange(`C2:C${rows.length + 1}`).format.horizontalAlignment = "Left";
      sheet.getRange(`D2:D${rows.length + 1}`).format.wrapText = true;
      sheet.getRange(`E2:E${rows.length + 1}`).format.horizontalAlignment = "Center";
      sheet.getRange(`F2:H${rows.length + 1}`).format.wrapText = true;
    }
    sheet.getRange(`A1:H${Math.max(rows.length + 1, 2)}`).format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
    sheet.getRange("A:H").format.autofitColumns();
    sheet.getRange("B:B").format.columnWidthPx = 280;
    sheet.getRange("D:D").format.columnWidthPx = 280;
    sheet.getRange("F:F").format.columnWidthPx = 260;
    sheet.getRange("G:G").format.columnWidthPx = 240;
    sheet.getRange("H:H").format.columnWidthPx = 220;
  }

  return workbook;
}

async function findPdfById(year, paperId) {
  const srcDir = path.join(SOURCES[year], "papers");
  const files = await listPdfFiles(srcDir, { excludeRelated: false });
  return files.find((name) => name.startsWith(`${paperId}__`)) || null;
}

async function copyQecPdfs(yearData) {
  const copied = {};
  const qecRoot = path.join(TARGET_ROOT, "QEC");
  await fs.mkdir(qecRoot, { recursive: true });
  for (const year of YEARS) {
    const yearDir = path.join(qecRoot, String(year));
    await fs.mkdir(yearDir, { recursive: true });
    copied[year] = {};
    for (const paperId of QEC_SELECTION[year]) {
      const fileName = await findPdfById(year, paperId);
      if (fileName) {
        await fs.copyFile(path.join(SOURCES[year], "papers", fileName), path.join(yearDir, fileName));
      }
      const record = yearData[year].metadata.find((item) => String(item[yearData[year].idField]) === paperId);
      copied[year][paperId] = {
        fileName,
        record,
        status: fileName ? "已复制 PDF" : "未获取全文，仅基于摘要/元数据总结",
      };
    }
  }
  return copied;
}

function buildQecOverview() {
  return [
    "## 总览",
    "",
    "- 最接近 `decoder plugin / latency model` 的论文：`2023/3A-4`、`2023/8D-4`、`2026/1D-2`、`2026/1D-3`。",
    "- 更偏 `compiler / routing / control hardware` 的论文：`2024/2B-4`、`2024/6B-4`、`2024/6B-5`、`2025/6C-2`、`2026/1D-4`、`2026/2C-4`。",
    "- 更适合作为 `system-level benchmark` 或仿真内核参考的论文：`2023/8D-1`、`2025/3D-3`、`2025/6C-3`。",
    "",
  ].join("\n");
}

function buildQecReadme(copied, yearData) {
  const lines = ["# ASP-DAC QEC 相关论文整理", ""];
  lines.push("本目录汇总了 2023-2026 年 ASP-DAC 中与 QEC 仿真器设计最相关的论文副本。所有 PDF 均为复制副本，原始下载目录保持不变。", "");
  for (const year of YEARS) {
    lines.push(`## ${year}`, "");
    for (const paperId of QEC_SELECTION[year]) {
      const item = copied[year][paperId];
      const record = item.record || {};
      const note = QEC_NOTES[`${year}/${paperId}`];
      const doi = record.doi || "无 DOI / metadata-only";
      lines.push(`### ${paperId} - ${record.title || "Unknown Title"}`, "");
      lines.push(`- DOI: ${doi}`);
      lines.push(`- 全文状态：${item.status}`);
      lines.push(`- 内容概括：${note.summary}`);
      lines.push(`- 创新点：${note.innovation}`);
      lines.push(`- 同类工作定位：${note.comparison}`);
      lines.push(`- 对 QEC 仿真器的启发：${note.takeaway}`, "");
    }
  }
  lines.push(buildQecOverview());
  return lines.join("\n");
}

async function verifyWorkbook(workbook, outputRoot) {
  const inspect = await workbook.inspect({
    kind: "table",
    range: "A1:D10",
    sheetId: "Overview",
    include: "values",
    tableMaxRows: 10,
    tableMaxCols: 4,
  });
  await fs.writeFile(path.join(outputRoot, "_overview_inspect.ndjson"), inspect.ndjson, "utf8");
  const errorScan = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: "final formula error scan",
  });
  await fs.writeFile(path.join(outputRoot, "_error_scan.ndjson"), errorScan.ndjson, "utf8");
  const renderDir = path.join(os.tmpdir(), "aspdac_archive_previews");
  await fs.mkdir(renderDir, { recursive: true });
  for (const sheetName of ["Overview", "2023", "2024", "2025", "2026"]) {
    const blob = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
    await fs.writeFile(path.join(renderDir, `${sheetName}.png`), new Uint8Array(await blob.arrayBuffer()));
  }
}

async function main() {
  await ensureCleanTarget(TARGET_ROOT);

  const yearCopies = {};
  const yearData = {};
  for (const year of YEARS) {
    yearCopies[year] = await copyYearPdfs(year);
    yearData[year] = await buildYearData(year);
  }

  const workbook = await buildWorkbook(yearCopies, yearData);
  await verifyWorkbook(workbook, TARGET_ROOT);
  const exported = await SpreadsheetFile.exportXlsx(workbook);
  await exported.save(path.join(TARGET_ROOT, "missing_papers.xlsx"));

  const copied = await copyQecPdfs(yearData);
  const readme = buildQecReadme(copied, yearData);
  await fs.writeFile(path.join(TARGET_ROOT, "QEC", "README.md"), readme, "utf8");

  const summary = {
    targetRoot: TARGET_ROOT,
    copiedYearCounts: Object.fromEntries(YEARS.map((year) => [year, yearCopies[year].length])),
    missingCounts: Object.fromEntries(YEARS.map((year) => [year, yearData[year].missingRows.length])),
    qecPdfCounts: Object.fromEntries(YEARS.map((year) => [year, Object.values(copied[year]).filter((item) => item.fileName).length])),
  };
  await fs.writeFile(path.join(TARGET_ROOT, "_build_summary.json"), JSON.stringify(summary, null, 2), "utf8");
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
