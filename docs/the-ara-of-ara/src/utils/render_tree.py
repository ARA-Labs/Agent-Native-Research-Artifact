"""Render an ARA exploration_tree.yaml into a self-contained HTML visualization."""

import json
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_tree(yaml_path: Path) -> list[dict]:
    """Parse exploration_tree.yaml and return the tree list."""
    data = yaml.safe_load(yaml_path.read_text())
    if not isinstance(data, dict) or "tree" not in data:
        raise ValueError(f"{yaml_path}: missing top-level 'tree' key")
    return data["tree"]


def load_metadata(ara_dir: Path) -> dict:
    """Extract title and domain from PAPER.md frontmatter, if available."""
    paper_md = ara_dir / "PAPER.md"
    if not paper_md.is_file():
        return {}
    text = paper_md.read_text()
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        meta = yaml.safe_load(parts[1])
        return meta if isinstance(meta, dict) else {}
    except Exception:
        return {}


def _clean_multiline(obj):
    """Recursively collapse YAML multi-line strings into single lines."""
    if isinstance(obj, str):
        return " ".join(obj.split())
    if isinstance(obj, list):
        return [_clean_multiline(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _clean_multiline(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render(tree: list[dict], artifact_id: str, subtitle: str = "") -> str:
    """Inject tree data into the HTML template and return the full HTML string."""
    clean = _clean_multiline(tree)
    tree_json = json.dumps(clean, indent=2, ensure_ascii=False)
    html = _TEMPLATE
    html = html.replace("{{TREE_JSON}}", tree_json)
    html = html.replace("{{ARTIFACT_ID}}", artifact_id)
    html = html.replace("{{SUBTITLE}}", subtitle)
    return html


def render_artifact(ara_dir: Path) -> Path | None:
    """Render the exploration tree for an ARA artifact directory.

    Returns the output path on success, or None if no tree YAML exists.
    """
    yaml_path = ara_dir / "trace" / "exploration_tree.yaml"
    if not yaml_path.is_file():
        return None

    tree = load_tree(yaml_path)
    artifact_id = ara_dir.name
    meta = load_metadata(ara_dir)
    title = meta.get("title", "")
    domain = meta.get("domain", "")
    if title:
        subtitle = f"Research DAG &middot; {title}"
    elif domain:
        subtitle = f"Research DAG &middot; {domain}"
    else:
        subtitle = "Research DAG"

    html = render(tree, artifact_id, subtitle)
    out_path = yaml_path.with_suffix(".html")
    out_path.write_text(html)
    return out_path


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Exploration Tree — {{ARTIFACT_ID}}</title>
<style>
  :root {
    --bg: #fafafa;
    --card-bg: #ffffff;
    --border: #e0e0e0;
    --text: #1a1a1a;
    --text-secondary: #555;
    --question: #1565c0;
    --experiment: #e65100;
    --decision: #2e7d32;
    --dead-end: #c62828;
    --pivot: #6a1b9a;
    --edge: #bdbdbd;
    --dag-edge: #e57373;
    --font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    padding: 40px 24px 80px;
    max-width: 1200px;
    margin: 0 auto;
  }

  header {
    text-align: center;
    margin-bottom: 48px;
  }

  header h1 {
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.3px;
    margin-bottom: 6px;
  }

  header p {
    font-size: 13px;
    color: var(--text-secondary);
  }

  .legend {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 40px;
    flex-wrap: wrap;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .legend-dot.question   { background: var(--question); }
  .legend-dot.experiment { background: var(--experiment); }
  .legend-dot.decision   { background: var(--decision); }
  .legend-dot.dead_end   { background: var(--dead-end); }
  .legend-dot.pivot      { background: var(--pivot); }

  /* ---- Tree layout ---- */

  .tree {
    position: relative;
  }

  .node-group {
    position: relative;
    padding-left: 32px;
  }

  .node-group.has-children > .children::before {
    content: "";
    position: absolute;
    left: 15px;
    top: 0;
    bottom: 24px;
    width: 2px;
    background: var(--edge);
  }

  .children {
    position: relative;
    margin-top: 0;
  }

  .children > .node-group::before {
    content: "";
    position: absolute;
    left: -17px;
    top: 22px;
    width: 17px;
    height: 2px;
    background: var(--edge);
  }

  .tree > .node-group {
    padding-left: 0;
  }

  .tree > .node-group::before { display: none; }

  /* ---- Node card ---- */

  .node {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
    position: relative;
  }

  .node:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }

  .node.expanded {
    border-color: #999;
  }

  .node-header {
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }

  .node-indicator {
    flex-shrink: 0;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-top: 5px;
  }

  .node-indicator.question   { background: var(--question); }
  .node-indicator.experiment { background: var(--experiment); }
  .node-indicator.decision   { background: var(--decision); }
  .node-indicator.dead_end   { background: var(--dead-end); }
  .node-indicator.pivot      { background: var(--pivot); }

  .node-id {
    flex-shrink: 0;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
    background: #f0f0f0;
    color: var(--text-secondary);
    margin-top: 1px;
  }

  .node-title {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.4;
    flex: 1;
  }

  .node-type {
    flex-shrink: 0;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    margin-top: 2px;
  }

  .node-type.question   { background: #e3f2fd; color: var(--question); }
  .node-type.experiment { background: #fff3e0; color: var(--experiment); }
  .node-type.decision   { background: #e8f5e9; color: var(--decision); }
  .node-type.dead_end   { background: #ffebee; color: var(--dead-end); }
  .node-type.pivot      { background: #f3e5f5; color: var(--pivot); }

  .node-body {
    display: none;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
    font-size: 13px;
    line-height: 1.6;
    color: var(--text-secondary);
  }

  .node.expanded .node-body {
    display: block;
  }

  .node-field {
    margin-bottom: 8px;
  }

  .node-field:last-child {
    margin-bottom: 0;
  }

  .field-label {
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--text);
    margin-bottom: 2px;
  }

  .field-value {
    white-space: pre-wrap;
  }

  .evidence-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 3px;
  }

  .evidence-tag {
    font-size: 11px;
    padding: 1px 7px;
    border-radius: 3px;
    background: #f5f5f5;
    border: 1px solid #e0e0e0;
  }

  .alt-list {
    list-style: none;
    padding: 0;
  }

  .alt-list li {
    position: relative;
    padding-left: 14px;
    margin-bottom: 3px;
  }

  .alt-list li::before {
    content: "\00d7";
    position: absolute;
    left: 0;
    color: #ccc;
    font-weight: 700;
  }

  .dag-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    color: var(--dag-edge);
    border: 1px solid var(--dag-edge);
    border-radius: 4px;
    padding: 1px 6px;
    margin-left: 8px;
    font-weight: 600;
    vertical-align: middle;
  }

  .dag-badge svg {
    width: 10px;
    height: 10px;
  }

  .chevron {
    flex-shrink: 0;
    width: 16px;
    height: 16px;
    margin-top: 3px;
    transition: transform 0.15s ease;
    color: #ccc;
  }

  .node.expanded .chevron {
    transform: rotate(90deg);
    color: #999;
  }

  .stats {
    display: flex;
    justify-content: center;
    gap: 32px;
    margin-bottom: 32px;
    padding: 12px 0;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }

  .stat {
    text-align: center;
  }

  .stat-value {
    font-size: 20px;
    font-weight: 600;
  }

  .stat-label {
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>

<header>
  <h1>Exploration Tree — {{ARTIFACT_ID}}</h1>
  <p>{{SUBTITLE}}</p>
</header>

<div class="stats" id="stats"></div>

<div class="legend">
  <div class="legend-item"><div class="legend-dot question"></div>Question</div>
  <div class="legend-item"><div class="legend-dot experiment"></div>Experiment</div>
  <div class="legend-item"><div class="legend-dot decision"></div>Decision</div>
  <div class="legend-item"><div class="legend-dot dead_end"></div>Dead End</div>
  <div class="legend-item"><div class="legend-dot pivot"></div>Pivot</div>
</div>

<div class="tree" id="tree"></div>

<script>
const TREE = {{TREE_JSON}};

function collectAll(nodes) {
  let out = [];
  for (const n of nodes) {
    out.push(n);
    if (n.children) out = out.concat(collectAll(n.children));
  }
  return out;
}

function renderStats(tree) {
  const all = collectAll(tree);
  const types = {};
  all.forEach(n => { types[n.type] = (types[n.type] || 0) + 1; });
  const maxDepth = (function getDepth(nodes, d) {
    let m = d;
    for (const n of nodes) {
      if (n.children) m = Math.max(m, getDepth(n.children, d + 1));
    }
    return m;
  })(tree, 1);

  const el = document.getElementById("stats");
  el.innerHTML = `
    <div class="stat"><div class="stat-value">${all.length}</div><div class="stat-label">Nodes</div></div>
    <div class="stat"><div class="stat-value">${maxDepth}</div><div class="stat-label">Max Depth</div></div>
    <div class="stat"><div class="stat-value">${types.decision || 0}</div><div class="stat-label">Decisions</div></div>
    <div class="stat"><div class="stat-value">${types.experiment || 0}</div><div class="stat-label">Experiments</div></div>
    <div class="stat"><div class="stat-value">${types.dead_end || 0}</div><div class="stat-label">Dead Ends</div></div>
  `;
}

function renderEvidence(ev) {
  if (!ev) return "";
  const items = Array.isArray(ev) ? ev : [ev];
  if (items.length === 1 && typeof items[0] === "string" && items[0].length > 40) {
    return `<div class="node-field"><div class="field-label">Evidence</div><div class="field-value">${esc(items[0])}</div></div>`;
  }
  return `<div class="node-field"><div class="field-label">Evidence</div><div class="evidence-tags">${items.map(i => `<span class="evidence-tag">${esc(String(i))}</span>`).join("")}</div></div>`;
}

function renderAlternatives(alts) {
  if (!alts || alts.length === 0) return "";
  return `<div class="node-field"><div class="field-label">Rejected Alternatives</div><ul class="alt-list">${alts.map(a => `<li>${esc(a)}</li>`).join("")}</ul></div>`;
}

function renderBody(node) {
  let html = "";
  const t = node.type;

  if (t === "question" && node.description)
    html += `<div class="node-field"><div class="field-label">Description</div><div class="field-value">${esc(node.description)}</div></div>`;

  if (t === "experiment") {
    if (node.result) html += `<div class="node-field"><div class="field-label">Result</div><div class="field-value">${esc(node.result)}</div></div>`;
    html += renderEvidence(node.evidence);
  }

  if (t === "decision") {
    if (node.choice) html += `<div class="node-field"><div class="field-label">Choice</div><div class="field-value">${esc(node.choice)}</div></div>`;
    html += renderAlternatives(node.alternatives);
    html += renderEvidence(node.evidence);
  }

  if (t === "dead_end") {
    if (node.hypothesis) html += `<div class="node-field"><div class="field-label">Hypothesis</div><div class="field-value">${esc(node.hypothesis)}</div></div>`;
    if (node.failure_mode) html += `<div class="node-field"><div class="field-label">Failure Mode</div><div class="field-value">${esc(node.failure_mode)}</div></div>`;
    if (node.lesson) html += `<div class="node-field"><div class="field-label">Lesson</div><div class="field-value">${esc(node.lesson)}</div></div>`;
  }

  if (t === "pivot") {
    if (node.from) html += `<div class="node-field"><div class="field-label">From</div><div class="field-value">${esc(node.from)}</div></div>`;
    if (node.to) html += `<div class="node-field"><div class="field-label">To</div><div class="field-value">${esc(node.to)}</div></div>`;
    if (node.trigger) html += `<div class="node-field"><div class="field-label">Trigger</div><div class="field-value">${esc(node.trigger)}</div></div>`;
  }

  return html;
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s.trim();
  return d.innerHTML;
}

const TYPE_LABELS = {
  question: "Question",
  experiment: "Experiment",
  decision: "Decision",
  dead_end: "Dead End",
  pivot: "Pivot"
};

function renderNode(node) {
  const hasChildren = node.children && node.children.length > 0;
  const dagBadge = node.also_depends_on
    ? `<span class="dag-badge"><svg viewBox="0 0 16 16" fill="currentColor"><path d="M5 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm6 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-3 6a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"/></svg>also: ${node.also_depends_on.join(", ")}</span>`
    : "";

  const chevronSvg = `<svg class="chevron" viewBox="0 0 16 16" fill="currentColor"><path d="M6.22 3.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L9.94 8 6.22 4.28a.75.75 0 0 1 0-1.06z"/></svg>`;

  let html = `<div class="node-group ${hasChildren ? "has-children" : ""}">`;
  html += `<div class="node" onclick="this.classList.toggle('expanded')">`;
  html += `<div class="node-header">`;
  html += `<div class="node-indicator ${node.type}"></div>`;
  html += `<span class="node-id">${node.id}</span>`;
  html += `<span class="node-title">${esc(node.title)}${dagBadge}</span>`;
  html += `<span class="node-type ${node.type}">${TYPE_LABELS[node.type]}</span>`;
  html += chevronSvg;
  html += `</div>`;
  html += `<div class="node-body">${renderBody(node)}</div>`;
  html += `</div>`;

  if (hasChildren) {
    html += `<div class="children">`;
    for (const child of node.children) {
      html += renderNode(child);
    }
    html += `</div>`;
  }

  html += `</div>`;
  return html;
}

function render() {
  renderStats(TREE);
  const container = document.getElementById("tree");
  container.innerHTML = TREE.map(renderNode).join("");
}

render();
</script>
</body>
</html>"""
