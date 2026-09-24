/**
 * dsh-ltm auto-recall extension for Pi.
 *
 * Mirrors DSH's `ltm:recall` prompt section: on every agent start it renders the
 * bounded pinned/recent memory section and attaches it to Pi's system prompt as
 * a named section. Pi diffs sections between turns, so only a changed section is
 * re-sent as a transcript delta (prefix-cache friendly) instead of replacing the
 * whole prompt.
 *
 * Loaded by run_pi.ps1 via `pi --extension <this file>`. It shares the SQLite
 * store and the engine with the dsh-ltm MCP bridge (see ./engine.mjs).
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
// Plain-ESM engine shared with mcp-server.mjs (jiti loads it at runtime).
import { openLtm } from "./engine.mjs";

type Ltm = Awaited<ReturnType<typeof openLtm>>;

const SECTION_NAME = "ltm_memory";

export default function dshLtmRecall(pi: ExtensionAPI) {
  let ltm: Ltm | undefined;
  let opening: Promise<Ltm> | undefined;

  async function ensureLtm(cwd: string): Promise<Ltm> {
    if (ltm) return ltm;
    if (!opening) {
      opening = openLtm({ cwd })
        .then((instance) => {
          ltm = instance;
          return instance;
        })
        .finally(() => {
          opening = undefined;
        });
    }
    return opening;
  }

  pi.on("before_agent_start", async (event, ctx) => {
    try {
      const instance = await ensureLtm(ctx.cwd);
      const text = instance.recall();
      if (text) {
        event.systemPromptOptions.sections[SECTION_NAME] = text;
      }
    } catch (err) {
      // Recall is best-effort: never block a run because memory is unavailable.
      const message = err instanceof Error ? err.message : String(err);
      process.stderr.write(`[dsh-ltm-recall] ${message}\n`);
    }
  });

  pi.on("session_shutdown", async () => {
    ltm?.close();
    ltm = undefined;
  });
}
