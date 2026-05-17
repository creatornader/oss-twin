"""`oss-twin status`: show where private paths currently live."""

from pathlib import Path

from oss_twin.config import Config


def run(config: Config) -> int:
    print(f"public repo: {config.repo_root}")
    print(f"mirror:      {config.mirror_path}", end="")
    if not config.mirror_path.exists():
        print("  (missing — run `oss-twin init`)")
    else:
        print()
    if config.mirror.remote:
        print(f"mirror remote: {config.mirror.remote}")
    print()
    print("private paths:")

    if not config.private_paths:
        print("  (none configured)")
        return 0

    bad = 0
    for pattern in config.private_paths:
        in_public = _exists_in(config.repo_root, pattern)
        in_mirror = _exists_in(config.mirror_path, pattern) if config.mirror_path.exists() else False

        if in_public:
            marker = "PUBLIC LEAK"
            bad += 1
        elif in_mirror:
            marker = "in mirror"
        else:
            marker = "missing"
        print(f"  [{marker:>12}]  {pattern}")

    print()
    if bad:
        print(f"oss-twin: {bad} path(s) are present in the public repo and should be moved.")
        return 1
    return 0


def _exists_in(root: Path, pattern: str) -> bool:
    """True if `pattern` (a path or trailing-slash directory) has any file under `root`."""
    p = pattern.rstrip("/")
    full = root / p
    if not full.exists():
        # Try glob expansion
        for _ in root.rglob(p):
            return True
        return False
    if full.is_file():
        return True
    if full.is_dir():
        return any(full.rglob("*"))
    return False
