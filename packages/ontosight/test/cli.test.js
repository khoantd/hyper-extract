import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import test from "node:test";

const binPath = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "bin",
  "ontosight.js",
);

function run(args, { cwd, env } = {}) {
  return spawnSync(process.execPath, [binPath, ...args], {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      PATH: "",
      ...env,
    },
  });
}

test("shows help", () => {
  const result = run(["--help"], {
    env: { PATH: process.env.PATH ?? "" },
  });
  assert.equal(result.status, 0);
  assert.match(result.stdout, /--symbol/);
  assert.match(result.stdout, /auto-created/);
});

test("shows version", () => {
  const result = run(["--version"], {
    env: { PATH: process.env.PATH ?? "" },
  });
  assert.equal(result.status, 0);
  assert.match(result.stdout.trim(), /^\d+\.\d+\.\d+$/);
});

test("missing index with skip flag exits with init hint", () => {
  const dir = mkdtempSync(join(tmpdir(), "ontosight-cli-"));
  const result = run(["."], {
    cwd: dir,
    env: { ONTOSIGHT_SKIP_AUTO_INIT: "1" },
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /init -i/);
  assert.doesNotMatch(result.stderr, /Running:/);
});

test("missing index attempts auto init", () => {
  const dir = mkdtempSync(join(tmpdir(), "ontosight-cli-"));
  const result = run(["."], { cwd: dir });
  const output = `${result.stdout}${result.stderr}`;
  assert.notEqual(result.status, 0);
  assert.match(
    output,
    /Running: npx @colbymchenry\/codegraph init -i|Failed to run CodeGraph init/,
  );
  assert.doesNotMatch(output, /ONTOSIGHT_SKIP_AUTO_INIT/);
});

test("existing empty db file passes index check before python runner", () => {
  const dir = mkdtempSync(join(tmpdir(), "ontosight-cli-"));
  const cgDir = join(dir, ".codegraph");
  mkdirSync(cgDir, { recursive: true });
  writeFileSync(join(cgDir, "codegraph.db"), "");
  const result = run(["."], { cwd: dir });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Neither uv nor pipx found/);
  assert.doesNotMatch(result.stderr, /Running:/);
});
