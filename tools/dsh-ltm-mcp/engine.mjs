/**
 * Shared dsh-ltm engine loader.
 *
 * Used by both `mcp-server.mjs` (MCP tools) and `dsh-ltm-recall.ts` (Pi
 * auto-recall extension) so the engine is resolved in one place.
 *
 * The @tr1v3r/dsh-ltm bundle ships its engine as a hashed chunk
 * (`dist/scope-*.js`) that imports standalone (node:sqlite + schemastery only),
 * with real names hidden behind minified aliases:
 *   export { tokenize as _, ..., MemoryStore as u, loadConfig as y }
 * We discover the chunk and parse that export map at runtime so the loader
 * stays correct across builds, hashes, and alias changes.
 */
import { createRequire } from "node:module";
import { readdirSync, readFileSync, mkdirSync } from "node:fs";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { homedir } from "node:os";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

/** Absolute path to the installed @tr1v3r/dsh-ltm package, or undefined. */
export function findEnginePackage() {
  try {
    return dirname(require.resolve("@tr1v3r/dsh-ltm/package.json"));
  } catch {
    return undefined;
  }
}

/** Load the dsh-ltm engine functions. */
export async function loadEngine() {
  const pkgDir = findEnginePackage();
  if (!pkgDir) {
    throw new Error("@tr1v3r/dsh-ltm is not installed. Run `npm install` in this directory.");
  }

  const distDir = join(pkgDir, "dist");
  const chunkFile = readdirSync(distDir).find((f) => /^scope-.*\.js$/.test(f));
  if (!chunkFile) {
    throw new Error(`No dsh-ltm engine chunk (scope-*.js) found in ${distDir}.`);
  }
  const chunkPath = join(distDir, chunkFile);

  const exportMap = new Map(); // realName -> exportedAlias
  const stmt = readFileSync(chunkPath, "utf8").match(/export\s*\{([^}]+)\}/);
  if (stmt) {
    for (const raw of stmt[1].split(",")) {
      const part = raw.trim();
      if (!part) continue;
      const m = part.match(/^([A-Za-z0-9_$]+)\s+as\s+([A-Za-z0-9_$]+)$/);
      exportMap.set(m ? m[1] : part, m ? m[2] : part);
    }
  }

  const mod = await import(pathToFileURL(chunkPath).href);
  const pick = (name) => {
    const alias = exportMap.get(name) ?? name;
    const value = mod[alias];
    if (value === undefined) {
      throw new Error(`dsh-ltm engine export "${name}" not found (chunk ${chunkFile}).`);
    }
    return value;
  };

  return {
    chunkPath,
    MemoryStore: pick("MemoryStore"),
    loadConfig: pick("loadConfig"),
    resolveProjectScope: pick("resolveProjectScope"),
    visibleScopes: pick("visibleScopes"),
    normalizeTags: pick("normalizeTags"),
    renderPrompt: pick("renderPrompt"),
    loadTokenCounter: pick("loadTokenCounter"),
    promptBudgetReport: pick("promptBudgetReport"),
  };
}

/** Default SQLite path, shared with the Pi agent directory. */
export function defaultDbPath() {
  const base = process.env.PI_CODING_AGENT_DIR || join(homedir(), ".pi", "agent");
  return join(base, "memory", "ltm.db");
}

/** Resolve DSH_LTM_DB (or the default) to an absolute path. */
export function resolveDbPath(raw = process.env.DSH_LTM_DB) {
  const value = String(raw ?? "").trim();
  if (!value) return defaultDbPath();
  if (value === ":memory:") return value;
  return isAbsolute(value) ? value : resolve(process.cwd(), value);
}

/**
 * Open a store with scope helpers and a bounded recall renderer.
 *
 * @param {{ dbPath?: string, cwd?: string, defaultScope?: string, autoProjectScope?: boolean }} [options]
 */
export async function openLtm(options = {}) {
  const engine = await loadEngine();

  const dbPath = resolveDbPath(options.dbPath);
  if (dbPath !== ":memory:") {
    try {
      mkdirSync(dirname(dbPath), { recursive: true });
    } catch { /* the store reports an unusable path clearly */ }
  }

  const config = engine.loadConfig({
    path: dbPath,
    autoProjectScope: options.autoProjectScope ?? (process.env.DSH_LTM_AUTO_SCOPE !== "0"),
    defaultScope: options.defaultScope ?? (process.env.DSH_LTM_DEFAULT_SCOPE || ""),
  });

  const store = new engine.MemoryStore(config.path, {
    staleAfterDays: config.staleAfterDays,
    dedupeThreshold: config.dedupeThreshold,
    dedupeCosineThreshold: config.dedupeCosineThreshold,
    maxTextChars: config.maxTextChars,
    searchLimitMax: config.searchLimitMax,
  });

  const cwd = options.cwd || process.env.DSH_LTM_CWD || process.cwd();
  const activeScope = () =>
    config.autoProjectScope
      ? engine.resolveProjectScope(cwd, config.defaultScope).scope
      : config.defaultScope;
  const readableScopes = () => engine.visibleScopes(activeScope(), config.autoProjectScope);

  /** Bounded pinned + recent recall section, or "" when empty/unavailable. */
  const recall = () => engine.renderPrompt(store.forPrompt(config.promptRecentCount, readableScopes()), config);

  return {
    engine,
    config,
    store,
    dbPath,
    cwd,
    activeScope,
    readableScopes,
    recall,
    close() {
      try {
        store.close();
      } catch { /* already closed */ }
    },
  };
}
