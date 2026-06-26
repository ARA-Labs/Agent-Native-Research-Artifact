import fs from 'node:fs';
import path from 'node:path';
import { listSkills, getSkill } from './skills.js';
import { SUPPORTED_AGENTS, getAgentById, targetDirFor } from './agents.js';

const LOCK_FILE = '.ara-skills.json';

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else if (entry.isSymbolicLink()) {
      const link = fs.readlinkSync(s);
      try {
        fs.symlinkSync(link, d);
      } catch {
        fs.copyFileSync(s, d);
      }
    } else fs.copyFileSync(s, d);
  }
}

function rmIfExists(p) {
  if (fs.existsSync(p)) fs.rmSync(p, { recursive: true, force: true });
}

function readLock(dir) {
  const file = path.join(dir, LOCK_FILE);
  if (!fs.existsSync(file)) return { skills: {} };
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return { skills: {} };
  }
}

function writeLock(dir, data) {
  const file = path.join(dir, LOCK_FILE);
  ensureDir(dir);
  fs.writeFileSync(
    file,
    JSON.stringify({ ...data, updatedAt: new Date().toISOString() }, null, 2)
  );
}

/**
 * Install a set of skills to a single agent's skills directory.
 *
 * opts:
 *   agentId:   string, required
 *   skillIds:  string[] — empty array means "all skills"
 *   local:     boolean — install into the current project rather than $HOME
 *   cwd:       string  — overrides process.cwd() for local installs
 *   force:     boolean — overwrite existing installations
 *   quiet:     boolean — suppress log output
 */
export function install(opts) {
  const { agentId, skillIds = [], local = false, cwd, force = false, quiet = false } = opts;
  const agent = getAgentById(agentId);
  if (!agent) throw new Error(`Unknown agent: ${agentId}`);

  const allSkills = listSkills();
  const selected =
    skillIds.length === 0
      ? allSkills
      : skillIds.map((id) => {
          const s = getSkill(id);
          if (!s) throw new Error(`Unknown skill: ${id}`);
          return s;
        });

  const targetDir = targetDirFor(agent, { local, cwd });
  ensureDir(targetDir);

  const results = [];
  const lock = readLock(targetDir);
  lock.skills = lock.skills || {};

  for (const skill of selected) {
    const dest = path.join(targetDir, skill.id);
    const exists = fs.existsSync(dest);
    if (exists && !force) {
      results.push({ skill: skill.id, status: 'skipped', reason: 'already installed' });
      if (!quiet) console.log(`  ~ ${skill.id} already installed (use --force to overwrite)`);
      continue;
    }
    if (exists) rmIfExists(dest);
    copyDir(skill.path, dest);
    lock.skills[skill.id] = {
      installedAt: new Date().toISOString(),
      source: '@ara-commons/ara-skills',
    };
    results.push({ skill: skill.id, status: 'installed', dest });
    if (!quiet) console.log(`  + ${skill.id}  ->  ${dest}`);
  }

  writeLock(targetDir, lock);
  return { agent: agent.id, targetDir, results };
}

/**
 * Install to multiple agents at once.
 */
export function installMany(opts) {
  const { agentIds, ...rest } = opts;
  return agentIds.map((agentId) => install({ ...rest, agentId }));
}

export function uninstall(opts) {
  const { agentId, skillIds = [], local = false, cwd, quiet = false } = opts;
  const agent = getAgentById(agentId);
  if (!agent) throw new Error(`Unknown agent: ${agentId}`);

  const targetDir = targetDirFor(agent, { local, cwd });
  if (!fs.existsSync(targetDir)) {
    return { agent: agent.id, targetDir, results: [] };
  }

  const lock = readLock(targetDir);
  const known = Object.keys(lock.skills || {});
  const targets = skillIds.length === 0 ? known : skillIds;

  const results = [];
  for (const id of targets) {
    const dest = path.join(targetDir, id);
    if (fs.existsSync(dest)) {
      rmIfExists(dest);
      delete lock.skills[id];
      results.push({ skill: id, status: 'removed' });
      if (!quiet) console.log(`  - ${id}`);
    } else {
      results.push({ skill: id, status: 'missing' });
    }
  }
  writeLock(targetDir, lock);
  return { agent: agent.id, targetDir, results };
}

/**
 * "Update" = reconcile this agent against the FULL bundled skill set:
 * re-install (overwrite) every tracked skill AND pull in any skills that
 * were added to the package since the last install. Skips agents that have
 * nothing installed — update should refresh an existing setup, not bootstrap
 * a fresh one (use `install` for that).
 */
export function update(opts) {
  const { agentId, local = false, cwd, quiet = false } = opts;
  const agent = getAgentById(agentId);
  if (!agent) throw new Error(`Unknown agent: ${agentId}`);

  const targetDir = targetDirFor(agent, { local, cwd });
  const lock = readLock(targetDir);
  const ids = Object.keys(lock.skills || {});
  if (ids.length === 0) {
    if (!quiet) console.log(`  (no skills tracked at ${targetDir})`);
    return { agent: agent.id, targetDir, results: [] };
  }
  // skillIds: [] => all bundled skills; force => overwrite the tracked ones.
  return install({ agentId, skillIds: [], local, cwd, force: true, quiet });
}

/**
 * List currently installed skills across all known agents.
 * Checks both global and local (cwd) locations.
 */
export function listInstalled({ cwd = process.cwd() } = {}) {
  const rows = [];
  for (const agent of SUPPORTED_AGENTS) {
    for (const scope of ['global', 'local']) {
      const dir = targetDirFor(agent, { local: scope === 'local', cwd });
      if (!fs.existsSync(dir)) continue;
      const lock = readLock(dir);
      const skills = Object.keys(lock.skills || {});
      if (skills.length === 0) {
        // Also look for skill dirs present without a lock file.
        const bare = fs
          .readdirSync(dir, { withFileTypes: true })
          .filter((e) => e.isDirectory() && fs.existsSync(path.join(dir, e.name, 'SKILL.md')))
          .map((e) => e.name);
        if (bare.length > 0) rows.push({ agent: agent.id, scope, dir, skills: bare, tracked: false });
      } else {
        rows.push({ agent: agent.id, scope, dir, skills, tracked: true });
      }
    }
  }
  return rows;
}
