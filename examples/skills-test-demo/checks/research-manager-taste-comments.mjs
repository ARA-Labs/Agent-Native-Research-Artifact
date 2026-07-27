#!/usr/bin/env node
// Supporting, mechanical check for ONE part of a much bigger human-reviewed artifact: the
// shape of research-manager's taste-comment writes within examples/skills-test-demo/ara/.
// The primary judgment on a trajectory replay (prompts/research-manager-trajectory.md) is a
// human reading the resulting ara/ and deciding whether the routing/staging/crystallization
// decisions look right — that's not something a script can assert. What this script CAN
// assert is the taste-comment shape specifically: does it diff cleanly against a git ref (the
// living ARA evolves via commits, so "before" is git history, not a hand-maintained second
// copy) without breaking append-only-ness, valid tag enums, or trace-node immutability.
// No dependencies — the parsing below only needs to handle the specific shapes
// taste-comments.md defines, not general YAML/Markdown.
//
// One of possibly several checks/*.mjs files sharing the same ara/ — each one validates a
// different ARA-skill capability's effect on it. This one is research-manager's
// taste-comments only; a skill that only reads ara/ (rigor-reviewer, research-visualizer,
// research-foresight) would need a check shape that validates its output instead of diffing
// ara/, and compiler doesn't fit this shared-ara/ pattern at all (it builds an ARA from a
// paper/repo rather than editing an existing one) — see the repo's top-level README.
//
// Usage: node checks/research-manager-taste-comments.mjs [araDir] [gitRef]
// Defaults to ../ara (this demo) and origin/main.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const araDir = path.resolve(process.argv[2] ?? path.join(HERE, '..', 'ara'));
const gitRef = process.argv[3] ?? 'origin/main';

const ATTITUDE_TAGS = new Set(['endorse', 'uncertain', 'reject']);
const OBJECT_TAGS = new Set(['claim', 'evidence', 'framing', 'priority']);

const failures = [];
const fail = (msg) => failures.push(msg);
const pass = (msg) => console.log(`  ok — ${msg}`);

let repoRoot = null;
try {
  repoRoot = execFileSync('git', ['rev-parse', '--show-toplevel'], { cwd: araDir, encoding: 'utf8' }).trim();
} catch {
  console.warn('warning: not inside a git checkout — skipping before/after diff checks, running static checks only.');
}

function readCurrent(relPath) {
  const p = path.join(araDir, relPath);
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : null;
}

function readAtRef(relPath) {
  if (!repoRoot) return null;
  const araRelToRepo = path.relative(repoRoot, araDir);
  const gitPath = path.join(araRelToRepo, relPath).split(path.sep).join('/');
  try {
    return execFileSync('git', ['show', `${gitRef}:${gitPath}`], {
      cwd: repoRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    });
  } catch {
    return null; // file didn't exist at that ref — legitimate for a first write.
  }
}

// --- Markdown entry parsing (claims.md / heuristics.md) -------------------------

