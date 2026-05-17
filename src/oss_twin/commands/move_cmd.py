"""`oss-twin move`: relocate a file from the public repo to its matching path
in the private mirror."""

import shutil

from oss_twin.config import Config


def run(config: Config, path: str, force: bool = False) -> int:
    source = (config.repo_root / path).resolve()
    if not source.exists():
        print(f"oss-twin: {source} does not exist.")
        return 1

    try:
        rel = source.relative_to(config.repo_root)
    except ValueError:
        print(f"oss-twin: {source} is not under the public repo root ({config.repo_root}).")
        return 1

    target = config.mirror_path / rel
    if target.exists() and not force:
        print(f"oss-twin: target {target} already exists. Use --force to overwrite.")
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        shutil.rmtree(source)
    else:
        shutil.copy2(source, target)
        source.unlink()

    print(f"oss-twin: moved")
    print(f"  from: {source.relative_to(config.repo_root)}  (public)")
    print(f"    to: {rel}  (mirror at {config.mirror_path})")
    print(f"\nReview, then commit on both sides:")
    print(f"  cd {config.repo_root} && git add -A && git commit -m 'chore: move {rel} to mirror via oss-twin'")
    print(f"  cd {config.mirror_path} && git add -A && git commit -m 'chore: receive {rel} from public via oss-twin'")
    return 0
