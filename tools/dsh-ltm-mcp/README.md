# dsh-ltm-mcp

A minimal [MCP](https://modelcontextprotocol.io) (stdio) bridge that exposes the
seven [`@tr1v3r/dsh-ltm`](https://www.npmjs.com/package/@tr1v3r/dsh-ltm) memory
tools to any MCP client — Pi, Cursor, Claude Code, and friends.

It reuses the **real** dsh-ltm engine (CJK-aware tokenization, BM25 + character
n-gram rerank, near-duplicate detection, project scopes) instead of
reimplementing it, so memories stored here are schema-compatible with a DSH
profile that uses dsh-ltm.

## Tools

| Tool | Purpose |
|---|---|
| `memory_write(text, tags?, pinned?, force?)` | Store a durable fact (dedupe-checked) |
| `memory_search(query, limit?)` | CJK-aware hybrid search |
| `memory_forget(id)` | Delete one visible record |
| `memory_update(id, text?, tags?, pinned?)` | Revise in place, keeps the id |
| `memory_confirm(id \| "*")` | Refresh review timestamp / clear stale |
| `memory_list(scope?, tags?, stale?, limit?)` | Filtered browse (cross-project) |
| `memory_merge(targetId, sourceIds[], text?, tags?)` | Merge duplicates |

## How it plugs into Pi

`run_pi.ps1` handles everything on a fresh machine:

1. Locates this directory (`tools/dsh-ltm-mcp`) next to the script.
2. Runs `npm install` here when `node_modules/@tr1v3r/dsh-ltm` is missing.
3. Registers the `dsh-ltm` MCP server in `~/.pi/agent/mcp.json`
   (`node mcp-server.mjs`, with `DSH_LTM_DB=<pi agent>/memory/ltm.db`).

Restart the profile after the first install.

## Auto-recall (Pi extension)

`dsh-ltm-recall.ts` mirrors DSH's `ltm:recall` prompt section: on each agent
start it renders the bounded pinned/recent memory section and attaches it to
Pi's system prompt as the `ltm_memory` section. Pi diffs sections between turns,
so only a changed section is re-sent as a transcript delta (prefix-cache
friendly) instead of replacing the whole prompt. `run_pi.ps1` loads it with
`pi --extension`.

The extension shares `engine.mjs` and the same SQLite store as the MCP server, so
what the tools write shows up in recall automatically.

## Run it manually

```sh
npm install
DSH_LTM_DB="$HOME/.pi/agent/memory/ltm.db" node mcp-server.mjs
```

Point any MCP client at `node <abs>/tools/dsh-ltm-mcp/mcp-server.mjs`.

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `DSH_LTM_DB` | `<PI_CODING_AGENT_DIR\|~/.pi/agent>/memory/ltm.db` | SQLite file (`:memory:` allowed) |
| `DSH_LTM_CWD` | `process.cwd()` | Project dir used for scope detection |
| `DSH_LTM_DEFAULT_SCOPE` | `""` (global) | Fallback scope when auto-detection is off |
| `DSH_LTM_AUTO_SCOPE` | enabled | `0` disables automatic project scope |

## Notes

- **Zero framework deps**: it speaks newline-delimited JSON-RPC 2.0 directly and
  installs only `@tr1v3r/dsh-ltm` (+ `@deepseek-ai/schemastery`). The DSH/Cordis
  peer deps are deliberately skipped (see `.npmrc`) because this bridge imports
  the engine chunk, not the Cordis plugin.
- **Version-resilient engine loading**: dsh-ltm bundles its engine as a hashed
  chunk (`dist/scope-*.js`) with minified export aliases. The bridge discovers
  the chunk and parses its `export { real as alias }` map at runtime, so it keeps
  working across dsh-ltm patch/minor releases.
- **stdout is the protocol channel**; all diagnostics go to stderr.
- The MCP server exposes the tools; the Pi extension (`dsh-ltm-recall.ts`) adds
  automatic prompt recall. The server also returns an `instructions` hint at
  `initialize` telling the model how to behave.
