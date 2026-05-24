/**
 * NERV custom tools for OpenCode.
 *
 * These tools communicate with NERV MCP servers via HTTP, bypassing the
 * MCP subprocess round-trip for faster LLM tool calls.
 *
 * All tools have a 1s hard timeout and return structured JSON on failure.
 *
 * Uses @opencode-ai/plugin tool() helper to avoid Zod version conflicts.
 */

import { tool } from "@opencode-ai/plugin";

// ──────────────────────────────────────────────
// Internal: call nerv-memory MCP via HTTP POST
// ──────────────────────────────────────────────
const MEMORY_MCP_URL = "http://127.0.0.1:19821";

async function memoryRpc(method: string, params: Record<string, unknown> = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1000);

  try {
    const res = await fetch(`${MEMORY_MCP_URL}/rpc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now(),
        method,
        params,
      }),
      signal: controller.signal,
    });

    if (!res.ok) {
      return { error: `HTTP ${res.status}: ${res.statusText}` };
    }

    const data = await res.json();
    if (data.error) {
      return { error: data.error.message ?? String(data.error) };
    }
    return data.result;
  } catch (err: any) {
    if (err.name === "AbortError") return { error: "timeout" };
    return { error: err.message ?? "unavailable" };
  } finally {
    clearTimeout(timeout);
  }
}

// ──────────────────────────────────────────────
// Internal: call nerv-hub MCP via HTTP POST
// ──────────────────────────────────────────────
const HUB_MCP_URL = "http://127.0.0.1:19820";

async function hubRpc(method: string, params: Record<string, unknown> = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1000);

  try {
    const res = await fetch(`${HUB_MCP_URL}/rpc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now(),
        method,
        params,
      }),
      signal: controller.signal,
    });

    if (!res.ok) {
      return { error: `HTTP ${res.status}: ${res.statusText}` };
    }

    const data = await res.json();
    if (data.error) {
      return { error: data.error.message ?? String(data.error) };
    }
    return data.result;
  } catch (err: any) {
    if (err.name === "AbortError") return { error: "timeout" };
    return { error: err.message ?? "unavailable" };
  } finally {
    clearTimeout(timeout);
  }
}

// ──────────────────────────────────────────────
// Tools
// ──────────────────────────────────────────────

export const nerv_memory_stats = tool({
  description: "Return aggregate counts for active memories in NERV memory store.",
  args: {},
  async execute() {
    const result = await memoryRpc("memory_stats", {});
    if (result.error) {
      return JSON.stringify({ error: "memory_stats unavailable", detail: result.error });
    }
    return JSON.stringify(result);
  },
});

export const nerv_task_status = tool({
  description: "Get the current state of an A2A hub task by its ID.",
  args: {
    task_id: tool.schema.string().describe("The task ID to look up"),
  },
  async execute(args) {
    const result = await hubRpc("get_task", { task_id: args.task_id });
    if (result.error) {
      return JSON.stringify({ error: "task_status unavailable", detail: result.error });
    }
    return JSON.stringify(result);
  },
});

export const nerv_hub_health = tool({
  description: "Check whether the NERV A2A hub is reachable and healthy.",
  args: {},
  async execute() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1000);

    try {
      const res = await fetch("http://127.0.0.1:19820/health", {
        signal: controller.signal,
      });
      if (!res.ok) {
        return JSON.stringify({ connected: false, status: res.status });
      }
      const data = await res.json();
      return JSON.stringify({ connected: true, ...data });
    } catch {
      return JSON.stringify({ connected: false });
    } finally {
      clearTimeout(timeout);
    }
  },
});

export const nerv_check_pending_tasks = tool({
  description:
    "List all pending tasks assigned to an agent. Falls back to NERV_AGENT_SOURCE env var if agent_id omitted.",
  args: {
    agent_id: tool.schema
      .string()
      .optional()
      .describe("The agent ID to check. If omitted, uses NERV_AGENT_SOURCE from environment."),
  },
  async execute(args) {
    const agentId = args.agent_id ?? process.env.NERV_AGENT_SOURCE ?? "unknown";
    const result = await hubRpc("list_pending_tasks", { agent_id: agentId });
    if (result.error) {
      return JSON.stringify({ error: "check_pending_tasks unavailable", detail: result.error });
    }
    return JSON.stringify(result);
  },
});