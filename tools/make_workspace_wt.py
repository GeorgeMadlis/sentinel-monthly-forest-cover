#!/usr/bin/env python3
"""Build a single-file working-tree (WT) context document for a VS Code workspace.

The WT is a Markdown file meant to be pasted/uploaded into a ChatGPT or Claude chat window
that cannot see the local repos. For every folder in the workspace it emits:

  * a file tree (git-tracked + untracked-not-ignored files, gitingest style; generated
    `runs/` collapsed to per-run file counts), and
  * the full text of the Markdown files that explain how that repo works.

Default workspace is `sentinel-monthly-forest-cover.code-workspace`, which lives in the
sibling `forest-cover-lab` checkout and spans this repo plus `forest-cover-lab`. Live
satellite runs kept local via `.git/info/exclude` are not listed.

The output is a local context artifact, not a source file: keep it out of git
(`wt-*.md` is listed in `.git/info/exclude`). Stdlib only, no gitingest dependency.

Usage:
  python tools/make_workspace_wt.py
  python tools/make_workspace_wt.py --workspace path/to/x.code-workspace --out wt-x.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = REPO_ROOT.parent / "forest-cover-lab/sentinel-monthly-forest-cover.code-workspace"
MAX_MD_BYTES = 200_000

# Files never listed or included anywhere (generated context dumps, caches, envs).
GLOBAL_EXCLUDES = [
    "digest-*.txt", "wt-*.md", "*.code-workspace",
    ".venv/*", "*/.venv/*", "node_modules/*", "*/node_modules/*",
    "__pycache__/*", "*/__pycache__/*", ".pytest_cache/*", "*.pyc", ".DS_Store", "*/.DS_Store",
    ".ipynb_checkpoints/*", "*/.ipynb_checkpoints/*",
]

# Generated output directories whose trees are collapsed to one "(N files)" line per child.
TREE_COLLAPSE = ["runs", "out", "tmp"]

# Per-repo Markdown selection: include globs match per path segment (`*` never crosses `/`);
# exclude globs are plain fnmatch (`tests/*` excludes everything under tests/).
# Repos not listed fall back to DEFAULT_RULES.
DEFAULT_RULES = {
    "include": ["*.md", "docs/*.md", "docs/*/*.md", "*/README.md"],
    "exclude": ["out/*", "tests/*", "CHANGELOG.md"],
}
REPO_RULES = {
    "sentinel-monthly-forest-cover": {
        # README, docs, spec, script/example notes, and the committed example run report.
        "include": ["*.md", "docs/*.md", "specs/*.md", "*/README.md", "*/*/README.md",
                    "runs/*/report.md"],
        "exclude": ["tests/*"],
    },
    "forest-cover-lab": {
        # Governance, ADRs, specs, the knowledge graph cards and research notes all carry
        # meaning; only GitHub issue templates and test notes are left out.
        "include": ["*.md", "*/*.md", "*/*/*.md", "*/*/*/*.md"],
        "exclude": [".github/*", "tests/*"],
    },
}


def match_any(path: str, patterns: list[str]) -> bool:
    """fnmatch semantics: `*` also crosses `/` (used for excludes)."""
    return any(fnmatch.fnmatchcase(path, p) for p in patterns)


def match_segments(path: str, patterns: list[str]) -> bool:
    """Glob semantics per path segment: `*.md` matches only top-level files (used for includes)."""
    parts = path.split("/")
    for p in patterns:
        pp = p.split("/")
        if len(pp) == len(parts) and all(fnmatch.fnmatchcase(a, b) for a, b in zip(parts, pp)):
            return True
    return False


def repo_files(repo: Path) -> list[str]:
    """Tracked + untracked-not-ignored files; plain walk if the folder is not a git repo."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--cached", "--others", "--exclude-standard"],
            check=True, capture_output=True, text=True,
        ).stdout.splitlines()
    except subprocess.CalledProcessError:
        out = [str(p.relative_to(repo)) for p in repo.rglob("*") if p.is_file()]
    return sorted({f for f in out if (repo / f).is_file() and not match_any(f, GLOBAL_EXCLUDES)})


def git_head(repo: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%h %cs %s"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return "(not a git repo)"


def git_dirty(repo: Path) -> int:
    """Number of modified/untracked entries in `git status --porcelain` (0 if not a repo)."""
    try:
        return len(subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            check=True, capture_output=True, text=True,
        ).stdout.splitlines())
    except subprocess.CalledProcessError:
        return 0


