#!/usr/bin/env node
/**
 * dsh-ltm-mcp
 * -----------
 * A minimal MCP (stdio) bridge that exposes the seven @tr1v3r/dsh-ltm memory
 * tools to any MCP client (Pi, Cursor, Claude Code, ...).
 *
 * Design notes
 * ------------
 * - Zero framework dependencies: it speaks newline-delimited JSON-RPC 2.0
 *   directly, so `npm install` only pulls @tr1v3r/dsh-ltm (and its single
 *   transitive dep @deepseek-ai/schemastery).
 * - It reuses the *real* dsh-ltm engine (CJK tokenizer, BM25 + character
 *   n-gram rerank, near-duplicate detection, project scopes) via ./engine.mjs
 *   instead of reimplementing it.
 * - stdout is the JSON-RPC channel: logs go to stderr only.
 *
 * Environment
 * -----------
 *   DSH_LTM_DB             SQLite path (default: <PI_CODING_AGENT_DIR|~/.pi/agent>/memory/ltm.db, ":memory:" allowed)
 *   DSH_LTM_CWD            Project dir used for scope detection (default: process.cwd())
 *   DSH_LTM_DEFAULT_SCOPE  Fallback scope when project detection is disabled (default: "")
 *   DSH_LTM_AUTO_SCOPE     "0" disables auto project scope (default: enabled)
 */
import { openLtm } from "./engine.mjs";

const SERVER_NAME = "dsh-ltm";
const SERVER_VERSION = "0.1.0";
const PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"];

const log = (...parts) => process.stderr.write(`[dsh-ltm-mcp] ${parts.join(" ")}\n`);

// ---------------------------------------------------------------------------
// Open the store (same schema/engine as dsh-ltm, so a DB is shareable)
// ---------------------------------------------------------------------------
let ltm;
try {
  ltm = await openLtm();
} catch (err) {
  log(`FATAL: ${err?.message ?? err}`);
  process.exit(1);
}
const { config, store } = ltm;
const normalizeTags = ltm.engine.normalizeTags;

// ---------------------------------------------------------------------------
// Tool implementations (mirror dsh-ltm's own model tools)
// ---------------------------------------------------------------------------
function requireText(text, op) {
  const trimmed = String(text ?? "").trim();
  if (!trimmed) throw new Error(`${op}: text must not be blank`);
  if (trimmed.length > config.maxTextChars) {
    throw new Error(`${op}: text is ${trimmed.length} chars, over the ${config.maxTextChars} limit`);
  }
  return trimmed;
}
function clampLimit(limit, tool) {
  const requested = limit ?? config.searchLimitDefault;
  if (!Number.isInteger(requested) || requested < 1) {
    throw new Error(`${tool}: limit must be an integer >= 1 (got ${requested})`);
  }
  return Math.min(requested, config.searchLimitMax);
}
function tagList(tags) {
  return normalizeTags(Array.isArray(tags) ? tags : []).split(" ").filter((t) => t.length > 0);
}

const TOOLS = {
  memory_write(args) {
    const { record, dedupeHits } = store.write(requireText(args.text, "memory_write"), tagList(args.tags), {
      scope: ltm.activeScope(),
      pinned: args.pinned ?? false,
      force: args.force ?? false,
    });
    return { record, dedupeHits };
  },
  memory_search(args) {
    return {
      results: store.search(String(args.query ?? ""), clampLimit(args.limit, "memory_search"), ltm.readableScopes()),
    };
  },
  memory_forget(args) {
    return { deleted: store.forget(args.id, ltm.readableScopes()) };
  },
  memory_update(args) {
    const patch = {};
    if (args.text !== undefined) patch.text = requireText(args.text, "memory_update");
    if (args.tags !== undefined) patch.tags = tagList(args.tags);
    if (args.pinned !== undefined) patch.pinned = args.pinned;
    return { record: store.update(args.id, patch, ltm.readableScopes()) };
  },
  memory_confirm(args) {
    return { confirmed: store.confirm(args.id, ltm.readableScopes()) };
  },
  memory_list(args) {
    const filter = {};
    if (args.scope !== undefined) filter.scope = args.scope;
    if (args.tags !== undefined) filter.tags = args.tags;
    if (args.stale !== undefined) filter.stale = args.stale;
    if (args.limit !== undefined) filter.limit = clampLimit(args.limit, "memory_list");
    return { records: store.list(filter) };
  },
  memory_merge(args) {
    const input = { targetId: args.targetId, sourceIds: args.sourceIds };
    if (args.text !== undefined) input.text = args.text;
    if (args.tags !== undefined) input.tags = tagList(args.tags);
    return { record: store.merge(input, ltm.readableScopes()) };
  },
};

