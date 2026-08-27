#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const manifestPath = path.join(scriptDir, '..', 'full-runtime-manifest.json');

function announce() {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const aliases = [];
  for (const command of manifest.commands) {
    for (const alias of command.aliases) {
      const normalized = alias.replace(/^\/+/, '');
      if (!aliases.includes(normalized)) aliases.push(normalized);
    }
  }
  return {
    name: manifest.adapter.name,
    full_runtime: 'opt-in with ARS_CODEX_FULL_RUNTIME=1',
    agent_team: 'opt-in with ARS_CODEX_AGENT_TEAM=1',
    hooks: 'opt-in with ARS_CODEX_HOOKS=1',
    aliases,
    note: 'Hook wrapper is read-only and does not print secrets or mutate files.',
  };
}

if (process.argv.length !== 3 || process.argv[2] !== 'announce') {
  console.error('Usage: node ars_codex_hook.mjs announce');
  process.exit(2);
}

process.stdout.write(`${JSON.stringify(announce())}\n`);
