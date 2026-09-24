#!/usr/bin/env node
/**
 * Apply ./seeds.json into the current project scope.
 *
 * Idempotent: the engine's near-duplicate check rejects anything already stored,
 * so running this repeatedly never creates duplicates. Entries are written
 * pinned by default. Scope is derived from DSH_LTM_CWD / process.cwd(), which
 * run_pi.ps1 sets to the repository root, so each machine seeds its own scope
 * hash (Git project scopes are machine/path specific by design).
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { openLtm } from "./engine.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const seedsPath = process.env.DSH_LTM_SEEDS || join(here, "seeds.json");

let seeds;
try {
  seeds = JSON.parse(readFileSync(seedsPath, "utf8"));
} catch (err) {
  console.error(`[dsh-ltm-seed] cannot read ${seedsPath}: ${err?.message ?? err}`);
  process.exit(1);
}

const memories = Array.isArray(seeds?.memories) ? seeds.memories : [];

let ltm;
try {
  ltm = await openLtm({ cwd: process.env.DSH_LTM_CWD });
} catch (err) {
  console.error(`[dsh-ltm-seed] cannot open the store: ${err?.message ?? err}`);
  process.exit(1);
}

const scope = ltm.activeScope();
let created = 0;
let skipped = 0;

for (const entry of memories) {
  const text = String(entry?.text ?? "").trim();
  if (!text) continue;
  try {
    const { dedupeHits } = ltm.store.write(text, entry.tags ?? [], {
      scope,
      pinned: entry.pinned ?? true,
      force: false,
    });
    if (dedupeHits.length === 0) created++;
    else skipped++;
  } catch (err) {
    console.error(`[dsh-ltm-seed] skipped an entry: ${err?.message ?? err}`);
  }
}

console.log(`[dsh-ltm-seed] scope=${scope} created=${created} skipped=${skipped} total=${memories.length}`);
ltm.close();
