#!/usr/bin/env node
/**
 * npx wrapper: spawn uvx/pipx ontosight-codegraph after verifying CodeGraph index.
 */
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const INIT_CMD = "npx @colbymchenry/codegraph init -i";
const INIT_HINT = `Run: ${INIT_CMD}`;
const FLAG_WITH_VALUE = new Set(["--path", "--symbol", "--task", "--hops", "--max-nodes"]);

const __dirname = dirname(fileURLToPath(import.meta.url));

function readPinnedVersion() {
  if (process.env.ONTOSIGHT_CODEGRAPH_VERSION) {
    return process.env.ONTOSIGHT_CODEGRAPH_VERSION;
  }
  try {
    const pkg = JSON.parse(
      readFileSync(join(__dirname, "..", "package.json"), "utf8"),
    );
    return pkg.ontosightCodegraphVersion || "0.1.0";
  } catch {
    return "0.1.0";
  }
}

function printHelp() {
  console.log(`Usage: npx @royalsolution/ontosight [project-path] [options]

Visualize a CodeGraph call subgraph in OntoSight.

Prerequisites:
  - Python 3.11+ with uv (https://docs.astral.sh/uv/) or pipx
  - CodeGraph index (auto-created via ${INIT_CMD} when missing)

Options:
  --path <prefix>     Limit symbols to files under this path
  --symbol <name>     Seed symbol for subgraph expansion
  --task <text>       Natural-language task seed
  --hops <n>          BFS hop depth (default: 2)
  --max-nodes <n>     Maximum nodes (default: 200)
  -h, --help          Show this help
  -V, --version       Show npm package version

Examples:
  npx @royalsolution/ontosight .
  npx @royalsolution/ontosight . --symbol view_graph --path vendor/ontosight/
`);
}

function printVersion() {
  try {
    const pkg = JSON.parse(
      readFileSync(join(__dirname, "..", "package.json"), "utf8"),
    );
    console.log(pkg.version);
  } catch {
    console.log("0.1.0");
  }
}

function parseArgs(argv) {
  const passthrough = [];
  let projectPath = ".";
  let sawPath = false;

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") {
      return { help: true };
    }
    if (arg === "-V" || arg === "--version") {
      return { version: true };
    }
    if (arg.startsWith("-")) {
      passthrough.push(arg);
      if (FLAG_WITH_VALUE.has(arg)) {
        const value = argv[i + 1];
        if (value === undefined || value.startsWith("-")) {
          console.error(`Error: ${arg} requires a value`);
          process.exit(1);
        }
        passthrough.push(value);
        i += 1;
      }
      continue;
    }
    if (!sawPath) {
      projectPath = arg;
      sawPath = true;
    } else {
      passthrough.push(arg);
    }
  }

  return { projectPath, passthrough };
}

function commandExists(cmd) {
  const probe =
    process.platform === "win32" ? "where" : "command";
  const args =
    process.platform === "win32" ? [cmd] : ["-v", cmd];
  const result = spawnSync(probe, args, { stdio: "ignore", shell: false });
  return result.status === 0;
}

function run(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, {
    stdio: "inherit",
    shell: false,
    env: process.env,
    ...options,
  });
  if (result.error) {
    return { ok: false, error: result.error };
  }
  return { ok: true, status: result.status ?? 1 };
}

function ensureCodegraphIndex(root, dbPath) {
  if (existsSync(dbPath)) {
    return;
  }

  if (process.env.ONTOSIGHT_SKIP_AUTO_INIT === "1") {
    console.error(
      `Error: CodeGraph index not found at ${dbPath}. ${INIT_HINT}`,
    );
    process.exit(1);
  }

  console.log(`CodeGraph index not found. Running: ${INIT_CMD}`);
  const initResult = run(
    "npx",
    ["@colbymchenry/codegraph", "init", "-i"],
    { cwd: root },
  );

  if (!initResult.ok) {
    console.error(
      `Error: Failed to run CodeGraph init (${initResult.error?.message ?? "unknown error"}). ${INIT_HINT}`,
    );
    process.exit(1);
  }

  if (initResult.status !== 0) {
    process.exit(initResult.status);
  }

  if (!existsSync(dbPath)) {
    console.error(
      `Error: CodeGraph init completed but index not found at ${dbPath}. ${INIT_HINT}`,
    );
    process.exit(1);
  }
}

function main() {
  const parsed = parseArgs(process.argv.slice(2));
  if (parsed.help) {
    printHelp();
    return;
  }
  if (parsed.version) {
    printVersion();
    return;
  }

  const { projectPath, passthrough } = parsed;
  const root = resolve(process.cwd(), projectPath);
  const dbPath = join(root, ".codegraph", "codegraph.db");

  ensureCodegraphIndex(root, dbPath);

  const pyVersion = readPinnedVersion();
  const uvxArgs = [`ontosight-codegraph@${pyVersion}`, projectPath, ...passthrough];

  if (commandExists("uvx")) {
    const result = run("uvx", uvxArgs);
    if (result.ok) {
      process.exit(result.status);
    }
  }

  if (commandExists("pipx")) {
    const pipxArgs = [
      "run",
      "--spec",
      `ontosight-codegraph==${pyVersion}`,
      "ontosight-codegraph",
      projectPath,
      ...passthrough,
    ];
    const result = run("pipx", pipxArgs);
    if (result.ok) {
      process.exit(result.status);
    }
  }

  console.error(
    "Error: Neither uv nor pipx found on PATH.\n\n" +
      "Install uv (recommended): curl -LsSf https://astral.sh/uv/install.sh | sh\n" +
      "Or install pipx: https://pipx.pypa.io/stable/installation/",
  );
  process.exit(1);
}

main();