const strArray = { type: "array", items: { type: "string" } };
const TOOL_DEFS = [
  {
    name: "memory_write",
    description:
      "Store a durable, self-contained fact worth remembering across sessions (project convention, preference, decision, lesson). Near-duplicate detection runs first: matching candidates are returned instead of written unless force=true. Prefer memory_search when unsure, and memory_update when revising the same fact.",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string", description: "The self-contained fact to remember." },
        tags: { ...strArray, description: "Optional lowercase tags." },
        pinned: { type: "boolean", description: "Pinned records always render first in recall." },
        force: { type: "boolean", description: "Write even if near-duplicates exist." },
      },
      required: ["text"],
    },
  },
  {
    name: "memory_search",
    description:
      "Search stored memories in the current project plus global scope: CJK-aware tokenization followed by BM25 + character n-gram cosine reranking. Use before writing when the identity of a fact is unknown.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Keywords (Chinese/English both supported)." },
        limit: { type: "integer", description: "Max results (default 10, hard cap 50)." },
      },
      required: ["query"],
    },
  },
  {
    name: "memory_forget",
    description:
      "Delete one visible global/current-project memory by id, for a fact that is now wrong or obsolete. Ids come from memory_search or memory_write.",
    inputSchema: {
      type: "object",
      properties: { id: { type: "integer", description: "Memory id to delete." } },
      required: ["id"],
    },
  },
  {
    name: "memory_update",
    description:
      "Revise an existing memory in place, keeping its id: change text, tags, and/or pinned. Use this for a changed state of the same fact instead of writing a duplicate.",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "integer", description: "Memory id to update." },
        text: { type: "string", description: "New text." },
        tags: { ...strArray, description: "Replacement tags." },
        pinned: { type: "boolean", description: "New pinned state." },
      },
      required: ["id"],
    },
  },
  {
    name: "memory_confirm",
    description:
      'Refresh the review timestamp of a memory to clear its stale status. Pass an integer id, or "*" to confirm every visible memory.',
    inputSchema: {
      type: "object",
      properties: {
        id: { anyOf: [{ type: "integer" }, { type: "string", enum: ["*"] }], description: 'Memory id, or "*" for all visible memories.' },
      },
      required: ["id"],
    },
  },
  {
    name: "memory_list",
    description:
      "Browse memories with filters (tags are AND, stale filter, limit). Explicit cross-project aggregation surface; use memory_search for lookups.",
    inputSchema: {
      type: "object",
      properties: {
        scope: { type: "string", description: 'Scope bucket; "" = global.' },
        tags: { ...strArray, description: "Require all of these tags." },
        stale: { type: "boolean", description: "Only stale (true) or only fresh (false) records." },
        limit: { type: "integer", description: "Max records." },
      },
    },
  },
  {
    name: "memory_merge",
    description:
      "Merge duplicate memories into a target id: sourceIds are absorbed and deleted, optional text/tags override the result, and tags default to the union. Merge never crosses scope boundaries.",
    inputSchema: {
      type: "object",
      properties: {
        targetId: { type: "integer", description: "Record that survives." },
        sourceIds: { type: "array", items: { type: "integer" }, description: "Records to absorb." },
        text: { type: "string", description: "Optional merged text." },
        tags: { ...strArray, description: "Optional merged tags (default: union)." },
      },
      required: ["targetId", "sourceIds"],
    },
  },
];

const INSTRUCTIONS =
  `Long-term memory store (dsh-ltm, ${SERVER_VERSION}). Durable facts persist across sessions, separated by project scope. ` +
  "Search before writing when a fact's identity is unknown; use memory_update to revise the same fact instead of duplicating; " +
  "ids come from memory_search / memory_write. Near-duplicate writes are rejected unless force=true.";

// ---------------------------------------------------------------------------
// Minimal MCP stdio server (newline-delimited JSON-RPC 2.0)
// ---------------------------------------------------------------------------
function send(message) {
  process.stdout.write(JSON.stringify(message) + "\n");
}
function reply(id, result) {
  send({ jsonrpc: "2.0", id, result });
}
function replyError(id, code, message) {
  send({ jsonrpc: "2.0", id, error: { code, message } });
}

function handle(message) {
  const { id, method, params } = message;
  const isNotification = id === undefined || id === null;

  switch (method) {
    case "initialize": {
      const requested = params?.protocolVersion;
      reply(id, {
        protocolVersion: PROTOCOL_VERSIONS.includes(requested) ? requested : PROTOCOL_VERSIONS[0],
        capabilities: { tools: {} },
        serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
        instructions: INSTRUCTIONS,
      });
      return;
    }
    case "notifications/initialized":
    case "notifications/cancelled":
    case "notifications/roots/list_changed":
      return; // notifications never get a response
    case "ping":
      if (!isNotification) reply(id, {});
      return;
    case "tools/list":
      reply(id, { tools: TOOL_DEFS });
      return;
    case "resources/list":
      reply(id, { resources: [] });
      return;
    case "resources/templates/list":
      reply(id, { resourceTemplates: [] });
      return;
    case "prompts/list":
      reply(id, { prompts: [] });
      return;
    case "tools/call": {
      const name = params?.name;
      const args = params?.arguments ?? {};
      const fn = TOOLS[name];
      if (!fn) {
        replyError(id, -32601, `Unknown tool: ${name}`);
        return;
      }
      try {
        const out = fn(args);
        reply(id, { content: [{ type: "text", text: JSON.stringify(out, null, 2) }] });
      } catch (err) {
        reply(id, { content: [{ type: "text", text: String(err?.message ?? err) }], isError: true });
      }
      return;
    }
    default:
      if (!isNotification) replyError(id, -32601, `Method not found: ${method}`);
  }
}

let buffer = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buffer += chunk;
  let newline;
  while ((newline = buffer.indexOf("\n")) >= 0) {
    const line = buffer.slice(0, newline).trim();
    buffer = buffer.slice(newline + 1);
    if (!line) continue;
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      log(`ignoring non-JSON line: ${line.slice(0, 120)}`);
      continue;
    }
    try {
      handle(message);
    } catch (err) {
      if (message?.id !== undefined && message?.id !== null) {
        replyError(message.id, -32603, String(err?.message ?? err));
      } else {
        log(`handler error: ${err?.stack ?? err}`);
      }
    }
  }
});

function shutdown() {
  ltm?.close();
  process.exit(0);
}
process.stdin.on("end", shutdown);
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
