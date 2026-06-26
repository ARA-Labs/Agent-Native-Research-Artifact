import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { listSkills } from '../src/skills.js';
import { SUPPORTED_AGENTS, getAgentById } from '../src/agents.js';
import { install, uninstall, update, listInstalled } from '../src/installer.js';

test('listSkills discovers the four ARA skills', () => {
  const ids = listSkills().map((s) => s.id).sort();
  assert.deepEqual(ids, ['compiler', 'research-manager', 'research-visualizer', 'rigor-reviewer']);
});

test('agent registry exposes expected ids', () => {
  const ids = SUPPORTED_AGENTS.map((a) => a.id);
  assert.ok(ids.includes('claude-code'));
  assert.ok(ids.includes('cursor'));
  assert.ok(ids.includes('generic'));
  assert.equal(getAgentById('claude-code').id, 'claude-code');
});

test('install + uninstall cycle (local, tmp dir)', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ara-skills-'));
  try {
    const res = install({
      agentId: 'claude-code',
      skillIds: ['compiler'],
      local: true,
      cwd: tmp,
      force: true,
      quiet: true,
    });
    assert.equal(res.results[0].status, 'installed');
    const installed = path.join(tmp, '.claude/skills/compiler/SKILL.md');
    assert.ok(fs.existsSync(installed), 'SKILL.md should be copied');

    const rows = listInstalled({ cwd: tmp });
    const row = rows.find((r) => r.agent === 'claude-code' && r.scope === 'local');
    assert.ok(row && row.skills.includes('compiler'));

    const rm = uninstall({
      agentId: 'claude-code',
      skillIds: ['compiler'],
      local: true,
      cwd: tmp,
      quiet: true,
    });
    assert.equal(rm.results[0].status, 'removed');
    assert.ok(!fs.existsSync(installed));
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test('update reconciles a partial install to the full bundled skill set', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ara-skills-update-'));
  try {
    // Start with only one skill installed.
    install({ agentId: 'claude-code', skillIds: ['compiler'], local: true, cwd: tmp, force: true, quiet: true });

    // update() must pull in skills added to the package since that install.
    update({ agentId: 'claude-code', local: true, cwd: tmp, quiet: true });

    const skillsDir = path.join(tmp, '.claude/skills');
    for (const id of listSkills().map((s) => s.id)) {
      assert.ok(
        fs.existsSync(path.join(skillsDir, id, 'SKILL.md')),
        `update should have installed "${id}"`
      );
    }
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test('lock file updatedAt advances on reinstall', async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ara-skills-lock-'));
  try {
    const opts = {
      agentId: 'claude-code',
      skillIds: ['compiler'],
      local: true,
      cwd: tmp,
      force: true,
      quiet: true,
    };
    const lockPath = path.join(tmp, '.claude/skills/.ara-skills.json');

    install(opts);
    const first = JSON.parse(fs.readFileSync(lockPath, 'utf8')).updatedAt;

    await new Promise((r) => setTimeout(r, 10));
    install(opts);
    const second = JSON.parse(fs.readFileSync(lockPath, 'utf8')).updatedAt;

    assert.ok(
      new Date(second) > new Date(first),
      `updatedAt should advance on reinstall (was ${first}, still ${second})`
    );
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
