"""oss-twin CLI."""

import argparse
import sys
from pathlib import Path

from oss_twin import __version__
from oss_twin.config import CONFIG_FILENAME, load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="oss-twin",
        description="Keep a public OSS repo and its private mirror structurally aligned.",
    )
    parser.add_argument("--version", action="version", version=f"oss-twin {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    init_p = sub.add_parser("init", help="Scaffold the mirror repo with matching structure")
    init_p.add_argument("--config", type=Path, default=None, help=f"Path to {CONFIG_FILENAME}")
    init_p.add_argument("--push", action="store_true", help="Push to mirror remote after init")
    init_p.add_argument("--force", action="store_true", help="Overwrite existing scaffolding files")

    check_p = sub.add_parser("check", help="Fail if any private_paths exist in the public tree")
    check_p.add_argument("--config", type=Path, default=None)
    check_p.add_argument("--verbose", "-v", action="store_true")

    move_p = sub.add_parser("move", help="Move a file from public to private mirror")
    move_p.add_argument("path", help="Path (under public repo root) to move")
    move_p.add_argument("--config", type=Path, default=None)
    move_p.add_argument("--force", action="store_true", help="Overwrite if target exists in mirror")

    status_p = sub.add_parser("status", help="Show where each private path currently lives")
    status_p.add_argument("--config", type=Path, default=None)

    scaffold_p = sub.add_parser("scaffold-config", help=f"Write a starter {CONFIG_FILENAME} in cwd")
    scaffold_p.add_argument("--force", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "scaffold-config":
        return _cmd_scaffold_config(args)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"oss-twin: {e}", file=sys.stderr)
        return 2

    if args.cmd == "init":
        from oss_twin.commands.init_cmd import run as init_run
        return init_run(config, push=args.push, force=args.force)
    if args.cmd == "check":
        from oss_twin.commands.check_cmd import run as check_run
        return check_run(config, verbose=args.verbose)
    if args.cmd == "move":
        from oss_twin.commands.move_cmd import run as move_run
        return move_run(config, args.path, force=args.force)
    if args.cmd == "status":
        from oss_twin.commands.status_cmd import run as status_run
        return status_run(config)
    return 1


STARTER_CONFIG = """# oss-twin config
# This file declares the relationship between THIS public repo and its
# private mirror. Commit it. Run `oss-twin check` in CI to fail PRs that
# introduce private content into the public tree.

version: 1

mirror:
  # Path to the private mirror, relative to this repo's root (or absolute).
  path: ../{repo_name}-internal
  # Optional remote (oss-twin can push the mirror's initial commit here).
  # remote: git@github.com:user/{repo_name}-internal.git
  visibility: private

# Paths that should NEVER exist in this public repo. `oss-twin check` walks
# these and exits 1 if any match. Trailing `/` means "directory and contents."
# Globs are supported via fnmatch.
private_paths:
  - docs/handoffs/
  - docs/internal/
  - .remember/
  - thoughts/

# Directory structure to scaffold in the mirror on `oss-twin init`.
# Used to seed an empty mirror with the right shape.
mirror_scaffold:
  - docs/
  - docs/handoffs/
"""


def _cmd_scaffold_config(args) -> int:
    target = Path(CONFIG_FILENAME)
    if target.exists() and not args.force:
        print(f"{target} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1
    repo_name = Path.cwd().name
    target.write_text(STARTER_CONFIG.format(repo_name=repo_name))
    print(f"Wrote {target}.")
    print(f"Edit it to confirm the mirror path, then run:")
    print(f"  oss-twin init           # scaffold the mirror repo")
    print(f"  oss-twin check          # verify no private paths in the public tree")
    return 0