def collapse(paths: list[str], dirs: list[str]) -> list[str]:
    """Replace files under each `dirs` entry with one `<dir>/<child>/… (N files)` line per child."""
    counts: dict[str, int] = {}
    kept = []
    for p in paths:
        parts = p.split("/")
        if len(parts) > 1 and parts[0] in dirs:
            key = "/".join(parts[:2]) + ("/" if len(parts) > 2 else "")
            counts[key] = counts.get(key, 0) + 1
        else:
            kept.append(p)
    for key, n in counts.items():
        kept.append(f"{key}… ({n} files)" if key.endswith("/") else key)
    return sorted(kept)


def render_tree(root_name: str, paths: list[str]) -> str:
    """gitingest-style tree: files before directories at each level."""
    tree: dict = {}
    for p in paths:
        node = tree
        parts = p.split("/")
        for d in parts[:-1]:
            node = node.setdefault(d + "/", {})
        node[parts[-1]] = None

    lines = [f"└── {root_name}/"]

    def walk(node: dict, prefix: str) -> None:
        keys = sorted(node, key=lambda k: (node[k] is not None, k.lower()))
        for i, k in enumerate(keys):
            last = i == len(keys) - 1
            lines.append(f"{prefix}{'└── ' if last else '├── '}{k}")
            if node[k] is not None:
                walk(node[k], prefix + ("    " if last else "│   "))

    walk(tree, "    ")
    return "\n".join(lines)


def file_block(label: str, path: Path) -> str:
    size = path.stat().st_size
    if size > MAX_MD_BYTES:
        body = f"[omitted: {size} bytes > {MAX_MD_BYTES} byte limit]"
    else:
        body = path.read_text(encoding="utf-8", errors="replace").rstrip()
    fence = "`" * max(4, 1 + max((len(m) for m in re.findall(r"`+", body)), default=0))
    return f"#### `{label}`\n\n{fence}markdown\n{body}\n{fence}\n"


def repo_section(repo: Path) -> tuple[str, list[str]]:
    rules = REPO_RULES.get(repo.name, DEFAULT_RULES)
    files = repo_files(repo)
    mds = [f for f in files if f.endswith(".md")
           and match_segments(f, rules["include"]) and not match_any(f, rules["exclude"])]
    dirty = git_dirty(repo)
    parts = [
        f"## Repo: `{repo.name}`\n",
        f"- Local path: `{repo}`\n- HEAD: `{git_head(repo)}`"
        + (f" (+{dirty} uncommitted/untracked entries)" if dirty else "")
        + f"\n- Files listed: {len(files)}; Markdown files included below: {len(mds)}\n",
        f"### File tree — `{repo.name}`\n\n```text\n{render_tree(repo.name, collapse(files, TREE_COLLAPSE))}\n```\n",
        f"### Key Markdown — `{repo.name}`\n",
    ]
    parts += [file_block(f"{repo.name}/{m}", repo / m) for m in mds]
    return "\n".join(parts), mds


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    ap.add_argument("--out", type=Path, default=None,
                    help="default: <this repo>/wt-<workspace name>.md")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    folders = [(ws.parent / f["path"]).resolve() for f in json.loads(ws.read_text())["folders"]]
    out = args.out or REPO_ROOT / f"wt-{ws.stem}.md"

    sections, toc = [], []
    for repo in folders:
        if not repo.is_dir():
            toc.append(f"- `{repo.name}` — **missing locally, skipped**")
            continue
        text, mds = repo_section(repo)
        toc.append(f"- `{repo.name}` — {len(mds)} Markdown files")
        sections.append(text)

    header = (
        f"# Working tree (WT): `{ws.stem}` workspace\n\n"
        f"Generated {dt.datetime.now().astimezone().isoformat(timespec='seconds')} by "
        f"`tools/make_workspace_wt.py` from `{ws}`.\n\n"
        "Context pack for a chat assistant without access to the local repos: per repo, a file "
        "tree and the Markdown files that explain how the repo works. Source code, data, "
        "rendered HTML and run outputs are listed in the trees but not included. "
        "Canonical state is each repo's git HEAD, not this file.\n\n"
        "## Contents\n\n" + "\n".join(toc) + "\n"
    )
    out.write_text(header + "\n\n---\n\n".join([""] + sections), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