function parseMarkdownEntries(text) {
  if (text === null) return new Map();
  const lines = text.split('\n');
  const entries = new Map();
  let currentId = null;
  let currentLines = [];
  const flush = () => {
    if (currentId) entries.set(currentId, currentLines.join('\n'));
  };
  for (const line of lines) {
    const m = line.match(/^## ([A-Z]\d+):/);
    if (m) {
      flush();
      currentId = m[1];
      currentLines = [line];
    } else if (currentId) {
      currentLines.push(line);
    }
  }
  flush();
  return entries;
}

function splitTaste(body) {
  const lines = body.split('\n');
  const tasteHeaderIdx = lines.findIndex((l) => l.trim().startsWith('- **Taste**'));
  if (tasteHeaderIdx === -1) return { core: body.replace(/\s+$/, ''), tasteBullets: [] };
  const core = lines.slice(0, tasteHeaderIdx).join('\n').replace(/\s+$/, '');
  const tasteBullets = [];
  for (let i = tasteHeaderIdx + 1; i < lines.length; i++) {
    const l = lines[i];
    if (/^\s{2,}- \[/.test(l)) tasteBullets.push(l.trim());
    else if (l.trim() === '') continue;
    else break;
  }
  return { core, tasteBullets };
}

const TASTE_BULLET_RE = /^- \[(\d{4}-\d{2}-\d{2})\] `([a-z]+)` on `([a-z]+)` — (.+)$/;

function checkMarkdownFile(label, relPath) {
  console.log(`\n${label}`);
  const beforeEntries = parseMarkdownEntries(readAtRef(relPath));
  const afterEntries = parseMarkdownEntries(readCurrent(relPath));

  for (const [id, beforeBody] of beforeEntries) {
    const afterBody = afterEntries.get(id);
    if (afterBody === undefined) {
      fail(`${label}: entry ${id} present at ${gitRef} is missing now`);
      continue;
    }
    const beforeSplit = splitTaste(beforeBody);
    const afterSplit = splitTaste(afterBody);
    if (beforeSplit.core !== afterSplit.core) {
      fail(`${label}: entry ${id} changed outside its Taste subsection — taste writes must not touch other fields`);
    } else {
      pass(`${id}: non-Taste fields unchanged since ${gitRef}`);
    }
    for (let i = 0; i < beforeSplit.tasteBullets.length; i++) {
      if (afterSplit.tasteBullets[i] !== beforeSplit.tasteBullets[i]) {
        fail(`${label}: entry ${id} lost or rewrote a prior taste bullet at position ${i} — taste is append-only`);
      }
    }
  }

  if (afterEntries.size === 0) {
    console.log('  (no entries found)');
  }
  for (const [id, afterBody] of afterEntries) {
    const { tasteBullets } = splitTaste(afterBody);
    for (const bullet of tasteBullets) {
      const m = bullet.match(TASTE_BULLET_RE);
      if (!m) {
        fail(`${label}: entry ${id} has a malformed taste bullet: "${bullet}"`);
        continue;
      }
      const [, , attitude, object] = m;
      if (!ATTITUDE_TAGS.has(attitude)) fail(`${label}: entry ${id} taste bullet has invalid attitude tag "${attitude}"`);
      if (!OBJECT_TAGS.has(object)) fail(`${label}: entry ${id} taste bullet has invalid object tag "${object}"`);
      if (ATTITUDE_TAGS.has(attitude) && OBJECT_TAGS.has(object)) {
        pass(`${id} taste bullet: \`${attitude}\` on \`${object}\` — valid`);
      }
    }
  }
}

// --- exploration_tree.yaml parsing (top-level nodes only) -----------------------

function parseTreeNodes(text) {
  if (text === null) return new Map();
  const lines = text.split('\n');
  const nodes = new Map();
  let currentId = null;
  let currentLines = [];
  const flush = () => {
    if (currentId) nodes.set(currentId, currentLines.join('\n').replace(/\n+$/, ''));
  };
  for (const line of lines) {
    const m = line.match(/^ {2}- id: (N\d+)/);
    if (m) {
      flush();
      currentId = m[1];
      currentLines = [line];
    } else if (currentId) {
      currentLines.push(line);
    }
  }
  flush();
  return nodes;
}

function checkExplorationTree(relPath) {
  console.log('\ntrace/exploration_tree.yaml');
  const beforeNodes = parseTreeNodes(readAtRef(relPath));
  const afterNodes = parseTreeNodes(readCurrent(relPath));

  for (const [id, beforeBlock] of beforeNodes) {
    const afterBlock = afterNodes.get(id);
    if (afterBlock === undefined) {
      fail(`trace/exploration_tree.yaml: node ${id} present at ${gitRef} is missing now`);
    } else if (afterBlock !== beforeBlock) {
      fail(`trace/exploration_tree.yaml: node ${id} was mutated — trace nodes must never be edited, only pointed at`);
    } else {
      pass(`node ${id}: byte-identical since ${gitRef} (never edited)`);
    }
  }
  const newIds = [...afterNodes.keys()].filter((id) => !beforeNodes.has(id));
  if (newIds.length > 0) pass(`new node(s) appended since ${gitRef}: ${newIds.join(', ')}`);
  return new Set(afterNodes.keys());
}

// --- taste_log.yaml parsing ------------------------------------------------------

function parseTasteLog(text) {
  if (text === null) return [];
  const lines = text.split('\n');
  const entries = [];
  let current = null;
  for (const line of lines) {
    const idMatch = line.match(/^ {2}- id: (T\d+)/);
    if (idMatch) {
      if (current) entries.push(current);
      current = { id: idMatch[1] };
      continue;
    }
    if (!current) continue;
    const field = line.match(/^ {4}(\w+): (.*)$/);
    if (field) current[field[1]] = field[2].replace(/^"|"$/g, '');
  }
  if (current) entries.push(current);
  return entries;
}

function checkTasteLog(relPath, validNodeIds) {
  console.log('\ntrace/taste_log.yaml');
  const beforeEntries = parseTasteLog(readAtRef(relPath));
  const entries = parseTasteLog(readCurrent(relPath));
  if (entries.length === 0) {
    pass('no entries (file absent or empty) — nothing to check');
    return;
  }

  const beforeById = new Map(beforeEntries.map((e) => [e.id, e]));
  const afterById = new Map(entries.map((e) => [e.id, e]));
  for (const [id, beforeEntry] of beforeById) {
    const afterEntry = afterById.get(id);
    if (!afterEntry) {
      fail(`taste_log.yaml: entry ${id} present at ${gitRef} is missing now`);
    } else if (JSON.stringify(afterEntry) !== JSON.stringify(beforeEntry)) {
      fail(`taste_log.yaml: entry ${id} was mutated — taste_log entries must never be edited once written, only appended`);
    } else {
      pass(`${id}: unchanged since ${gitRef}`);
    }
  }

  const seenNums = [];
  for (const e of entries) {
    const numMatch = e.id.match(/^T(\d+)$/);
    if (!numMatch) {
      fail(`taste_log.yaml: entry id "${e.id}" doesn't match T{XX}`);
    } else {
      seenNums.push(Number(numMatch[1]));
    }

    if (!ATTITUDE_TAGS.has(e.tag)) fail(`taste_log.yaml: ${e.id} has invalid tag "${e.tag}"`);
    if (!OBJECT_TAGS.has(e.object)) fail(`taste_log.yaml: ${e.id} has invalid object "${e.object}"`);
    if (!e.target || !validNodeIds.has(e.target)) {
      fail(`taste_log.yaml: ${e.id} targets "${e.target}", which does not resolve to a real node in trace/exploration_tree.yaml`);
    } else {
      pass(`${e.id}: target ${e.target} resolves; tag=${e.tag} object=${e.object}`);
    }
  }

  const uniqueNums = new Set(seenNums);
  if (uniqueNums.size !== seenNums.length) fail('taste_log.yaml: T ids are not unique');
  const sorted = [...uniqueNums].sort((a, b) => a - b);
  const expected = sorted.map((_, i) => i + 1);
  if (JSON.stringify(sorted) !== JSON.stringify(expected)) {
    fail(`taste_log.yaml: T ids are not sequential starting at 1 (got T${sorted.join(', T')})`);
  } else {
    pass('T ids unique and sequential');
  }
}

// --- run ---------------------------------------------------------------------

console.log(`ara dir: ${araDir}`);
console.log(`diffing against: ${repoRoot ? gitRef : '(no git — static checks only)'}`);

checkMarkdownFile('logic/claims.md', 'logic/claims.md');
checkMarkdownFile('logic/solution/heuristics.md', 'logic/solution/heuristics.md');
const validNodeIds = checkExplorationTree('trace/exploration_tree.yaml');
checkTasteLog('trace/taste_log.yaml', validNodeIds);

console.log('');
if (failures.length > 0) {
  console.error(`FAILED — ${failures.length} invariant violation(s):`);
  for (const f of failures) console.error(`  ✗ ${f}`);
  process.exit(1);
} else {
  console.log('PASSED — all taste-comment invariants hold.');
  process.exit(0);
}
