#!/usr/bin/env node
// Validates the structural invariants a taste-comment write must never break, by
// diffing a "before" ARA snapshot against an "after" snapshot (same layout as
// research-manager would produce). No dependencies — the parsing below only needs
// to handle the specific shapes taste-comments.md defines, not general YAML/Markdown.
//
// Usage: node check.mjs [beforeDir] [afterDir]
// Defaults to ./before and ./after (this fixture).

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const beforeDir = path.resolve(process.argv[2] ?? path.join(HERE, 'before'));
const afterDir = path.resolve(process.argv[3] ?? path.join(HERE, 'after'));

const ATTITUDE_TAGS = new Set(['endorse', 'uncertain', 'reject']);
const OBJECT_TAGS = new Set(['claim', 'evidence', 'framing', 'priority']);

const failures = [];
const fail = (msg) => failures.push(msg);
const pass = (msg) => console.log(`  ok — ${msg}`);

function readIfExists(p) {
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : null;
}

// --- Markdown entry parsing (claims.md / heuristics.md) -------------------------

// Splits a claims.md/heuristics.md file into { id -> { header, body } } blocks,
// where body is the raw text of the entry after its `## ID: title` header line.
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

// Splits an entry body into { core, tasteBullets } — core is everything except
// the "- **Taste** (optional):" subsection and its bullets; tasteBullets is the
// raw bullet lines (in order) under it, if present.
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

const TASTE_BULLET_RE =
  /^- \[(\d{4}-\d{2}-\d{2})\] `([a-z]+)` on `([a-z]+)` — (.+)$/;

function checkMarkdownFile(label, beforePath, afterPath) {
  console.log(`\n${label}`);
  const beforeEntries = parseMarkdownEntries(readIfExists(beforePath));
  const afterEntries = parseMarkdownEntries(readIfExists(afterPath));

  for (const [id, beforeBody] of beforeEntries) {
    const afterBody = afterEntries.get(id);
    if (afterBody === undefined) {
      fail(`${label}: entry ${id} present in before/ is missing from after/`);
      continue;
    }
    const beforeSplit = splitTaste(beforeBody);
    const afterSplit = splitTaste(afterBody);
    if (beforeSplit.core !== afterSplit.core) {
      fail(`${label}: entry ${id} changed outside its Taste subsection — taste writes must not touch other fields`);
    } else {
      pass(`${id}: non-Taste fields unchanged`);
    }
    for (let i = 0; i < beforeSplit.tasteBullets.length; i++) {
      if (afterSplit.tasteBullets[i] !== beforeSplit.tasteBullets[i]) {
        fail(`${label}: entry ${id} lost or rewrote a prior taste bullet at position ${i} — taste is append-only`);
      }
    }
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
      if (!ATTITUDE_TAGS.has(attitude)) {
        fail(`${label}: entry ${id} taste bullet has invalid attitude tag "${attitude}"`);
      }
      if (!OBJECT_TAGS.has(object)) {
        fail(`${label}: entry ${id} taste bullet has invalid object tag "${object}"`);
      }
      if (ATTITUDE_TAGS.has(attitude) && OBJECT_TAGS.has(object)) {
        pass(`${id} taste bullet: \`${attitude}\` on \`${object}\` — valid`);
      }
    }
  }
}

// --- exploration_tree.yaml parsing (top-level nodes only) -----------------------

// Splits the tree into { id -> raw block text } for top-level `  - id: N{XX}` nodes.
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

function checkExplorationTree(beforePath, afterPath) {
  console.log('\ntrace/exploration_tree.yaml');
  const beforeNodes = parseTreeNodes(readIfExists(beforePath));
  const afterNodes = parseTreeNodes(readIfExists(afterPath));

  for (const [id, beforeBlock] of beforeNodes) {
    const afterBlock = afterNodes.get(id);
    if (afterBlock === undefined) {
      fail(`trace/exploration_tree.yaml: node ${id} present in before/ is missing from after/`);
    } else if (afterBlock !== beforeBlock) {
      fail(`trace/exploration_tree.yaml: node ${id} was mutated — trace nodes must never be edited, only pointed at`);
    } else {
      pass(`node ${id}: byte-identical (never edited)`);
    }
  }
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

function checkTasteLog(afterPath, validNodeIds) {
  console.log('\ntrace/taste_log.yaml');
  const entries = parseTasteLog(readIfExists(afterPath));
  if (entries.length === 0) {
    pass('no entries (file absent or empty) — nothing to check');
    return;
  }

  const seenNums = [];
  for (const e of entries) {
    const numMatch = e.id.match(/^T(\d+)$/);
    if (!numMatch) {
      fail(`taste_log.yaml: entry id "${e.id}" doesn't match T{XX}`);
    } else {
      seenNums.push(Number(numMatch[1]));
    }

    if (!ATTITUDE_TAGS.has(e.tag)) {
      fail(`taste_log.yaml: ${e.id} has invalid tag "${e.tag}"`);
    }
    if (!OBJECT_TAGS.has(e.object)) {
      fail(`taste_log.yaml: ${e.id} has invalid object "${e.object}"`);
    }
    if (!e.target || !validNodeIds.has(e.target)) {
      fail(`taste_log.yaml: ${e.id} targets "${e.target}", which does not resolve to a real node in after/trace/exploration_tree.yaml`);
    } else {
      pass(`${e.id}: target ${e.target} resolves; tag=${e.tag} object=${e.object}`);
    }
  }

  const uniqueNums = new Set(seenNums);
  if (uniqueNums.size !== seenNums.length) {
    fail('taste_log.yaml: T ids are not unique');
  }
  const sorted = [...uniqueNums].sort((a, b) => a - b);
  const expected = sorted.map((_, i) => i + 1);
  if (JSON.stringify(sorted) !== JSON.stringify(expected)) {
    fail(`taste_log.yaml: T ids are not sequential starting at 1 (got T${sorted.join(', T')})`);
  } else {
    pass('T ids unique and sequential');
  }
}

// --- run ---------------------------------------------------------------------

console.log(`before: ${beforeDir}`);
console.log(`after:  ${afterDir}`);

checkMarkdownFile('logic/claims.md', path.join(beforeDir, 'logic/claims.md'), path.join(afterDir, 'logic/claims.md'));
checkMarkdownFile(
  'logic/solution/heuristics.md',
  path.join(beforeDir, 'logic/solution/heuristics.md'),
  path.join(afterDir, 'logic/solution/heuristics.md')
);
const validNodeIds = checkExplorationTree(
  path.join(beforeDir, 'trace/exploration_tree.yaml'),
  path.join(afterDir, 'trace/exploration_tree.yaml')
);
checkTasteLog(path.join(afterDir, 'trace/taste_log.yaml'), validNodeIds);

console.log('');
if (failures.length > 0) {
  console.error(`FAILED — ${failures.length} invariant violation(s):`);
  for (const f of failures) console.error(`  ✗ ${f}`);
  process.exit(1);
} else {
  console.log('PASSED — all taste-comment invariants hold.');
  process.exit(0);
}
