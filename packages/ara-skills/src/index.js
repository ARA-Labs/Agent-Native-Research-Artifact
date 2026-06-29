import chalk from 'chalk';
import { SUPPORTED_AGENTS, detectAgents, getAgentById } from './agents.js';
import { listSkills } from './skills.js';
import { install, uninstall, update, listInstalled } from './installer.js';

const HELP = `
${chalk.bold.cyan('ara-skills')} — install ARA research skills to your coding agent

${chalk.bold('Usage:')}
  npx @ara-commons/ara-skills                 # interactive
  npx @ara-commons/ara-skills install [opts]
  npx @ara-commons/ara-skills list
  npx @ara-commons/ara-skills update  [opts]
  npx @ara-commons/ara-skills uninstall [opts]
  npx @ara-commons/ara-skills skills          # show available skills
  npx @ara-commons/ara-skills agents          # show supported agents

${chalk.bold('Install options:')}
  --all                         Install every skill (default if no --skill given)
  --skill <id>                  Install one skill (repeatable). Ids: compiler, research-manager, rigor-reviewer, research-visualizer, submit-ara
  --agent <id>                  Target one agent (repeatable). Default: auto-detect, else claude-code
  --local                       Install into ./<agent>/skills instead of $HOME
  --force                       Overwrite existing installations
  --quiet                       Suppress per-skill log output

${chalk.bold('Examples:')}
  npx @ara-commons/ara-skills install --all
  npx @ara-commons/ara-skills install --skill compiler --agent claude-code
  npx @ara-commons/ara-skills install --all --local
  npx @ara-commons/ara-skills uninstall --skill rigor-reviewer --agent cursor
`;

function parseArgs(argv) {
  const out = { _: [], skills: [], agents: [], flags: {} };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--skill' || a === '-s') out.skills.push(argv[++i]);
    else if (a === '--agent' || a === '-a') out.agents.push(argv[++i]);
    else if (a === '--all') out.flags.all = true;
    else if (a === '--local') out.flags.local = true;
    else if (a === '--force') out.flags.force = true;
    else if (a === '--quiet' || a === '-q') out.flags.quiet = true;
    else if (a === '--help' || a === '-h') out.flags.help = true;
    else if (a === '--version' || a === '-v') out.flags.version = true;
    else if (a.startsWith('-')) throw new Error(`Unknown flag: ${a}`);
    else out._.push(a);
  }
  return out;
}

function resolveAgents(requested) {
  if (requested.length > 0) {
    for (const id of requested) {
      if (!getAgentById(id)) {
        throw new Error(
          `Unknown agent "${id}". Supported: ${SUPPORTED_AGENTS.map((a) => a.id).join(', ')}`
        );
      }
    }
    return requested;
  }
  const detected = detectAgents();
  if (detected.length > 0) return detected.map((a) => a.id);
  return ['claude-code'];
}

export async function main(argv) {
  const args = parseArgs(argv);

  if (args.flags.help) {
    console.log(HELP);
    return;
  }
  if (args.flags.version) {
    const { readFileSync } = await import('node:fs');
    const { fileURLToPath } = await import('node:url');
    const { dirname, join } = await import('node:path');
    const here = dirname(fileURLToPath(import.meta.url));
    const pkg = JSON.parse(readFileSync(join(here, '..', 'package.json'), 'utf8'));
    console.log(pkg.version);
    return;
  }

  const cmd = args._[0];

  if (!cmd) {
    const { interactiveFlow } = await import('./prompts.js');
    await interactiveFlow();
    return;
  }

  if (cmd === 'skills') {
    for (const s of listSkills()) {
      console.log(`${chalk.bold(s.id)}`);
      console.log(`  ${chalk.gray(s.description.slice(0, 120))}`);
    }
    return;
  }

  if (cmd === 'agents') {
    const detected = new Set(detectAgents().map((a) => a.id));
    for (const a of SUPPORTED_AGENTS) {
      const tag = detected.has(a.id) ? chalk.green('✓ detected') : chalk.gray('not detected');
      console.log(`${chalk.bold(a.id.padEnd(14))} ${tag}  ${chalk.gray(a.globalSkillsDir)}`);
    }
    return;
  }

  if (cmd === 'list') {
    const rows = listInstalled();
    if (rows.length === 0) {
      console.log('No ARA skills installed.');
      return;
    }
    for (const r of rows) {
      console.log(`${chalk.bold(r.agent)} (${r.scope})  ${chalk.gray(r.dir)}`);
      for (const s of r.skills) console.log(`  • ${s}`);
    }
    return;
  }

  const local = !!args.flags.local;
  const force = !!args.flags.force;
  const quiet = !!args.flags.quiet;

  if (cmd === 'install') {
    const agentIds = resolveAgents(args.agents);
    const skillIds = args.skills;
    if (!quiet) {
      const label = skillIds.length ? skillIds.join(', ') : 'all skills';
      console.log(
        `Installing ${chalk.bold(label)} to ${chalk.bold(agentIds.join(', '))} (${
          local ? 'local' : 'global'
        })`
      );
    }
    for (const agentId of agentIds) {
      if (!quiet) console.log(chalk.bold(`→ ${agentId}`));
      install({ agentId, skillIds, local, force, quiet });
    }
    return;
  }

  if (cmd === 'update') {
    const agentIds = resolveAgents(args.agents);
    for (const agentId of agentIds) {
      if (!quiet) console.log(chalk.bold(`→ ${agentId}`));
      update({ agentId, local, quiet });
    }
    return;
  }

  if (cmd === 'uninstall') {
    const agentIds = resolveAgents(args.agents);
    const skillIds = args.skills;
    for (const agentId of agentIds) {
      if (!quiet) console.log(chalk.bold(`→ ${agentId}`));
      uninstall({ agentId, skillIds, local, quiet });
    }
    return;
  }

  console.log(HELP);
  throw new Error(`Unknown command: ${cmd}`);
}
