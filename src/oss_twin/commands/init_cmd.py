"""`oss-twin init`: scaffold the private mirror repo with matching structure."""

import subprocess
from pathlib import Path

from oss_twin.config import Config


CLAUDE_TEMPLATE = """# {name}: private mirror

Private half of the public `{public_name}` repo. Holds operator-internal
content that was stripped from the public repo, plus anything else too
sensitive for public surface.

## Working set

| Concern | Source of truth |
|---------|----------------|
| Product source + public docs | public `{public_name}` repo |
| Operator memory (handoffs, internal notes) | this repo |
| Pre-implementation plans + design specs | this repo |
| 1Password vault item names, deploy IDs, internal-only operational state | this repo |

## Sync triggers

| Event | Update |
|-------|--------|
| Milestone shipped in public repo | New handoff under `docs/handoffs/` |
| Design decision made before implementation | New spec under `docs/superpowers/specs/` |
| Implementation planned before coding | New plan under `docs/superpowers/plans/` |
| Production state changes | Append to or revise latest handoff |

## Cross-repo links

- Public repo: see `.oss-twin.yaml` in that repo for the mirror configuration
- Leak-class catalog: https://github.com/creatornader/leakguard
"""

README_TEMPLATE = """# {name}

Private mirror of public `{public_name}`. See CLAUDE.md for the working set.
"""

GITIGNORE_TEMPLATE = """.DS_Store
.remember/
node_modules/
__pycache__/
*.pyc
.venv/
.env
"""


def run(config: Config, push: bool = False, force: bool = False) -> int:
    target = config.mirror_path
    public_name = config.repo_root.name
    mirror_name = target.name

    if target.exists() and any(target.iterdir()) and not force:
        print(f"oss-twin: {target} already exists and is non-empty. Use --force to overwrite scaffolding.")
        return 1

    target.mkdir(parents=True, exist_ok=True)

    # git init if not already
    if not (target / ".git").exists():
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=target, check=True)
        print(f"  git init -> {target}")

    # Scaffold directories
    for d in config.mirror_scaffold:
        (target / d).mkdir(parents=True, exist_ok=True)
        gitkeep = target / d / ".gitkeep"
        if not any((target / d).iterdir()):
            gitkeep.touch()
        print(f"  scaffold -> {d}")

    # Write CLAUDE.md
    claude = target / "CLAUDE.md"
    if not claude.exists() or force:
        claude.write_text(CLAUDE_TEMPLATE.format(name=mirror_name, public_name=public_name))
        print(f"  write -> CLAUDE.md")

    # Write README.md
    readme = target / "README.md"
    if not readme.exists() or force:
        readme.write_text(README_TEMPLATE.format(name=mirror_name, public_name=public_name))
        print(f"  write -> README.md")

    # Write .gitignore
    gi = target / ".gitignore"
    if not gi.exists() or force:
        gi.write_text(GITIGNORE_TEMPLATE)
        print(f"  write -> .gitignore")

    # Initial commit
    if not _has_commits(target):
        subprocess.run(["git", "add", "-A"], cwd=target, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", f"chore: scaffold {mirror_name} via oss-twin"],
            cwd=target,
            check=True,
        )
        print(f"  initial commit")

    # Optionally push
    if push and config.mirror.remote:
        print(f"  pushing to {config.mirror.remote}...")
        subprocess.run(
            ["git", "remote", "add", "origin", config.mirror.remote],
            cwd=target,
            check=False,  # may already exist
        )
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=target, check=True)

    print(f"\noss-twin: mirror ready at {target}")
    if config.mirror.remote and not push:
        print(f"To push: cd {target} && git remote add origin {config.mirror.remote} && git push -u origin main")
        print(f"Or re-run: oss-twin init --push")
    return 0


def _has_commits(repo: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0
