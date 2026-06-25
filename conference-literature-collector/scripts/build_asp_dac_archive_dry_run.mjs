import path from "node:path";

const DESKTOP = "C:\\Users\\CYL04\\Desktop";
const TARGET_ROOT = path.join(DESKTOP, "ASP-DAC");
const YEARS = [2023, 2024, 2025, 2026];
const SOURCES = Object.fromEntries(YEARS.map((year) => [year, path.join(DESKTOP, `ASP_DAC_${year}`)]));

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  console.log(`Usage: node build_asp_dac_archive_dry_run.mjs

Print the Desktop ASP-DAC archive plan without copying, deleting, or writing files.`);
  process.exit(0);
}

console.log(JSON.stringify({ dryRun: true, targetRoot: TARGET_ROOT, sources: SOURCES, years: YEARS }, null, 2));
